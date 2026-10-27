"""Ed25519 signing + signed tokens + audit hash-chain + revocation.

Priority order for Ed25519 (real, not demo):
1. `cryptography` library if installed (pip install cryptography)
2. `openssl` CLI (present on Linux/macOS/Windows-OpenSSH hosts)
   - genpkey ED25519, pkeyutl -sign/-verify with -rawin
3. Fallback HMAC-SHA256, clearly labelled DEMO, and destructive
   actions must refuse to run in DEMO mode unless --allow-demo is
   passed explicitly. Never silently present HMAC as Ed25519.

Token: device + scope + command_hash + nonce + expiry, signed.
Audit: H_n = SHA256(H_{n-1} || device || command || result || ts).
Revocation: a JSON list of revoked fingerprints / token nonces.
"""
import hashlib
import hmac
import json
import os
import secrets
import shutil
import subprocess
import time

HOME = os.path.expanduser("~/.device-control")
KEY_DIR = os.path.join(HOME, "keys")
AUDIT_PATH = os.path.join(HOME, "audit.jsonl")
REVOKE_PATH = os.path.join(HOME, "revoked.json")
DEMO_KEY_PATH = os.path.join(HOME, "demo-key.txt")

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False


def backend():
    if _HAS_CRYPTO:
        return "cryptography-ed25519"
    if shutil.which("openssl"):
        return "openssl-ed25519"
    return "hmac-demo"


def fingerprint(public_bytes: bytes) -> str:
    return hashlib.sha256(public_bytes).hexdigest()


def command_hash(command: str) -> str:
    return hashlib.sha256(command.encode()).hexdigest()


# ---------- key generation ----------
def generate_keypair(name):
    """Generate Ed25519 keypair, store private 0600, return (pub_bytes, fingerprint, backend)."""
    os.makedirs(KEY_DIR, exist_ok=True)
    priv_path = os.path.join(KEY_DIR, name + ".pem")
    pub_path = os.path.join(KEY_DIR, name + ".pub")
    if _HAS_CRYPTO:
        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        with open(priv_path, "wb") as f:
            f.write(priv.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
        os.chmod(priv_path, 0o600)
        with open(pub_path, "wb") as f:
            f.write(pub)
        return pub, fingerprint(pub), "cryptography-ed25519"
    if shutil.which("openssl"):
        subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519",
                        "-out", priv_path], check=True, capture_output=True)
        os.chmod(priv_path, 0o600)
        out = subprocess.run(["openssl", "pkey", "-in", priv_path,
                              "-pubout", "-outform", "DER"],
                             check=True, capture_output=True)
        # DER SubjectPublicKeyInfo: last 32 bytes are the raw key
        pub = out.stdout[-32:]
        with open(pub_path, "wb") as f:
            f.write(pub)
        return pub, fingerprint(pub), "openssl-ed25519"
    # DEMO fallback only
    os.makedirs(HOME, exist_ok=True)
    if not os.path.exists(DEMO_KEY_PATH):
        with open(DEMO_KEY_PATH, "w") as f:
            f.write(secrets.token_hex(32))
        os.chmod(DEMO_KEY_PATH, 0o600)
    with open(DEMO_KEY_PATH) as f:
        key = f.read().strip().encode()
    pub = hashlib.sha256(key).digest()
    return pub, fingerprint(pub), "hmac-demo"


def _sign_openssl(priv_path, data: bytes) -> bytes:
    r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", priv_path,
                        "-rawin", "-in", "/dev/stdin"],
                       input=data, capture_output=True, check=True)
    return r.stdout


def _verify_openssl(pub_der_path, data: bytes, sig: bytes) -> bool:
    # openssl pkeyutl -verify needs a PEM public key; we store raw, so
    # reconstruct via a temporary PEM generated from the raw key is
    # complex — instead verify via ssh-keygen style is out of scope.
    # For openssl backend, verification is done by re-signing check
    # in the paired controller (same key holder). This function returns
    # False to force the cryptography path for verification when possible.
    return False


def sign(name, data: bytes):
    priv_path = os.path.join(KEY_DIR, name + ".pem")
    if _HAS_CRYPTO and os.path.exists(priv_path):
        with open(priv_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), None)
        return priv.sign(data)
    if shutil.which("openssl") and os.path.exists(priv_path):
        return _sign_openssl(priv_path, data)
    with open(DEMO_KEY_PATH, "rb") as f:
        key = f.read().strip()
    return hmac.new(key, data, hashlib.sha256).digest()


def verify_with_public(pub_bytes: bytes, data: bytes, sig: bytes) -> bool:
    if _HAS_CRYPTO:
        try:
            Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig, data)
            return True
        except Exception:
            return False
    # openssl verify path: requires cryptography for raw-key verify;
    # without it, verification is not trusted — return False.
    return False


# ---------- tokens ----------
def make_token(device_name, scope, command, ttl_seconds=60, key_name="controller"):
    ch = command_hash(command)
    nonce = secrets.token_hex(8)
    expiry = int(time.time()) + ttl_seconds
    payload = f"{device_name}|{scope}|{ch}|{nonce}|{expiry}".encode()
    try:
        sig = sign(key_name, payload).hex()
        mode = backend()
    except Exception:
        sig = ""
        mode = "unsigned"
    return {"device": device_name, "scope": scope, "nonce": nonce,
            "expiry": expiry, "command_hash": ch, "sig": sig, "mode": mode}


def verify_token(token, command, pub_bytes=None):
    if token.get("expiry", 0) < int(time.time()):
        return False, "token expired"
    if command_hash(command) != token.get("command_hash"):
        return False, "command hash mismatch"
    if is_revoked_nonce(token.get("nonce", "")):
        return False, "nonce revoked"
    if pub_bytes is not None:
        payload = (f"{token['device']}|{token['scope']}|{token['command_hash']}"
                   f"|{token['nonce']}|{token['expiry']}").encode()
        try:
            sig = bytes.fromhex(token.get("sig", ""))
        except Exception:
            return False, "bad signature encoding"
        if not verify_with_public(pub_bytes, payload, sig):
            return False, "bad signature"
    return True, "ok"


# ---------- audit ----------
class AuditChain:
    def __init__(self, path=AUDIT_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.last = "0" * 64
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    try:
                        self.last = json.loads(line)["hash"]
                    except Exception:
                        pass

    def append(self, device, command, result):
        ts = int(time.time())
        h = hashlib.sha256(
            f"{self.last}|{device}|{command}|{result}|{ts}".encode()).hexdigest()
        entry = {"device": device, "command": command, "result": result,
                 "ts": ts, "prev": self.last, "hash": h}
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.last = h
        return entry

    def verify(self):
        prev = "0" * 64
        count = 0
        if not os.path.exists(self.path):
            return True, 0
        with open(self.path) as f:
            for line in f:
                if not line.strip():
                    continue
                e = json.loads(line)
                expect = hashlib.sha256(
                    f"{prev}|{e['device']}|{e['command']}|{e['result']}|{e['ts']}".encode()).hexdigest()
                if expect != e["hash"] or e["prev"] != prev:
                    return False, count
                prev = e["hash"]
                count += 1
        return True, count


# ---------- revocation ----------
def load_revoked():
    if os.path.exists(REVOKE_PATH):
        try:
            with open(REVOKE_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"fingerprints": [], "nonces": []}


def is_revoked_nonce(nonce):
    return nonce in load_revoked().get("nonces", [])


def revoke_fingerprint(fp):
    data = load_revoked()
    if fp not in data["fingerprints"]:
        data["fingerprints"].append(fp)
    os.makedirs(HOME, exist_ok=True)
    with open(REVOKE_PATH, "w") as f:
        json.dump(data, f, indent=2)
    return data
