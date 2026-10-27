# Security

The full design lives in `~/workspace/device-harness/security-design.md`. This document is the version implemented in Clavis v0.1.0, with what is still planned marked as such.

## Threat model

| Threat | Mitigation |
| --- | --- |
| Attacker on LAN or internet | Private mesh only, default-deny firewall, agents listen only on the mesh IP |
| Man in the middle | Pairing keys plus mTLS with short-lived certificates |
| Replay | Timestamp, nonce, and monotonic counter; reject anything older than 60 seconds, with a reused nonce, or a regressed counter |
| One device compromised | Per-device scopes; a token cannot be upgraded to a wider scope |
| Private key stolen | Keys stored at mode `0600` on the device; hardware keystore integration is planned (see below) |
| Audit log tampered with | SHA-256 hash-chain, verifiable with `audit` |
| Controller lost | Revocation list over the mesh, kill switch that ends all sessions |

## Transport

A private mesh: WireGuard, Tailscale, or Headscale. The design specifies X25519, ChaCha20-Poly1305, BLAKE2s, Noise IKpsk2, and rekeying roughly every 2 minutes, with forward secrecy. The mesh itself is a prerequisite, not something Clavis provisions: set it up before pairing any device.

## Identity

Each device holds its own Ed25519 keypair. Its identity is the SHA-256 fingerprint of its public key. Private keys are stored at mode `0600` under `~/.device-control/keys/` in v0.1.0.

Implemented signing backends, in priority order:

1. The `cryptography` library, when installed (`pip install -e ".[crypto]"`).
2. The `openssl` CLI, present on most Linux, macOS, and Windows-OpenSSH hosts.
3. A clearly labelled HMAC-SHA256 DEMO fallback, which refuses destructive actions unless `--allow-demo` is passed explicitly. HMAC is never silently presented as Ed25519.

Hardware keystore storage (Android Keystore, Windows DPAPI/TPM, macOS Secure Enclave/Keychain, Linux TPM2) with PIN or biometric unlock is **planned, not yet implemented**. Until then, file permissions are the protection, and keys must never leave the device, enter the registry, or be included in a cloud backup.

## Pairing

Pairing establishes a permanent Ed25519 identity plus a one-time ephemeral key:

- Devices with a screen: the user compares a 6-digit SAS code on the device and on the controller, and approves on both sides. The handshake is Noise XX (X25519, ChaCha20-Poly1305, BLAKE2s); the ephemeral key is deleted after pairing.
- Headless servers: a 5-minute one-time token bound to the device fingerprint.
- Screenless fallback (planned): SPAKE2 with a 6-digit code.

A device is not shown as controllable until pairing succeeds.

## Authority

The controller acts as a local certificate authority (Ed25519 root key, ideally held in a Secure Enclave or YubiKey). Device certificates are short-lived: 24 hours normally, 1 hour for sensitive operations, with scope in an extension (`spiffe://home/device/<name>`).

Every command carries a token containing device ID, scope, a 60-second expiry, a nonce, and a hash of the command, signed by the controller. A token issued for one action cannot be reused for another: a screenshot token cannot debloat a device.

## Audit and rate limiting

Every executed change is appended to a hash-chain:

```
H_n = SHA-256(H_{n-1} || command || result || timestamp)
```

Verify it with `device_control.cli audit`. The chain is signed periodically in the design; in v0.1.0, verification checks the chain itself.

Five consecutive verification failures lock the device for 15 minutes. Identity rotation every 30 days and automatic certificate renewal are planned.

## NEVER lists and dry-run by default

The following are always blocked, even with `--confirm`:

- Windows: Microsoft Store and .NET runtimes.
- Linux: systemd, D-Bus, and display managers.
- Android: Settings, SystemUI, the current launcher, and the current input method.

All destructive CLI actions default to dry-run. In MCP, destructive tools are dry-run only by design (see README): a prompt-injected host must not be able to debloat a device through MCP alone.

## Revocation and kill switch

`device_control.cli revoke --fingerprint <sha256>` removes a device key. A revoked device must pair again from zero. The kill switch ends all sessions and forces re-pairing of every device.

## What the security key is not

The key is authentication and authorisation: proof that a command comes from the controller owner. It is not an OS bypass. It cannot unlock disk encryption, enrol a new biometric, pass a CAPTCHA, break a vendor lock, or control a device you do not own.
