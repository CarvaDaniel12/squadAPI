"""Local lightweight prompt optimizer/aggregator interface.

The orchestrator can optionally call into this module to transform a raw
user request into a structured :class:`PromptPlan` and later aggregate
specialist outputs back into a final response.  The heavy lifting (actual
LLM calls) is intentionally deferred so the project can run without the
local model enabled.
"""
from __future__ import annotations

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, Sequence

import aiohttp

from ..config.models import PromptOptimizerConfig
from ..models.prompt_plan import PromptPlan

logger = logging.getLogger(__name__)


class LocalPromptOptimizer:
    """Thin wrapper around a local small LLM used for planning and synthesis."""

    def __init__(self, config: Optional[PromptOptimizerConfig] = None):
        self.config = config
        self._model = None
        self._lock = asyncio.Lock()
        self._ollama_endpoint = None

        if not config or not config.enabled:
            logger.info("Local prompt optimizer disabled")
        else:
            logger.info(
                "Local prompt optimizer enabled using %s runtime (model=%s)",
                config.runtime,
                config.model_path if config.runtime != "ollama" else "ollama",
            )

            # Set Ollama endpoint if runtime is ollama
            if config.runtime == "ollama":
                self._ollama_endpoint = getattr(config, "endpoint", "http://localhost:11434")

    @property
    def enabled(self) -> bool:
        return bool(self.config and self.config.enabled)

    async def optimize(self, user_request: str) -> Optional[PromptPlan]:
        """Produce a structured :class:`PromptPlan` from natural language text."""
        if not self.enabled:
            return None

        # For Ollama runtime, use lightweight normalization
        if self.config and self.config.runtime == "ollama":
            return await self._optimize_with_ollama(user_request)

        await self._ensure_model_loaded()
        raise NotImplementedError(
            "Local prompt optimizer runtime is not implemented yet."
        )

    async def synthesize(self, plan: PromptPlan, specialist_outputs: Sequence[str]) -> Optional[str]:
        """Combine specialist outputs into a final response using the local model."""
        if not self.enabled:
            return None

        # For Ollama runtime, use API endpoint
        if self.config and self.config.runtime == "ollama":
            return await self._synthesize_with_ollama(plan, specialist_outputs)

        await self._ensure_model_loaded()
        raise NotImplementedError(
            "Local prompt optimizer synthesis is not implemented yet."
        )

    async def _ensure_model_loaded(self) -> None:
        if not self.enabled or self._model:
            return

        async with self._lock:
            if self._model:
                return

            runtime = self.config.runtime if self.config else ""
            if runtime == "ollama":
                # For Ollama, no local model loading needed - API-based
                self._model = "ollama"
            elif runtime == "llama-cpp":
                self._model = self._load_llama_cpp()
            elif runtime == "gpt4all":
                self._model = self._load_gpt4all()
            else:
                logger.warning("Unsupported prompt optimizer runtime '%s'", runtime)
                self._model = None

    def _load_llama_cpp(self):
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "llama-cpp-python is required for the local prompt optimizer"
            ) from exc

        config = self.config
        assert config is not None
        model_path = Path(config.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Prompt optimizer model not found: {model_path}")

        logger.info("Loading llama.cpp model from %s", model_path)
        return Llama(
            model_path=str(model_path),
            n_ctx=config.max_context_tokens,
            temperature=config.temperature,
        )

    def _load_gpt4all(self):  # pragma: no cover
        try:
            from gpt4all import GPT4All  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "gpt4all package is required for the local prompt optimizer"
            ) from exc

        config = self.config
        assert config is not None
        model_path = Path(config.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Prompt optimizer model not found: {model_path}")

        logger.info("Loading GPT4All model from %s", model_path)
        return GPT4All(model_name=str(model_path))

    async def _optimize_with_ollama(self, user_request: str) -> Optional[PromptPlan]:
        """Use Ollama to normalize and structure user request into a lightweight plan.

        This is a simplified version that doesn't require full BMAD compliance.
        For production, this would call Ollama to analyze the request.
        """
        logger.debug("Optimizing prompt with Ollama: %s", user_request[:100])

        # For now, return None to skip optimization (passthrough mode)
        # This allows the system to work without full PromptPlan complexity
        # The orchestrator will handle the request directly
        return None

    async def _synthesize_with_ollama(self, plan: PromptPlan, specialist_outputs: Sequence[str]) -> Optional[str]:
        """Use Ollama to aggregate specialist outputs into a final response."""
        if not specialist_outputs:
            return None

        # If only one output, return it directly
        if len(specialist_outputs) == 1:
            return specialist_outputs[0]

        logger.info("Synthesizing %d specialist outputs with Ollama", len(specialist_outputs))

        model = self.config.model_path if self.config else "llama3.2:3b"

        # Build synthesis prompt
        outputs_text = "\n\n---\n\n".join([
            f"Output {i+1}:\n{output}"
            for i, output in enumerate(specialist_outputs)
        ])

        prompt = f"""You are an expert technical aggregator. Your task is to synthesize multiple specialist outputs into a single, coherent response.

Original Request: {plan.user_request}

Specialist Outputs:
{outputs_text}

Instructions:
- Combine the insights from all outputs
- Remove redundancy and contradictions
- Maintain technical accuracy
- Provide a clear, unified response
- Keep the tone professional and concise

Synthesized Response:"""

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature if self.config else 0.3,
                        "num_predict": 2000
                    }
                }

                async with session.post(
                    f"{self._ollama_endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error("Ollama synthesis failed: HTTP %d - %s", resp.status, error_text)
                        # Fallback: return first output
                        return specialist_outputs[0]

                    result = await resp.json()
                    synthesized = result.get("response", "").strip()

                    if synthesized:
                        logger.info("✓ Ollama synthesis successful (%d chars)", len(synthesized))
                        return synthesized
                    else:
                        logger.warning("Ollama returned empty response, using first output")
                        return specialist_outputs[0]

        except asyncio.TimeoutError:
            logger.error("Ollama synthesis timeout, using first output")
            return specialist_outputs[0]
        except Exception as exc:
            logger.error("Ollama synthesis error: %s, using first output", exc)
            return specialist_outputs[0]
