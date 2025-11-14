"""Database migration script to create audit_logs table."""

import asyncio
import asyncpg
import os
import sys


async def migrate():
    """Create audit_logs table and indexes."""
    # Get connection parameters from environment
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "squad")
    password = os.getenv("POSTGRES_PASSWORD", "squad123")
    database = os.getenv("POSTGRES_DB", "squad_api")

    print(f"Connecting to PostgreSQL at {host}:{port}/{database}...")

    try:
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database=database
        )
    except Exception as e:
        print(f" Failed to connect to database: {e}")
        sys.exit(1)

    try:
        print("Creating audit_logs table...")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_id VARCHAR(100),
                conversation_id VARCHAR(100),
                agent VARCHAR(50) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                latency_ms INTEGER,
                tokens_in INTEGER,
                tokens_out INTEGER,
                error_message TEXT,
                request_id VARCHAR(100),
                metadata JSONB
            )
        """
        )
        print(" Table audit_logs created")

        print("Creating indexes...")
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)"
        )
        print("   idx_audit_timestamp")

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)"
        )
        print("   idx_audit_user")

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent)"
        )
        print("   idx_audit_agent")

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status)"
        )
        print("   idx_audit_status")

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_provider ON audit_logs(provider)"
        )
        print("   idx_audit_provider")

        print("\n Migration completed successfully")

    except Exception as e:
        print(f" Migration failed: {e}")
        sys.exit(1)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())

