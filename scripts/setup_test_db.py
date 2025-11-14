"""Setup script to run unit tests with local PostgreSQL."""

import os
import asyncio
import asyncpg
import sys


async def setup_test_database():
    """Create test database and tables in local PostgreSQL."""

    # Hardcoded for local PostgreSQL
    host = "localhost"
    port = 5432
    user = "postgres"
    password = "impale145"
    database = "squad_api_test"

    print(f"Conectando ao PostgreSQL local: {host}:{port}...")

    try:
        # First connect to default postgres database to create test db
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        print(" Conectado ao PostgreSQL!")

        # Create test database
        try:
            await conn.execute(f"CREATE DATABASE {database}")
            print(f" Database '{database}' criado!")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f" Database '{database}' j existe")

        await conn.close()

        # Now connect to test database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        print(f" Conectado ao database '{database}'!")

        # Create audit_logs table
        print("Criando tabela audit_logs...")
        await conn.execute("""
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
        """)
        print(" Tabela audit_logs criada!")

        # Create indexes
        print("Criando ndices...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_provider ON audit_logs(provider)")
        print(" ndices criados!")

        await conn.close()

        print("\n Banco de testes configurado com sucesso!")
        print("\nAgora pode rodar os testes:")
        print("python -m pytest tests/unit/test_audit_logger.py tests/integration/test_orchestrator_audit.py -v")

    except Exception as e:
        print(f" Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_test_database())


if __name__ == "__main__":
    asyncio.run(setup_test_database())

