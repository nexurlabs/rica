from pathlib import Path
import sqlite3

DB_PATH = Path.home() / ".rica" / "rica.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"No local Rica database found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear local tables used by Rica's self-hosted runtime.
    tables = [
        "servers",
        "usage_stats",
        "error_logs",
        "sessions",
        "api_keys",
        "channel_configs",
    ]

    for table in tables:
        try:
            cur.execute(f"DELETE FROM {table}")
            print(f"Cleared table: {table}")
        except sqlite3.OperationalError:
            print(f"Skipped missing table: {table}")

    conn.commit()
    conn.close()
    print("Local Rica database reset complete.")


if __name__ == "__main__":
    main()
