"""Cleanup script to enforce audit log retention policy."""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime, timedelta


async def cleanup(retention_days: int = 90):
    """
    Delete audit logs older than retention_days.

    Args:
        retention_days: Number of days to retain logs (default: 90)
    """
    # Get connection parameters from environment
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "squad")
    password = os.getenv("POSTGRES_PASSWORD", "squad123")
    database = os.getenv("POSTGRES_DB", "squad_api")

    print(
        f"Connecting to PostgreSQL at {host}:{port}/{database} for cleanup (retention: {retention_days} days)..."
    )

    try:
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database=database
        )
    except Exception as e:
        print(f" Failed to connect to database: {e}")
        sys.exit(1)

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        print(f"Deleting audit logs older than {cutoff_date.isoformat()}...")

        result = await conn.execute(
            "DELETE FROM audit_logs WHERE timestamp < $1", cutoff_date
        )

        # Parse "DELETE N" to get count
        deleted_count = int(result.split()[-1]) if result and result.startswith("DELETE") else 0
        print(
            f" Deleted {deleted_count} audit logs older than {retention_days} days"
        )

    except Exception as e:
        print(f" Cleanup failed: {e}")
        sys.exit(1)

    finally:
        await conn.close()


if __name__ == "__main__":
    # Allow override via command line argument
    retention = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    asyncio.run(cleanup(retention))

