"""Full test suite for device-control v1. Run: PYTHONPATH=src python3 -m unittest discover -s tests -v
No real device, no destructive action: all execution paths are
dry-run, mocked, or read-only on this Linux host.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, ROOT)
ENV = dict(os.environ, PYTHONPATH=ROOT)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cli(*args):
    return subprocess.run([sys.executable, "-m", "device_control.cli", *args],
                          capture_output=True, text=True, env=ENV, cwd=REPO)


class TestRegistry(unittest.TestCase):
    def test_default_devices_are_the_agreed_four(self):
        r = cli("devices", "list")
        self.assertEqual(r.returncode, 0, r.stderr)
        names = [d["name"] for d in json.loads(r.stdout)["devices"]]
        # Order may change after a pair() run rewrites the registry file;
        # the set is the contract, not the order.
        self.assertEqual(set(names), {"pc-windows", "laptop", "hp-android", "tv-android"})

    def test_add_and_remove_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "devices.json")
            from device_control import devices
            d = devices.Device(name="test-pc", kind="windows", transport="powershell", scopes=["windows.probe"])
            devices.add_device(d, path)
            self.assertIsNotNone(devices.get_device("test-pc", path))
            devices.remove_device("test-pc", path)
            self.assertIsNone(devices.get_device("test-pc", path))


class TestNeverLists(unittest.TestCase):
    def test_never_is_blocked_even_if_listed(self):
        from device_control import never
        safe, blocked = never.filter_never(
            ["com.android.systemui", "com.example.bloat"], "android")
        self.assertIn("com.android.systemui", blocked)
        self.assertIn("com.example.bloat", safe)
        safe, blocked = never.filter_never(["systemd", "cups"], "linux-pkg")
        self.assertIn("systemd", blocked)
        self.assertIn("cups", safe)


class TestSecurity(unittest.TestCase):
    def test_audit_chain_verify(self):
        from device_control import security
        with tempfile.TemporaryDirectory() as td:
            chain = security.AuditChain(os.path.join(td, "audit.jsonl"))
            chain.append("tv-android", "probe", "ok")
            chain.append("tv-android", "debloat dry-run", "ok")
            ok, count = chain.verify()
            self.assertTrue(ok)
            self.assertEqual(count, 2)

    def test_token_expiry_and_command_hash(self):
        from device_control import security
        tok = security.make_token("tv-android", "adb.probe", "probe tv", ttl_seconds=60)
        ok, _ = security.verify_token(tok, "probe tv")
        self.assertTrue(ok)
        ok, msg = security.verify_token(tok, "different command")
        self.assertFalse(ok)
        self.assertIn("hash", msg)

    def test_ed25519_keypair_via_openssl_or_cryptography(self):
        from device_control import security
        # Use a temp HOME by monkeypatching KEY_DIR
        with tempfile.TemporaryDirectory() as td:
            old = security.KEY_DIR
            security.KEY_DIR = td
            try:
                pub, fp, backend = security.generate_keypair("test-device")
                self.assertEqual(len(pub), 32)
                self.assertEqual(len(fp), 64)
                self.assertIn("ed25519", backend)
            finally:
                security.KEY_DIR = old

    def test_pairing_sas_format(self):
        from device_control import pairing
        with tempfile.TemporaryDirectory() as td:
            from device_control import security
            old = security.KEY_DIR
            security.KEY_DIR = td
            try:
                info = pairing.pair("hp-android")
                self.assertRegex(info["sas_code"], r"^\d{3} \d{3}$")
                self.assertEqual(len(info["public_key_fingerprint_sha256"]), 64)
            finally:
                security.KEY_DIR = old


class TestDriversDryRun(unittest.TestCase):
    def test_windows_appearance_script_dark(self):
        from device_control import windows
        cmds = windows.appearance_commands("dark")
        self.assertTrue(any("AppsUseLightTheme" in c and "0" in c for c in cmds))

    def test_linux_appearance_dark(self):
        from device_control import linux
        cmds = linux.appearance_commands("dark")
        self.assertTrue(any("prefer-dark" in c for c in cmds))

    def test_android_appearance_minimal_mentions_launcher_first(self):
        from device_control import android
        cmds = android.appearance_commands("minimal")
        self.assertTrue(cmds[0].startswith("# 1. Install"))

    def test_adb_parse_list_ignores_comments(self):
        from device_control import adb
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            f.write("# comment\ncom.example.a\n\ncom.example.b\n")
            path = f.name
        self.assertEqual(adb.parse_debloat_list(path), ["com.example.a", "com.example.b"])

    def test_adb_debloat_dry_run_makes_no_change(self):
        from device_control import adb
        ok, res = adb.debloat(packages=["com.example.a"], dry_run=True)
        self.assertTrue(ok)
        self.assertTrue(res["dry_run"])


class TestCLI(unittest.TestCase):
    def test_appearance_dry_run_windows(self):
        r = cli("appearance", "--device", "pc-windows", "--profile", "dark", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["dry_run"])

    def test_appearance_dry_run_tv(self):
        r = cli("appearance", "--device", "tv-android", "--profile", "minimal", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["dry_run"])

    def test_debloat_dry_run_blocks_never(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            f.write("com.android.systemui\ncom.example.bloat\n")
            path = f.name
        r = cli("debloat", "--device", "tv-android", "--list", path, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("com.android.systemui", data["blocked_never"])
        self.assertIn("com.example.bloat", data["would_disable"])

    def test_unknown_device_fails(self):
        r = cli("probe", "--device", "tidak-ada")
        self.assertNotEqual(r.returncode, 0)

    def test_linux_probe_readonly_on_this_host(self):
        # This host is Linux, so laptop probe should return real package info, read-only
        r = cli("probe", "--device", "laptop")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("package_count", data)

    def test_pair_and_audit_and_token(self):
        r = cli("pair", "--device", "hp-android")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertRegex(data["sas_code"], r"^\d{3} \d{3}$")
        r = cli("audit")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = cli("token", "--device", "hp-android", "--scope", "adb.probe", "--command", "probe")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nonce", json.loads(r.stdout))


class TestLaunch(unittest.TestCase):
    def test_windows_launch(self):
        from device_control import windows
        self.assertIn("Start-Process", windows.launch_command("notepad.exe"))

    def test_linux_launch(self):
        from device_control import linux
        self.assertIn("nohup", linux.launch_command("firefox"))

    def test_android_launch_monkey(self):
        from device_control import android
        cmd = android.launch_command("com.netflix.ninja")
        self.assertIn("monkey -p com.netflix.ninja", cmd)
        self.assertIn("LAUNCHER", cmd)

    def test_cli_launch_dry_run(self):
        r = cli("launch", "--device", "tv-android", "--app", "com.netflix.ninja", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["dry_run"])
        self.assertIn("com.netflix.ninja", data["would_run"])

    def test_cli_launch_dry_run_windows(self):
        r = cli("launch", "--device", "pc-windows", "--app", "notepad.exe", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Start-Process", json.loads(r.stdout)["would_run"])


class TestUIAndSearch(unittest.TestCase):
    SAMPLE_XML = """<?xml version="1.0"?><hierarchy><node text="" resource-id="" class="android.widget.FrameLayout" clickable="false" bounds="[0,0][1080,2400]"><node text="Buka" resource-id="com.example:id/open" class="android.widget.Button" clickable="true" bounds="[100,200][300,300]" /><node text="Netflix" resource-id="" class="android.widget.TextView" clickable="false" bounds="[100,400][500,500]" /></node></hierarchy>"""

    def test_parse_dump_and_find_button(self):
        from device_control import ui
        parsed = ui.parse_dump(self.SAMPLE_XML)
        self.assertEqual(parsed["count"], 3)
        node = ui.find_by_text(parsed["nodes"], "buka")
        self.assertIsNotNone(node)
        self.assertEqual(node["center"], [200, 250])
        self.assertTrue(node["clickable"])

    def test_find_missing_button_returns_none(self):
        from device_control import ui
        parsed = ui.parse_dump(self.SAMPLE_XML)
        self.assertIsNone(ui.find_by_text(parsed["nodes"], "tidak ada"))

    def test_search_known_alias(self):
        from device_control import appsearch
        pkgs = ["com.netflix.ninja", "com.whatsapp", "com.google.android.youtube"]
        res = appsearch.search("Netflix", pkgs)
        self.assertEqual(res["best"]["package"], "com.netflix.ninja")
        self.assertEqual(res["best"]["score"], 100)
        self.assertFalse(res["ambiguous"])

    def test_search_by_name_only_no_package(self):
        from device_control import appsearch
        pkgs = ["com.spotify.music", "com.whatsapp"]
        res = appsearch.search("spotify", pkgs)
        self.assertEqual(res["best"]["package"], "com.spotify.music")

    def test_search_ambiguous_when_no_match(self):
        from device_control import appsearch
        res = appsearch.search("aplikasi entah", ["com.whatsapp"])
        self.assertTrue(res["ambiguous"])
        self.assertIsNone(res["best"])

    def test_cli_ui_dry_run_and_search_dry_run(self):
        r = cli("ui", "--device", "tv-android", "tap", "--text", "Buka", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["dry_run"])
        r = cli("search-app", "--device", "hp-android", "--query", "Netflix", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["dry_run"])
        r = cli("screenshot", "--device", "tv-android", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["dry_run"])


class TestWinLinuxUI(unittest.TestCase):
    def test_winui_script_uses_official_uia(self):
        import pathlib
        text = pathlib.Path(os.path.join(REPO, "scripts", "winui.ps1")).read_text()
        for needle in ["UIAutomationClient", "AutomationElement]::RootElement",
                       "FindFirst", "InvokePattern", "ValuePattern", "TreeScope"]:
            self.assertIn(needle, text)

    def test_winui_command_generation(self):
        from device_control import winui
        cmd = winui.command("Click", window="Calculator", name="7")
        self.assertIn("winui.ps1", " ".join(cmd))
        self.assertIn("Calculator", cmd)
        self.assertIn("7", cmd)

    def test_linuxui_find_unique_and_ambiguous(self):
        from device_control import linuxui
        class Fake:
            def __init__(self, name, children=None):
                self.name = name; self._c = children or []
                self.childCount = len(self._c)
            def getRoleName(self): return "push button"
            def getChildAt(self, i): return self._c[i]
        root = Fake("Window", [Fake("Login"), Fake("Cancel")])
        node, msg = linuxui.find_unique(root, "login")
        self.assertEqual(node.name, "Login")
        root2 = Fake("Window", [Fake("Save"), Fake("Save As")])
        node, msg = linuxui.find_unique(root2, "save")
        self.assertIsNone(node)
        self.assertIn("ambiguous", msg)

    def test_cli_ui_windows_dry_run(self):
        r = cli("ui", "--device", "pc-windows", "tap", "--window", "Calculator", "--text", "7", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["dry_run"])
        self.assertIn("winui.ps1", data["would_run"])

    def test_cli_ui_linux_dry_run(self):
        r = cli("ui", "--device", "laptop", "dump", "--window", "Firefox", "--dry-run")
        # laptop on this Linux host goes to linux-atspi path
        self.assertEqual(r.returncode, 0, r.stderr)


class TestMCP(unittest.TestCase):
    def _mcp(self, payload):
        p = subprocess.run([sys.executable, "-m", "device_control.mcp_server"],
                           input=payload, capture_output=True, text=True, env=ENV, cwd=REPO)
        self.assertEqual(p.returncode, 0, p.stderr)
        return [json.loads(l) for l in p.stdout.strip().splitlines() if l.strip()]

    def test_initialize_and_tools_list(self):
        out = self._mcp('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n'
                        '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n')
        self.assertEqual(out[0]["result"]["serverInfo"]["name"], "device-control")
        names = [t["name"] for t in out[1]["result"]["tools"]]
        self.assertIn("device_list", names)
        self.assertIn("device_debloat", names)
        self.assertIn("audit_verify", names)

    def test_mcp_debloat_is_always_dry_run(self):
        out = self._mcp('{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device_debloat","arguments":{"device":"tv-android","list_file":"examples/debloat/generic-safe.txt"}}}\n')
        content = json.loads(out[0]["result"]["content"][0]["text"])
        self.assertTrue(content["dry_run"])

    def test_mcp_launch_is_dry_run(self):
        out = self._mcp('{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device_launch","arguments":{"device":"tv-android","app":"com.netflix.ninja"}}}\n')
        content = json.loads(out[0]["result"]["content"][0]["text"])
        self.assertTrue(content["dry_run"])
        self.assertIn("com.netflix.ninja", content["would_run"])

    def test_open_website_validates_and_builds_commands(self):
        from device_control import openwebsite, windows, linux, android
        self.assertTrue(openwebsite.validate_url("https://github.com")[0])
        self.assertFalse(openwebsite.validate_url("javascript:alert(1)")[0])
        self.assertFalse(openwebsite.validate_url("https://x.com/a'b")[0])
        self.assertIn("Start-Process", windows.launch_command("", "https://example.com"))
        self.assertIn("xdg-open", linux.launch_command("", "https://example.com"))
        self.assertIn("VIEW", android.launch_command("", "", "https://example.com"))

    def test_cli_open_website_dry_run_windows(self):
        r = cli("open-website", "--device", "pc-windows", "--url", "https://example.com", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("Start-Process", data["would_run"])
        self.assertTrue(data["dry_run"])

    def test_cli_open_website_rejects_bad_url(self):
        r = cli("open-website", "--device", "pc-windows", "--url", "javascript:alert(1)", "--dry-run")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("error", json.loads(r.stdout))

    def test_mcp_open_website_is_dry_run(self):
        out = self._mcp('{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device_open_website","arguments":{"device":"pc-windows","url":"https://example.com"}}}\n')
        content = json.loads(out[0]["result"]["content"][0]["text"])
        self.assertTrue(content["dry_run"])
        self.assertIn("Start-Process", content["would_run"])

    def test_mcp_unknown_method_errors(self):
        out = self._mcp('{"jsonrpc":"2.0","id":1,"method":"bogus/method"}\n')
        self.assertIn("error", out[0])


if __name__ == "__main__":
    unittest.main()
