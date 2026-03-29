# Rica - Sandboxed Python Code Executor (Docker Version)
# Runs code securely inside an offline, memory-limited Docker container.

import asyncio
import tempfile
import os

# Maximum output sizes
MAX_STDOUT_BYTES = 50_000    # 50 KB stdout cap
MAX_FILE_BYTES = 10_000_000  # 10 MB total file output cap
MAX_CONCURRENT_EXECUTIONS = int(os.environ.get("RICA_EXECUTOR_MAX_CONCURRENCY", "3"))
EXECUTOR_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)


async def execute_python(code: str, server_id: str, message=None, config: dict = None) -> dict:
    """
    Execute Python code in a sandboxed Docker container.

    Returns: {
        "output": "stdout text",
        "error": "stderr text or None",
        "files": [{"name": "file.png", "data": bytes}, ...]
    }
    """
    async with EXECUTOR_SEMAPHORE:
        with tempfile.TemporaryDirectory(prefix=f"Rica_{server_id}_") as tmpdir:
            setup_code = f"""
import sys
import os
import io

OUTPUT_DIR = '/workspace'

_output_files = []
def save_output(data: bytes, filename: str):
    \"\"\"Save a file that will be sent back to Discord.\"\"\"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'wb') as f:
        f.write(data)
    _output_files.append(filename)

"""
            full_code = setup_code + code + """

# Print files for collection
if _output_files:
    print(f"__FILES__:{','.join(_output_files)}")
"""
            code_file = os.path.join(tmpdir, "script.py")
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(full_code)

            try:
                abs_tmpdir = os.path.abspath(tmpdir)

                process = await asyncio.create_subprocess_exec(
                    "docker", "run",
                    "--rm", "-i",
                    "--network", "none",
                    "--memory", "128m",
                    "--cpus", "0.5",
                    "--pids-limit", "64",
                    "-v", f"{abs_tmpdir}:/workspace",
                    "-w", "/workspace",
                    "python:3.10-slim",
                    "python", "script.py",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )

                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.communicate()
                    return {
                        "output": "",
                        "error": "⏱️ Execution timed out (30s limit)",
                        "files": [],
                    }

                output = stdout.decode("utf-8", errors="replace")
                error = stderr.decode("utf-8", errors="replace") if process.returncode != 0 else None

                if len(output) > MAX_STDOUT_BYTES:
                    output = output[:MAX_STDOUT_BYTES] + "\n... (output truncated at 50KB limit)"

                files = []
                total_file_size = 0
                if "__FILES__:" in output:
                    lines = output.split("\n")
                    clean_lines = []
                    for line in lines:
                        if line.startswith("__FILES__:"):
                            try:
                                file_names = line.split(":", 1)[1].split(",")
                                for fname in file_names:
                                    fpath = os.path.join(tmpdir, fname.strip())
                                    if os.path.exists(fpath):
                                        file_size = os.path.getsize(fpath)
                                        total_file_size += file_size
                                        if total_file_size > MAX_FILE_BYTES:
                                            error = (error or "") + (
                                                f"\n⚠️ Total file output exceeds {MAX_FILE_BYTES // 1_000_000}MB limit. Some files were skipped."
                                            )
                                            break
                                        with open(fpath, "rb") as f:
                                            files.append({"name": fname.strip(), "data": f.read()})
                            except Exception:
                                pass
                        else:
                            clean_lines.append(line)
                    output = "\n".join(clean_lines)

                return {
                    "output": output.strip(),
                    "error": error.strip() if error else None,
                    "files": files,
                }

            except Exception as e:
                return {
                    "output": "",
                    "error": f"Failed to start Docker sandbox: {e}\nMake sure Docker is installed on the host.",
                    "files": [],
                }
