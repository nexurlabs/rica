# Rica - Sandboxed Python Code Executor (Docker)
# Network-enabled for Discord API, resource-limited, scoped filesystem.

import asyncio
import tempfile
import os

MAX_STDOUT_BYTES = 50_000
MAX_FILE_BYTES = 10_000_000
MAX_CONCURRENT_EXECUTIONS = int(os.environ.get("RICA_EXECUTOR_MAX_CONCURRENCY", "3"))
EXECUTOR_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)


async def execute_python(code: str, server_id: str, message=None, config: dict = None) -> dict:
    """
    Execute Python code in a Docker container.
    - Network: ENABLED (Discord API + internet access)
    - Filesystem: /workspace is bind-mounted from the host tmpdir so file
      outputs (save_output) survive after the container exits
    - Resources: 256MB RAM, 0.5 CPU, 32 processes max
    - Timeout: 60 seconds
    - Cannot: access host files, escape container, use GPU
    """
    async with EXECUTOR_SEMAPHORE:
        with tempfile.TemporaryDirectory(prefix=f"Rica_{server_id}_") as tmpdir:
            # `outdir` is bind-mounted to /workspace inside the container so
            # files written via save_output persist on the host for collection.
            outdir = os.path.join(tmpdir, "output")
            os.makedirs(outdir, exist_ok=True)

            setup_code = r"""
import sys, os, asyncio, httpx

# ── Patch discord.py so send/reply gracefully handles stale references ──
import discord
_orig_send = discord.TextChannel.send
async def _safe_send(self, content=None, *, reference=None, **kwargs):
    if reference is not None:
        try:
            return await _orig_send(self, content=content, reference=reference, **kwargs)
        except discord.HTTPException as e:
            if e.status == 400 and e.code == 50035:
                # "Invalid Form Body – Unknown message" means the referenced
                # message no longer exists (deleted or expired). Retry without ref.
                return await _orig_send(self, content=content, **kwargs)
            raise
    return await _orig_send(self, content=content, **kwargs)
discord.TextChannel.send = _safe_send
# Also patch for Thread and VoiceChannel if they exist
for _cls in (discord.Thread,):
    try:
        _cls.send = _safe_send
    except Exception:
        pass

# ── Output file helper ──
OUTPUT_DIR = '/workspace'
_output_files = []
def save_output(data: bytes, filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'wb') as f:
        f.write(data)
    _output_files.append(filename)
"""
            full_code = setup_code + "\n" + code + "\nprint('__FILES__:' + ','.join(_output_files))\n"

            code_file = os.path.join(tmpdir, "script.py")
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(full_code)

            try:
                abs_tmpdir = os.path.abspath(tmpdir)
                abs_outdir = os.path.abspath(outdir)
                discord_token = config.get("discord_token", "") if config else ""

                # Build extended env vars from the message object
                guild_id = str(server_id)
                channel_id = ""
                author_id = ""
                message_id = ""
                if message is not None:
                    guild_id = str(message.guild.id)
                    channel_id = str(message.channel.id)
                    author_id = str(message.author.id)
                    message_id = str(message.id)

                # All env vars to pass into the Docker container
                docker_env = (
                    f"-e DISCORD_TOKEN=\"Bot {discord_token}\" "
                    f"-e DISCORD_BOT_TOKEN={discord_token} "
                    f"-e SERVER_ID={guild_id} "
                    f"-e DISCORD_GUILD_ID={guild_id} "
                    f"-e DISCORD_CHANNEL_ID={channel_id} "
                    f"-e DISCORD_MESSAGE_ID={message_id} "
                    f"-e DISCORD_AUTHOR_ID={author_id} "
                )

                # Use sg docker to run with docker group permissions.
                # Bind-mount the host output dir as /workspace so files
                # written via save_output() survive after the container exits.
                docker_sh = (
                    f"sg docker -c 'docker run --rm -i "
                    f"--network bridge "
                    f"--memory 256m --memory-swap 256m "
                    f"--cpus 0.5 --pids-limit 32 "
                    f"-v {abs_outdir}:/workspace:rw "
                    f"-v {abs_tmpdir}/script.py:/workspace/script.py:ro "
                    f"-w /workspace "
                    f"{docker_env}"
                    f"rica-executor python /workspace/script.py'"
                )

                # Minimal env for the outer bash - the actual secrets go into the Docker container via docker_env
                clean_env = {
                    "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games",
                    "PYTHONDONTWRITEBYTECODE": "1",
                }

                process = await asyncio.create_subprocess_exec(
                    "bash", "-c", docker_sh,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd="/tmp",
                    env=clean_env,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.communicate()
                    return {
                        "output": "",
                        "error": "⏱️ Execution timed out (60s limit)",
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
                                    fname = fname.strip()
                                    if not fname:
                                        continue
                                    # Files were written to /workspace inside the
                                    # container, which is bind-mounted to outdir
                                    # on the host, so they survive past exit.
                                    fpath = os.path.join(outdir, fname)
                                    if os.path.exists(fpath):
                                        file_size = os.path.getsize(fpath)
                                        total_file_size += file_size
                                        if total_file_size > MAX_FILE_BYTES:
                                            error = (error or "") + f"\n⚠️ File output exceeds 10MB limit."
                                            break
                                        with open(fpath, "rb") as f:
                                            files.append({"name": fname, "data": f.read()})
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

            except FileNotFoundError:
                return {
                    "output": "",
                    "error": "❌ Docker not found on this system.",
                    "files": [],
                }
            except Exception as e:
                return {
                    "output": "",
                    "error": f"Execution error: {e}",
                    "files": [],
                }