#!/usr/bin/env python3
"""Test the native messaging host end to end over its stdio protocol."""

import json
import os
import struct
import subprocess
import tempfile
import time
from pathlib import Path

HOST = Path(__file__).resolve().parent / "native-host" / "shepherd-native-host"


def run_host(message, shepherd_bin, raw=None):
    """Send one framed message to the host, return its decoded reply."""
    data = raw if raw is not None else json.dumps(message).encode()
    env = dict(os.environ, SHEPHERD_BIN=str(shepherd_bin))
    with tempfile.TemporaryDirectory() as state:
        env["XDG_STATE_HOME"] = state
        out = subprocess.run(
            [str(HOST)],
            input=struct.pack("=I", len(data)) + data,
            capture_output=True,
            env=env,
            timeout=10,
        ).stdout
    (length,) = struct.unpack("=I", out[:4])
    assert len(out) == 4 + length, f"trailing bytes on stdout: {out!r}"
    return json.loads(out[4:])


def fake_shepherd(tmpdir):
    """A stand-in shepherd that records its argv."""
    record = Path(tmpdir) / "argv.json"
    script = Path(tmpdir) / "fake-shepherd"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"open({str(record)!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
    )
    script.chmod(0o755)
    return script, record


def wait_for(path, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists() and path.stat().st_size:
            return json.loads(path.read_text())
    raise AssertionError(f"{path} never written")


def test_routes_https_url():
    with tempfile.TemporaryDirectory() as tmpdir:
        script, record = fake_shepherd(tmpdir)
        reply = run_host({"url": "https://github.com/d1rewolf/shepherd"}, script)
        assert reply == {"ok": True}, reply
        assert wait_for(record) == ["https://github.com/d1rewolf/shepherd"]
    print("✓ https URL routed to shepherd")


def test_rejects_unsafe_urls():
    bad = ["--incognito", "javascript:alert(1)", "file:///etc/passwd",
           "chrome://settings", "", None, "https://x.com/\nevil"]
    with tempfile.TemporaryDirectory() as tmpdir:
        script, record = fake_shepherd(tmpdir)
        for url in bad:
            reply = run_host({"url": url}, script)
            assert reply["ok"] is False, f"{url!r} accepted: {reply}"
        time.sleep(0.3)
        assert not record.exists(), "shepherd ran for a rejected URL"
    print("✓ flag-like and non-http(s) URLs rejected")


def test_malformed_message():
    with tempfile.TemporaryDirectory() as tmpdir:
        script, _ = fake_shepherd(tmpdir)
        reply = run_host(None, script, raw=b"not json")
        assert reply["ok"] is False
    print("✓ malformed message answered with an error, not a crash")


def test_manifest_key_matches_extension_id():
    import base64
    import hashlib
    root = Path(__file__).resolve().parent
    key = json.loads((root / "browser-extension" / "manifest.json").read_text())["key"]
    digest = hashlib.sha256(base64.b64decode(key)).hexdigest()[:32]
    ext_id = "".join(chr(ord("a") + int(c, 16)) for c in digest)
    assert f'EXTENSION_ID="{ext_id}"' in (root / "native-host" / "install.sh").read_text()
    print(f"✓ manifest key matches install.sh extension id ({ext_id})")


if __name__ == "__main__":
    test_routes_https_url()
    test_rejects_unsafe_urls()
    test_malformed_message()
    test_manifest_key_matches_extension_id()
    print("\nAll native host tests passed")
