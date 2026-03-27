# Rica Tests - Executor Security

import sys
import os
import shutil
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from executor import execute_python, MAX_STDOUT_BYTES

# Skip tests if Docker is not installed (e.g., local Windows environment)
pytestmark = pytest.mark.skipif(
    not shutil.which("docker"),
    reason="Docker is required to run the code execution sandbox tests."
)

def _run(code, server_id="test"):
    return asyncio.get_event_loop().run_until_complete(
        execute_python(code, server_id)
    )

class TestExecutorSecurity:
    """Tests for sandboxed code execution security in Docker."""

    def test_basic_execution(self):
        result = _run('print("hello world")')
        assert result["output"] == "hello world"
        assert result["error"] is None

    def test_math_works(self):
        result = _run("print(2 + 2)")
        assert result["output"] == "4"

    def test_no_network_access(self):
        # The container should have --network none, so this will fail
        result = _run('''
import urllib.request
try:
    urllib.request.urlopen("http://example.com", timeout=2)
    print("success")
except Exception as e:
    print(f"failed: {e}")
''')
        # It should NOT print success
        assert "success" not in result["output"]
        assert "failed" in result["output"] or result["error"]

    def test_timeout(self):
        result = _run("import time; time.sleep(60)")
        assert result["error"] is not None
        assert "timed out" in result["error"].lower()

    def test_stdout_size_limit(self):
        # Generate output larger than MAX_STDOUT_BYTES
        result = _run(f'print("x" * {MAX_STDOUT_BYTES + 10000})')
        assert "truncated" in result["output"].lower()

    def test_allows_write_inside_sandbox(self):
        result = _run("""
import os
# Writing inside OUTPUT_DIR (the sandbox) should work
with open(os.path.join(OUTPUT_DIR, "test.txt"), "w") as f:
    f.write("safe content")
print("write succeeded")
""")
        assert "write succeeded" in result["output"]
        assert result["error"] is None

    def test_file_output_collection(self):
        result = _run("""
save_output(b"test file content", "output.txt")
print("done")
""")
        assert "done" in result["output"]
        assert len(result["files"]) >= 1
        assert any(f["name"] == "output.txt" for f in result["files"])
