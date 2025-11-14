"""
OpenRouter Smart Fallback
Auto-discovers and retries with available FREE models on failure

When a request fails, automatically:
1. Fetches current FREE models from OpenRouter API
2. Picks the best available model
3. Retries the request
"""

import logging
import asyncio
import aiohttp
from typing import Optional, List, Dict
from pathlib import Path
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OpenRouterSmartFallback:
    """
    Intelligent fallback for OpenRouter

    When a model fails (404, rate limit, etc.), automatically discovers
    available FREE models and retries with the best one.
    """

    def __init__(self, api_key: str, cache_duration_minutes: int = 60):
        """
        Initialize smart fallback

        Args:
            api_key: OpenRouter API key
            cache_duration_minutes: How long to cache model list
        """
        self.api_key = api_key
        self.cache_duration = timedelta(minutes=cache_duration_minutes)

        # Cache
        self._cached_models: List[Dict] = []
        self._cache_time: Optional[datetime] = None

        # Track failures
        self._failed_models = set()

    async def discover_free_models(self, force_refresh: bool = False) -> List[Dict]:
        """
        Discover all FREE models available on OpenRouter

        Args:
            force_refresh: Force refresh even if cache valid

        Returns:
            List of free model dicts with id, name, context, etc.
        """
        # Check cache
        if not force_refresh and self._cached_models and self._cache_time:
            if datetime.now() - self._cache_time < self.cache_duration:
                logger.debug(f"Using cached models ({len(self._cached_models)} models)")
                return self._cached_models

        logger.info("🔍 Discovering FREE models from OpenRouter API...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to fetch models: {resp.status}")
                        return self._cached_models  # Return old cache if available

                    data = await resp.json()
                    models = data.get('data', [])

            # Filter for FREE models
            free_models = []
            for model in models:
                pricing = model.get('pricing', {})
                prompt_price = float(pricing.get('prompt', '0'))
                completion_price = float(pricing.get('completion', '0'))

                if prompt_price == 0 and completion_price == 0:
                    free_models.append({
                        'id': model['id'],
                        'name': model.get('name', model['id']),
                        'context': model.get('context_length', 0),
                        'description': model.get('description', ''),
                        'architecture': model.get('architecture', {}),
                    })

            # Sort by quality indicators
            # 1. Context length (bigger = better)
            # 2. Not in failed list
            free_models.sort(
                key=lambda x: (
                    x['id'] not in self._failed_models,  # Working models first
                    x['context']  # Then by context
                ),
                reverse=True
            )

            # Update cache
            self._cached_models = free_models
            self._cache_time = datetime.now()

            logger.info(f"✅ Discovered {len(free_models)} FREE models")

            return free_models

        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return self._cached_models  # Return old cache if available

    def pick_best_model(
        self,
        models: List[Dict],
        task_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Pick best model based on task type

        Args:
            models: List of available models
            task_type: 'code', 'reasoning', 'general', or None

        Returns:
            Model ID or None
        """
        if not models:
            return None

        # Filter out failed models
        available = [m for m in models if m['id'] not in self._failed_models]

        if not available:
            # All models failed, clear failures and try again
            logger.warning("All models failed, resetting failure list")
            self._failed_models.clear()
            available = models

        # Pick based on task type
        if task_type == 'code':
            # Prefer code-specialized models
            for model in available:
                name_lower = model['name'].lower()
                id_lower = model['id'].lower()
                if 'coder' in name_lower or 'code' in id_lower:
                    logger.info(f"🎯 Picked code model: {model['id']}")
                    return model['id']

        elif task_type == 'reasoning':
            # Prefer reasoning models
            for model in available:
                name_lower = model['name'].lower()
                id_lower = model['id'].lower()
                if 'deepseek' in name_lower or 'r1' in id_lower or 'chimera' in id_lower:
                    logger.info(f"🧠 Picked reasoning model: {model['id']}")
                    return model['id']

        # Default: pick largest context model
        best = available[0]
        logger.info(f"📊 Picked best available: {best['id']} ({best['context']}K context)")
        return best['id']

    async def call_with_auto_fallback(
        self,
        provider,  # OpenRouterProvider instance
        messages: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        task_type: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Call OpenRouter with automatic fallback on failure

        Args:
            provider: OpenRouterProvider instance
            messages: Messages to send (or None to build from prompts)
            system_prompt: System prompt (used if messages is None)
            user_prompt: User prompt (used if messages is None)
            task_type: Type of task for model selection
            max_retries: Max number of models to try
            **kwargs: Additional arguments for provider._direct_call()

        Returns:
            LLMResponse

        Raises:
            ProviderAPIError: If all models fail
        """
        original_model = provider.model
        attempts = 0

        while attempts < max_retries:
            try:
                # Try current model
                logger.info(f"🔄 Attempt {attempts + 1}: Using model {provider.model}")
                response = await provider._direct_call(
                    messages=messages,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    **kwargs
                )

                # Success! Return response
                logger.info(f"✅ Success with model: {provider.model}")
                return response

            except Exception as e:
                error_msg = str(e).lower()

                # Check if it's a "model not available" error
                is_model_unavailable = (
                    '404' in error_msg or
                    'not found' in error_msg or
                    'no endpoints' in error_msg or
                    'not a valid model' in error_msg or
                    ('429' in error_msg and 'temporarily rate-limited upstream' in error_msg)  # Upstream provider down
                )

                if is_model_unavailable:
                    logger.warning(f"❌ Model {provider.model} not available: {e}")

                    # Mark as failed
                    self._failed_models.add(provider.model)

                    # Discover available models
                    models = await self.discover_free_models()

                    if not models:
                        logger.error("No FREE models available!")
                        raise

                    # Pick best alternative
                    new_model = self.pick_best_model(models, task_type)

                    if not new_model or new_model == provider.model:
                        logger.error("No alternative models found")
                        raise

                    # Switch to new model
                    logger.info(f"🔀 Switching to: {new_model}")
                    provider.model = new_model
                    attempts += 1

                    # Small delay before retry
                    await asyncio.sleep(1)

                else:
                    # Different error (our rate limit, timeout, etc.)
                    logger.error(f"Non-fallback error: {e}")
                    raise        # All retries failed
        logger.error(f"Failed after {max_retries} attempts")
        provider.model = original_model  # Restore original
        raise Exception(f"All {max_retries} OpenRouter models failed")

    def mark_model_failed(self, model_id: str):
        """Mark a model as failed to avoid retrying it"""
        self._failed_models.add(model_id)
        logger.info(f"Marked {model_id} as failed")

    def clear_failures(self):
        """Clear failure list (e.g., after some time)"""
        self._failed_models.clear()
        logger.info("Cleared failure list")

    def get_stats(self) -> Dict:
        """Get statistics"""
        return {
            'cached_models': len(self._cached_models),
            'failed_models': len(self._failed_models),
            'cache_age_minutes': (
                (datetime.now() - self._cache_time).total_seconds() / 60
                if self._cache_time else None
            )
        }
