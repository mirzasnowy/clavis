# Skill: device-control v0.1.0

Control PC Windows, laptop, HP Android, TV Android — existing OS,
no OS replacement, no root.

## Rules (non-negotiable)
1. Probe/apps/services first (read-only). Never debloat from a generic list.
2. Dry-run first, backup second, confirm third. MCP is dry-run ONLY.
3. NEVER lists always apply, even with --confirm.
4. Android: disable-user only, never uninstall system packages.
5. Windows/Linux: run the exact script shown in dry-run on the real
   device via its admin agent; this host is not that device unless
   the device IS this host.
6. If a device is not in `devices list`, stop and ask.
7. Open an app or a site ONLY via the dedicated tool, never via
   click/tap: `device_launch` for apps, `device_open_website`
   (CLI: `open-website --device <name> --url <https://...>`) for
   sites. `ui tap` is only for elements INSIDE an already-open app.
   Reason: a click is screen-dependent and multi-step (find icon,
   wait, find address bar, type, Enter, survive focus/autocomplete
   loss); a dedicated open is one deterministic OS intent
   (Windows Start-Process, Linux xdg-open, Android VIEW intent),
   with a clear audit entry and URL validation (http/https only).

## Commands (run from device-control/, PYTHONPATH=src)
- `device-control devices list`
- `device-control probe --device <name>`
- `device-control apps --device <name> --dry-run`
- `device-control services --device <name> --dry-run`
- `device-control debloat --device <name> --list <file> --dry-run`
- `device-control debloat --device <name> --list <file> --confirm`
- `device-control appearance --device <name> --profile dark|light|minimal --dry-run`
- `device-control backup --device <name>`
- `device-control restore --device <name> --dry-run`
- `device-control pair --device <name>` (compare SAS on both screens)
- `device-control audit` (verify hash-chain)
- `device-control open-website --device <name> --url <https://...> --dry-run`
- `device-control mcp` (stdio MCP server, 14 tools)

## MCP tools
device_list, device_probe, device_apps, device_services,
device_debloat (dry-run), device_restore (plan), device_appearance
(dry-run), device_backup, device_launch (dry-run),
device_open_website (dry-run), device_ui, device_search_app,
device_screenshot, audit_verify.

## Appearance profiles
dark, light, minimal, tv-minimal — see examples/appearance/profiles.json.
Android launcher: install FLauncher/Projectivy first, set default,
screenshot check, only then disable old launcher.
