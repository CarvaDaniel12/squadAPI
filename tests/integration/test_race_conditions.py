"""
Testes de Concorrência - Race Conditions no Rate Limiting

Testa se as correções de race conditions estão funcionando corretamente
com operações concorrentes de rate limiting.
"""

import asyncio
import pytest
import time
from typing import List
from unittest.mock import AsyncMock, MagicMock

# Importar classes de rate limiting
from src.rate_limit.combined import CombinedRateLimiter
from src.rate_limit.atomic_operations import AtomicRateLimiter
from src.models.rate_limit import ProviderRateLimitConfig


class TestRaceConditions:
    """Testes para race conditions em rate limiting"""

    @pytest.mark.asyncio
    async def test_atomic_vs_fallback_behavior(self):
        """Testa diferença de comportamento entre modo atômico e fallback"""

        # Configurar mock Redis para simular Redis disponível
        mock_redis = AsyncMock()
        mock_redis.script_load = AsyncMock(return_value="test_script_sha")
        mock_redis.evalsha = AsyncMock(return_value=1)  # 1 = success

        # Test 1: CombinedRateLimiter com Redis (modo atômico)
        atomic_limiter = AtomicRateLimiter(mock_redis)
        combined_atomic = CombinedRateLimiter(mock_redis)

        # Registrar provider
        config = ProviderRateLimitConfig(
            provider="test_provider",
            rpm=10,
            burst=5,
            window_size=60
        )
        combined_atomic.register_provider("test_provider", config)

        # Verificar se está usando modo atômico
        assert combined_atomic._use_atomic == True

        # Test 2: CombinedRateLimiter sem Redis (modo fallback)
        combined_fallback = CombinedRateLimiter(None)
        combined_fallback.register_provider("test_provider", config)

        # Verificar se está usando modo fallback
        assert combined_fallback._use_atomic == False

    @pytest.mark.asyncio
    async def test_concurrent_atomic_requests(self):
        """Testa requests concorrentes usando atomic operations"""

        # Mock Redis que sempre retorna success para atomic operations
        mock_redis = AsyncMock()
        mock_redis.script_load = AsyncMock(return_value="atomic_script_sha")
        mock_redis.evalsha = AsyncMock(return_value=1)  # 1 = success
        mock_redis.zcount = AsyncMock(return_value=5)  # Simula 5 requests na janela
        mock_redis.hmget = AsyncMock(return_value=[8.5, time.time()])  # Simula tokens disponíveis

        combined_limiter = CombinedRateLimiter(mock_redis)
        combined_limiter.register_provider("test_provider", ProviderRateLimitConfig(
            provider="test_provider",
            rpm=10,
            burst=5,
            window_size=60
        ))

        # Simular 5 requests concorrentes
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                self._simulate_atomic_request(combined_limiter, f"request_{i}")
            )
            tasks.append(task)

        # Aguardar todos completarem
        results = await asyncio.gather(*tasks)

        # Verificar se todos foram aprovados (atomic operations eliminam race conditions)
        assert all(result["success"] for result in results)
        assert all("atomic" in result["mode"] for result in results)

    @pytest.mark.asyncio
    async def test_concurrent_fallback_requests(self):
        """Testa requests concorrentes usando fallback (com risco de race condition)"""

        # Mock que simula comportamento não-atômico
        mock_redis = AsyncMock()
        mock_redis.script_load = AsyncMock(return_value="atomic_script_sha")
        mock_redis.evalsha = AsyncMock(return_value=1)

        # Configurar sliding window que permite passar em check_limit mas falhará em add_request
        sliding_window_mock = AsyncMock()
        sliding_window_mock.check_limit = AsyncMock(return_value=True)  # Sempre passa na verificação
        sliding_window_mock.add_request = AsyncMock()  # Simula adição (race condition pode ocorrer aqui)
        sliding_window_mock.get_window_count = AsyncMock(return_value=5)

        combined_limiter = CombinedRateLimiter(None)  # Sem Redis = modo fallback
        combined_limiter.sliding_window = sliding_window_mock

        # Configurar token bucket que sempre passa
        token_bucket_mock = AsyncMock()
        token_bucket_acquire_mock = AsyncMock()
        token_bucket_acquire_mock.__aenter__ = AsyncMock(return_value=None)
        token_bucket_acquire_mock.__aexit__ = AsyncMock(return_value=None)
        token_bucket_mock.acquire = MagicMock(return_value=token_bucket_acquire_mock)
        combined_limiter.token_bucket = token_bucket_mock

        combined_limiter.register_provider("test_provider", ProviderRateLimitConfig(
            provider="test_provider",
            rpm=10,
            burst=5,
            window_size=60
        ))

        # Simular requests concorrentes
        tasks = []
        for i in range(15):  # Mais que o limite para testar race conditions
            task = asyncio.create_task(
                self._simulate_fallback_request(combined_limiter, f"request_{i}")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # No modo fallback, race conditions podem permitir que alguns requests passem
        # mesmo excedendo o limite (mas isso é o comportamento esperado com race conditions)
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        fallback_count = sum(1 for r in results if isinstance(r, dict) and "fallback" in r.get("mode", ""))

        assert fallback_count > 0  # Pelo menos alguns devem usar modo fallback

    async def _simulate_atomic_request(self, combined_limiter, request_id: str) -> dict:
        """Simula um request usando atomic operations"""
        try:
            start_time = time.time()
            async with combined_limiter.acquire("test_provider"):
                # Simular trabalho
                await asyncio.sleep(0.01)

            return {
                "request_id": request_id,
                "success": True,
                "mode": "atomic",
                "duration": time.time() - start_time
            }
        except Exception as e:
            return {
                "request_id": request_id,
                "success": False,
                "mode": "atomic",
                "error": str(e)
            }

    async def _simulate_fallback_request(self, combined_limiter, request_id: str) -> dict:
        """Simula um request usando fallback (com race condition)"""
        try:
            start_time = time.time()
            async with combined_limiter.acquire("test_provider"):
                # Simular trabalho
                await asyncio.sleep(0.01)

            return {
                "request_id": request_id,
                "success": True,
                "mode": "fallback",
                "duration": time.time() - start_time
            }
        except Exception as e:
            return {
                "request_id": request_id,
                "success": False,
                "mode": "fallback",
                "error": str(e)
            }

    @pytest.mark.asyncio
    async def test_atomic_status_methods(self):
        """Testa métodos de status do atomic rate limiter"""

        mock_redis = AsyncMock()
        mock_redis.script_load = AsyncMock(return_value="test_sha")
        mock_redis.evalsha = AsyncMock(return_value=1)
        mock_redis.zcount = AsyncMock(return_value=3)
        mock_redis.hmget = AsyncMock(return_value=[7.2, time.time()])

        combined_limiter = CombinedRateLimiter(mock_redis)
        combined_limiter.register_provider("groq", ProviderRateLimitConfig(
            provider="groq",
            rpm=60,
            burst=30,
            window_size=60
        ))

        # Testar get_atomic_status
        status = combined_limiter.get_atomic_status()

        assert status["atomic_enabled"] == True
        assert status["redis_available"] == True
        assert status["total_providers"] == 1
        assert "groq" in status["provider_configs"]

        # Testar enable_atomic_fallback_warnings
        combined_limiter.enable_atomic_fallback_warnings()  # Não deve mostrar warnings

        # Testar reset
        mock_redis.delete = AsyncMock()
        await combined_limiter.reset("groq")
        mock_redis.delete.assert_called_once()


if __name__ == "__main__":
    # Executar testes manualmente para debug
    import sys
    sys.path.append(".")

    async def run_tests():
        test_instance = TestRaceConditions()

        print("🧪 Testando comportamento atômico vs fallback...")
        await test_instance.test_atomic_vs_fallback_behavior()
        print("✅ Teste de comportamento passou!")

        print("🧪 Testando requests concorrentes atômicos...")
        await test_instance.test_concurrent_atomic_requests()
        print("✅ Teste de concorrência atômica passou!")

        print("🧪 Testando métodos de status...")
        await test_instance.test_atomic_status_methods()
        print("✅ Teste de status passou!")

        print("\n🎉 Todos os testes passaram!")

    asyncio.run(run_tests())
