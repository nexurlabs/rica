# Rica - Sandboxed Python Code Executor (Docker Version)
# Runs code securely inside an offline, memory-limited Docker container.

import asyncio
import tempfile
import os

# Maximum output sizes
MAX_STDOUT_BYTES = 50_000   # 50 KB stdout cap
MAX_FILE_BYTES = 10_000_000  # 10 MB total file output cap

async def execute_python(code: str, server_id: str, message=None, config: dict = None) -> dict:
    """
    Execute Python code in a sandboxed Docker container.

    Args:
        code: Python code to execute
        server_id: Server ID (for context)
        message: Discord message
        config: Server config

    Returns: {
        "output": "stdout text",
        "error": "stderr text or None",
        "files": [{"name": "file.png", "data": bytes}, ...]
    }
    """
    with tempfile.TemporaryDirectory(prefix=f"Rica_{server_id}_") as tmpdir:
        # We need a setup script to grab output files
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
            # Run in docker container process with strict limits
            abs_tmpdir = os.path.abspath(tmpdir)
            
            # Note: We must convert standard paths to format Docker expects if on Windows locally (for testing), 
            # but usually this runs on Linux VMs where abspath is perfect.
            # Docker requires absolute paths for volumes.
            
            process = await asyncio.create_subprocess_exec(
                "docker", "run",
                "--rm", "-i",                    # Auto-remove, interactive
                "--network", "none",             # NO INTERNET ACCESS
                "--memory", "128m",              # 128 MB RAM max
                "--cpus", "0.5",                 # 50% CPU core max
                "--pids-limit", "64",            # Prevent fork bombs
                # mount tmpdir to /workspace (rw)
                "-v", f"{abs_tmpdir}:/workspace",    
                "-w", "/workspace",              # Working directory inside
                "python:3.10-slim",              # Tiny python image
                "python", "script.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmpdir,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            except asyncio.TimeoutError:
                # If docker hangs, kill it
                process.kill()
                return {"output": "", "error": "⏱️ Execution timed out (30s limit)", "files": []}

            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace") if process.returncode != 0 else None

            # Enforce limits
            if len(output) > MAX_STDOUT_BYTES:
                output = output[:MAX_STDOUT_BYTES] + "\\n... (output truncated at 50KB limit)"

            # Collect files written to tmpdir
            files = []
            total_file_size = 0
            if "__FILES__:" in output:
                lines = output.split("\\n")
                clean_lines = []
                for line in lines:
                    if line.startswith("__FILES__:"):
                        try:
                            file_names = line.split(":")[1].split(",")
                            for fname in file_names:
                                fpath = os.path.join(tmpdir, fname.strip())
                                if os.path.exists(fpath):
                                    file_size = os.path.getsize(fpath)
                                    total_file_size += file_size
                                    if total_file_size > MAX_FILE_BYTES:
                                        error = (error or "") + f"\\n⚠️ Total file output exceeds {MAX_FILE_BYTES // 1_000_000}MB limit. Some files were skipped."
                                        break
                                    with open(fpath, "rb") as f:
                                        files.append({"name": fname.strip(), "data": f.read()})
                        except Exception:
                            pass
                    else:
                        clean_lines.append(line)
                output = "\\n".join(clean_lines)

            return {
                "output": output.strip(),
                "error": error.strip() if error else None,
                "files": files,
            }

        except Exception as e:
            return {"output": "", "error": f"Failed to start Docker sandbox: {e}\\nMake sure Docker is installed on the host.", "files": []}

