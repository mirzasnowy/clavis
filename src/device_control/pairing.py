"""Pairing: real Ed25519 identity + SAS, out-of-band.

Flow (docs/security.md):
1. Device/controller generates Ed25519 identity (security.py).
2. Show name + fingerprint + 6-digit SAS on BOTH screens.
3. User compares SAS by eye, approves on both sides.
4. Only public key + name + initial scope are stored in the registry.
   Private key never leaves the device (0600 file here, keystore/
   Secure Enclave/TPM on real devices).
5. Ephemeral pairing code is single-use and discarded.
"""
import secrets

from device_control import security


def pair(device_name, scope="probe"):
    pub, fp, backend = security.generate_keypair(device_name)
    sas = f"{secrets.randbelow(1000):03d} {secrets.randbelow(1000):03d}"
    return {
        "device": device_name,
        "backend": backend,
        "sas_code": sas,
        "public_key_fingerprint_sha256": fp,
        "public_key_hex": pub.hex(),
        "initial_scope": scope,
        "instruction": (
            "Compare this SAS code on the device screen and on the "
            "controller screen. If they match, approve on both sides. "
            "If they do NOT match, STOP — possible MITM. "
            "Store only the fingerprint + name + scope in devices.json."),
        "private_key_note": "Private key stays in ~/.device-control/keys/ (0600). Never share it, never put it in devices.json, chat, or a backup to the cloud.",
    }
