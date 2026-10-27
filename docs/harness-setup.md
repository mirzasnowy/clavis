# Harness setup — copy, paste, run

Clavis exposes one MCP server, 14 tools, over stdio. Destructive tools are **dry-run only in MCP** — real execution happens in the CLI with `--confirm`, on a paired device.

## 1. Install (once)

```bash
git clone https://github.com/mirzasnowy/clavis.git
cd clavis
python3 --version   # needs 3.10+
pip install -e .    # optional: then `device-control` works without PYTHONPATH
```

If you skip `pip install -e .`, every command below needs `PYTHONPATH=src` and must run from the `device-control/` folder.

Test the server before connecting any harness:

```bash
cd device-control
PYTHONPATH=src python3 -m device_control.mcp_server <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
EOF
```

You should see 14 tools, starting with `device_list`. If you see `ModuleNotFoundError: device_control`, your `PYTHONPATH` or working directory is wrong — fix that first, not the harness config.

## 2. Connect a harness (pick one)

The server is always the same. Only the config file changes. Replace `/path/to/clavis` with your real path. If you installed with `pip install -e .`, drop the `PYTHONPATH` line.

### Claude Code

Config: `.mcp.json` in your project, or `~/.claude.json`.

```json
{"mcpServers": {"device-control": {
  "command": "python3",
  "args": ["-m", "device_control.mcp_server"],
  "cwd": "/path/to/clavis",
  "env": {"PYTHONPATH": "src"}
}}}
```

Or from a terminal:

```bash
claude mcp add device-control -- python3 -m device_control.mcp_server
```

Then restart Claude Code and copy `skills/device-control/SKILL.md` to `.claude/skills/device-control/` so the rules (dry-run first, open-don't-click) travel with it.

### Codex

Config: `~/.codex/config.toml` (ready-made copy: `configs/harness/codex.toml`).

```toml
[mcp_servers.device-control]
command = "python3"
args = ["-m", "device_control.mcp_server"]
cwd = "/path/to/clavis"
env = { PYTHONPATH = "src" }
```

Or:

```bash
codex mcp add device-control -- python3 -m device_control.mcp_server
```

### OpenCode

Config: `opencode.json` in your project, or `~/.config/opencode/opencode.json` (ready-made copy: `configs/harness/opencode.json`).

```json
{"$schema": "https://opencode.ai/config.json",
 "mcp": {"device-control": {"type": "local",
   "command": ["python3", "-m", "device_control.mcp_server"],
   "directory": "/path/to/clavis",
   "environment": {"PYTHONPATH": "src"},
   "enabled": true}}}
```

### Cursor / VS Code

Settings → MCP → Add new MCP server, type `command`, then paste:

```json
{"mcpServers": {"device-control": {
  "command": "python3",
  "args": ["-m", "device_control.mcp_server"],
  "cwd": "/path/to/clavis",
  "env": {"PYTHONPATH": "src"}
}}}
```

VS Code also accepts the same block in `.vscode/mcp.json`.

### Gemini CLI

Config: `.gemini/settings.json` (ready-made copy: `configs/harness/gemini-settings.json`). Same `mcpServers` block as Cursor above.

### Any other MCP harness

If it supports MCP stdio, use the same command, args, working directory, and `PYTHONPATH`. If it only supports HTTP, Clavis does not have an HTTP mode yet — use the CLI fallback below instead.

## 3. Prompts to paste into the harness

Copy these verbatim. Each one is safe: read-only or dry-run.

**See your devices (first prompt, always):**

```
List my Clavis devices with device_list, then probe tv-android
read-only with device_probe. Do not debloat anything yet.
```

**Dry-run a debloat plan:**

```
Show me the dry-run debloat plan for tv-android from
examples/debloat/generic-safe.txt, and list what the NEVER
list blocks. Do not confirm anything.
```

**Open a site (dry-run in MCP, confirm in CLI):**

```
Open https://example.com on pc-windows with
device_open_website (dry-run only), then show me the exact
CLI command to confirm it on the device.
```

**Back up before any change:**

```
Back up tv-android with device_backup, then show the restore
plan with device_restore. Stop and wait for my approval.
```

## 4. Real execution (CLI, not MCP)

MCP will never execute a destructive action. When a dry-run plan looks right, run it yourself on the device:

```bash
cd device-control
export PYTHONPATH=src   # skip if you did pip install -e .
python3 -m device_control.cli backup --device tv-android
python3 -m device_control.cli debloat --device tv-android \
  --list examples/debloat/generic-safe.txt --dry-run
python3 -m device_control.cli debloat --device tv-android \
  --list examples/debloat/generic-safe.txt --confirm
python3 -m device_control.cli audit
```

Safe order, every time: mesh → pair (compare the 6-digit SAS on both screens) → probe → backup → dry-run → confirm → audit.

## 5. No MCP at all

Any harness that can run a shell can use Clavis without MCP:

```bash
device-control devices list
device-control probe --device tv-android
device-control apps --device tv-android --dry-run
```

Add `skills/device-control/SKILL.md` to the harness's skill folder so it follows the same rules.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ModuleNotFoundError: device_control` | Set `cwd` to the repo and `PYTHONPATH` to `src`, or run `pip install -e .` |
| Tools do not appear in the harness | Restart the harness after editing its config; check the config file path |
| MCP returns a plan, not an execution | Expected. MCP is dry-run only. Execute with the CLI `--confirm` on the device |
| Device not in `devices list` | Stop and ask — do not invent a device name. Pair it first |
