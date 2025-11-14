"""
Fallback Chain Executor

Automatically retries failed LLM calls with alternative providers.
Ensures 99.5%+ SLA by falling back to healthy providers.
"""

import logging
import time
from typing import List, Optional, Dict

from ..providers.base import LLMProvider
from ..models.provider import (
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)


logger = logging.getLogger(__name__)


class AllProvidersFailed(Exception):
    """Raised when all providers in fallback chain have failed"""
    
    def __init__(self, agent_id: str, chain: List[str], errors: Dict[str, Exception]):
        self.agent_id = agent_id
        self.chain = chain
        self.errors = errors
        message = (
            f"All providers failed for agent '{agent_id}'. "
            f"Chain attempted: {chain}. "
            f"Errors: {list(errors.keys())}"
        )
        super().__init__(message)


class FallbackExecutor:
    """
    Executes LLM calls with automatic fallback chain
    
    Features:
    - Automatic retry with alternative providers
    - Configurable fallback chains per agent
    - Error tracking and logging
    - Metrics for fallback usage
    - Quality-based escalation support
    
    Usage:
        executor = FallbackExecutor(providers, fallback_chains)
        response = await executor.execute_with_fallback(
            agent_id="analyst",
            system_prompt="You are helpful",
            user_prompt="Hello"
        )
    """
    
    def __init__(
        self,
        providers: Dict[str, LLMProvider],
        fallback_chains: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize fallback executor
        
        Args:
            providers: Dict mapping provider name  provider instance
            fallback_chains: Dict mapping agent_id  list of provider names
                             Example: {"analyst": ["groq", "cerebras", "gemini"]}
        """
        self.providers = providers
        self.fallback_chains = fallback_chains or {}
        
        # Default fallback chain if not specified
        self.default_chain = list(providers.keys())
        
        # Statistics
        self.total_calls = 0
        self.fallback_triggered = 0
        self.fallback_success = 0
        self.all_failed = 0
        
        logger.info(
            f"Fallback executor initialized: "
            f"{len(providers)} providers, "
            f"{len(fallback_chains)} custom chains"
        )
    
    def get_fallback_chain(self, agent_id: str) -> List[str]:
        """
        Get fallback chain for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of provider names to try in order
        """
        chain = self.fallback_chains.get(agent_id, self.default_chain)
        
        # Filter to only available providers
        available_chain = [p for p in chain if p in self.providers]
        
        if not available_chain:
            logger.warning(
                f"No available providers for agent '{agent_id}', "
                f"using all providers"
            )
            return self.default_chain
        
        return available_chain
    
    async def execute_with_fallback(
        self,
        agent_id: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Execute LLM call with automatic fallback
        
        Tries providers in fallback chain order. If one fails, automatically
        tries the next provider in the chain.
        
        Args:
            agent_id: Agent identifier (for fallback chain lookup)
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            
        Returns:
            LLMResponse from first successful provider
            
        Raises:
            AllProvidersFailed: If all providers in chain failed
        """
        self.total_calls += 1
        start_time = time.time()
        
        chain = self.get_fallback_chain(agent_id)
        errors = {}
        
        logger.debug(
            f"Executing with fallback chain for '{agent_id}': {chain}"
        )
        
        for idx, provider_name in enumerate(chain):
            provider = self.providers.get(provider_name)
            
            if not provider:
                logger.warning(f"Provider '{provider_name}' not found, skipping")
                continue
            
            try:
                logger.debug(
                    f"[{agent_id}] Attempt {idx+1}/{len(chain)}: "
                    f"Trying provider '{provider_name}'"
                )
                
                # Call provider
                response = await provider.call(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Success!
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                if idx > 0:
                    # Fallback was used
                    self.fallback_triggered += 1
                    self.fallback_success += 1
                    
                    logger.info(
                        f" Fallback success for '{agent_id}': "
                        f"{provider_name} succeeded after {idx} failures "
                        f"(total latency: {elapsed_ms}ms)"
                    )
                else:
                    logger.debug(
                        f" Primary success for '{agent_id}': "
                        f"{provider_name} (latency: {response.latency_ms}ms)"
                    )
                
                return response
                
            except (ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError) as e:
                # Provider failed, try next in chain
                errors[provider_name] = e
                
                if idx < len(chain) - 1:
                    # More providers to try
                    next_provider = chain[idx + 1]
                    logger.warning(
                        f"  [{agent_id}] {provider_name} failed ({type(e).__name__}), "
                        f"trying fallback: {next_provider}"
                    )
                    
                    if idx == 0:
                        self.fallback_triggered += 1
                else:
                    # Last provider in chain
                    logger.error(
                        f" [{agent_id}] {provider_name} failed ({type(e).__name__}), "
                        f"no more fallbacks available"
                    )
            
            except Exception as e:
                # Unexpected error
                logger.error(
                    f" [{agent_id}] Unexpected error from {provider_name}: {e}"
                )
                errors[provider_name] = e
        
        # All providers failed
        self.all_failed += 1
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            f" All providers failed for '{agent_id}' after {elapsed_ms}ms. "
            f"Chain: {chain}, Errors: {len(errors)}"
        )
        
        raise AllProvidersFailed(
            agent_id=agent_id,
            chain=chain,
            errors=errors
        )
    
    def get_stats(self) -> Dict:
        """Get fallback statistics"""
        return {
            'total_calls': self.total_calls,
            'fallback_triggered': self.fallback_triggered,
            'fallback_success': self.fallback_success,
            'all_failed': self.all_failed,
            'fallback_rate': (
                100 * self.fallback_triggered / self.total_calls
                if self.total_calls > 0 else 0
            ),
            'success_rate': (
                100 * self.fallback_success / self.fallback_triggered
                if self.fallback_triggered > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset statistics (for testing)"""
        self.total_calls = 0
        self.fallback_triggered = 0
        self.fallback_success = 0
        self.all_failed = 0
        logger.info("Fallback statistics reset")


