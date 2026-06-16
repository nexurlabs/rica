import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from executor import execute_python


class _Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_executor_exposes_discord_context_environment():
    message = _Obj(
        id=444,
        guild=_Obj(id=111),
        channel=_Obj(id=222),
        author=_Obj(id=333),
    )

    result = asyncio.run(
        execute_python(
            """
import os
print(os.environ["DISCORD_TOKEN"])
print(os.environ["DISCORD_BOT_TOKEN"])
print(os.environ["DISCORD_GUILD_ID"])
print(os.environ["DISCORD_CHANNEL_ID"])
print(os.environ["DISCORD_MESSAGE_ID"])
print(os.environ["DISCORD_AUTHOR_ID"])
""",
            "server-fallback",
            message=message,
            config={"discord_token": "raw-token"},
        )
    )

    assert result["error"] is None
    assert result["output"].splitlines() == [
        "Bot raw-token",
        "raw-token",
        "111",
        "222",
        "444",
        "333",
    ]
