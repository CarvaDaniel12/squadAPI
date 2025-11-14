"""
Stub LLM Provider for Testing

Fake provider that simulates LLM behavior without making real API calls.
Used for unit tests and development without API keys.
"""

import asyncio
import time
import logging
from typing import Optional, List, Dict, Any

from .base import LLMProvider
from ..models.provider import ProviderConfig, LLMResponse


logger = logging.getLogger(__name__)


class StubLLMProvider(LLMProvider):
    """
    Fake LLM provider for testing
    
    Features:
    - No real API calls (works offline)
    - Deterministic responses
    - Configurable fixed responses
    - Tracks call history
    - Simulates realistic latency
    - Supports all LLMProvider interface methods
    
    Usage:
        stub = StubLLMProvider(fixed_response="Test response")
        response = await stub.call("system", "user")
        assert stub.call_count == 1
    """
    
    def __init__(
        self,
        config: Optional[ProviderConfig] = None,
        fixed_response: Optional[str] = None,
        simulate_latency: bool = True,
        latency_range: tuple[int, int] = (50, 150)
    ):
        """
        Initialize stub provider
        
        Args:
            config: Provider config (uses default stub config if None)
            fixed_response: Fixed response text (uses echo if None)
            simulate_latency: Whether to simulate realistic latency
            latency_range: Min/max latency in milliseconds (default: 50-150ms)
        """
        # Create default config if not provided
        if config is None:
            config = ProviderConfig(
                name="stub",
                type="stub",
                model="stub-model-v1",
                rpm_limit=9999,  # No limit for testing
                tpm_limit=999999,
                max_tokens=2000,
                temperature=0.7,
                timeout=30
            )
        
        super().__init__(config)
        
        self.fixed_response = fixed_response
        self.simulate_latency = simulate_latency
        self.latency_range = latency_range
        
        # Call tracking
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []
        
        # Health status (can be toggled for testing)
        self._is_healthy = True
        
        logger.info(f"Stub provider initialized: simulate_latency={simulate_latency}")
    
    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Simulate LLM call
        
        Supports two calling conventions:
        1. call(system_prompt="...", user_prompt="...")  # Direct
        2. call(messages=[...])  # OpenAI format (from orchestrator)
        
        Returns fixed response or echoes user prompt.
        Tracks call history for inspection.
        """
        start_time = time.time()
        
        # Handle different calling conventions
        if messages is not None:
            # OpenAI format: extract system and user from messages
            system_prompt = ""
            user_prompt = ""
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", "")
                elif msg.get("role") == "user":
                    user_prompt = msg.get("content", "")
        
        # Ensure we have prompts
        system_prompt = system_prompt or ""
        user_prompt = user_prompt or "ping"
        
        # Simulate realistic latency
        if self.simulate_latency:
            latency_ms = self.latency_range[0] + (
                (self.latency_range[1] - self.latency_range[0]) * 
                (self.call_count % 100) / 100
            )
            await asyncio.sleep(latency_ms / 1000.0)
        
        # Generate response
        if self.fixed_response:
            content = self.fixed_response
        else:
            # Echo mode: return user prompt with prefix
            content = f"[STUB] Received: {user_prompt}"
        
        # Estimate tokens
        tokens_input = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        tokens_output = self.count_tokens(content)
        
        # Calculate actual latency
        actual_latency = int((time.time() - start_time) * 1000)
        
        # Track call
        self.call_count += 1
        self.call_history.append({
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'response': content,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'max_tokens': max_tokens or self.config.max_tokens,
            'temperature': temperature or self.config.temperature,
            'kwargs': kwargs
        })
        
        logger.debug(
            f"Stub call #{self.call_count}: "
            f"in={tokens_input}, out={tokens_output}, latency={actual_latency}ms"
        )
        
        return LLMResponse(
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=actual_latency,
            model=self.model,
            finish_reason="stop",
            provider=self.name
        )
    
    async def health_check(self) -> bool:
        """
        Check stub health status
        
        Returns current health status (can be toggled for testing).
        """
        logger.debug(f"Stub health check: {self._is_healthy}")
        return self._is_healthy
    
    def set_healthy(self, is_healthy: bool):
        """Set health status (for testing error scenarios)"""
        self._is_healthy = is_healthy
        logger.info(f"Stub health status set to: {is_healthy}")
    
    def set_fixed_response(self, response: str):
        """Change fixed response (for testing different scenarios)"""
        self.fixed_response = response
        logger.debug(f"Stub fixed response updated: {response[:50]}...")
    
    def reset(self):
        """Reset call tracking (for test isolation)"""
        self.call_count = 0
        self.call_history.clear()
        self._is_healthy = True
        logger.debug("Stub provider reset")
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get last call details (for test assertions)"""
        return self.call_history[-1] if self.call_history else None
    
    def assert_called_once(self):
        """Assert that call was made exactly once"""
        if self.call_count != 1:
            raise AssertionError(
                f"Expected 1 call, but got {self.call_count}"
            )
    
    def assert_called_with(self, user_prompt: str):
        """Assert that call was made with specific user prompt"""
        if not self.call_history:
            raise AssertionError("No calls made")
        
        last_call = self.get_last_call()
        if last_call['user_prompt'] != user_prompt:
            raise AssertionError(
                f"Expected user_prompt='{user_prompt}', "
                f"but got '{last_call['user_prompt']}'"
            )


# Default stub instance for quick testing
default_stub = StubLLMProvider()

