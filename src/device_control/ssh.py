"""SSH driver — allowlist only, no free shell."""
import shutil
import subprocess

ALLOWED = [
    ["uname", "-a"], ["hostname"],
    ["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
    ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"],
]


def probe(host, user=""):
    if not shutil.which("ssh"):
        return False, "ssh not found"
    target = f"{user}@{host}" if user else host
    out = {}
    for cmd in ALLOWED:
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                                target] + cmd, capture_output=True, text=True, timeout=30)
            out[" ".join(cmd)] = r.stdout.strip() or r.stderr.strip()
        except Exception as e:
            out[" ".join(cmd)] = f"error: {e}"
    return True, out
