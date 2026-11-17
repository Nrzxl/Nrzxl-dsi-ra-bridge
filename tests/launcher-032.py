"""Exercise the packaged .cmd directly on Windows, without PowerShell policy edits."""
import json, re, subprocess, sys, time, urllib.request
from pathlib import Path
launcher = Path(sys.argv[1]).resolve()
assert sys.platform == "win32" and launcher.is_file()
p = subprocess.Popen(["cmd.exe", "/d", "/c", str(launcher)], cwd=str(launcher.parent),
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     creationflags=subprocess.CREATE_NO_WINDOW)
try:
    deadline = time.monotonic() + 15
    state = None
    while time.monotonic() < deadline:
        if p.poll() is not None:
            output, _ = p.communicate(timeout=2)
            raise RuntimeError("CMD exited before HTTP startup: " + output.decode(errors="replace"))
        try:
            with urllib.request.urlopen("http://127.0.0.1:18217/state", timeout=1) as r:
                state = json.load(r)
            break
        except OSError:
            time.sleep(0.1)
    assert state is not None, "packaged CMD receiver failed to start"
    assert state["version"] == "0.3.2" and state["listen"] == "0.0.0.0:18216"
    # Engine spawn may complete just after HTTP startup.
    while not state["engine"]["available"] and time.monotonic() < deadline:
        time.sleep(0.1)
        with urllib.request.urlopen("http://127.0.0.1:18217/state") as r:
            state = json.load(r)
    assert state["engine"]["available"], "packaged native engine missing"
    with urllib.request.urlopen("http://127.0.0.1:18217/") as r:
        html = r.read().decode()
    token = re.search(r'const csrf="([a-f0-9]+)"', html).group(1)
    request = urllib.request.Request("http://127.0.0.1:18217/stop", data=b"",
                                    headers={"X-DSRB-Token": token}, method="POST")
    with urllib.request.urlopen(request) as r:
        assert r.status == 200
    output, _ = p.communicate(timeout=8)
    assert p.returncode == 0, output.decode(errors="replace")
    print(json.dumps(dict(status="PASS", launcher="packaged CMD on Windows", engine=True,
                          executionPolicyChanged=False, physical031="NOT_RUN")))
finally:
    if p.poll() is None:
        # Ensure test-only descendants cannot survive a failed assertion.
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW)
