"""
Context Window Management
Story 1.9: Context Window Management

Ensures conversation + system prompt fits within LLM context window
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ContextWindowManager:
    """Manages context window to prevent overflow"""

    # Context limits per provider (tokens)
    CONTEXT_LIMITS = {
        "groq": 8192,      # llama-3-70b: 8k context
        "cerebras": 8192,  # llama-3-8b: 8k context
        "gemini": 1_000_000,  # gemini-2.5-flash: 1M context
        "openrouter": 8192,   # Default: 8k
        "anthropic": 200_000,  # Claude 3.5 Sonnet: 200k context
    }

    def __init__(self, max_context: int = 8192):
        """
        Initialize Context Window Manager

        Args:
            max_context: Maximum context window size in tokens
        """
        self.max_context = max_context

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)

        Rule of thumb: 1 token  4 characters

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def trim_messages(
        self,
        messages: List[Dict],
        system_prompt: str,
        max_tokens: Optional[int] = None
    ) -> List[Dict]:
        """
        Trim message history to fit within context window

        Strategy:
        - Keep system prompt (always)
        - Keep most recent user message (always)
        - Trim older messages from middle if needed

        Args:
            messages: List of messages [{"role": "...", "content": "..."}]
            system_prompt: System prompt text
            max_tokens: Max context window (uses self.max_context if None)

        Returns:
            Trimmed messages list that fits in context
        """
        max_tokens = max_tokens or self.max_context

        # Calculate current usage
        system_tokens = self.estimate_tokens(system_prompt)
        messages_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        total_tokens = system_tokens + messages_tokens

        # If fits, return as-is
        if total_tokens <= max_tokens:
            logger.debug(f"Context window OK: {total_tokens}/{max_tokens} tokens")
            return messages

        # Need to trim
        logger.warning(f"Context window overflow: {total_tokens}/{max_tokens} tokens - trimming...")

        # Keep system (index 0) and latest user message
        if len(messages) <= 2:
            # Can't trim further
            return messages

        # Strategy: Remove from middle (oldest messages)
        # Keep first (system) and last few messages
        trimmed = [messages[0]]  # System

        # Calculate budget for history
        budget = max_tokens - system_tokens - self.estimate_tokens(messages[-1]["content"])

        # Add recent messages until budget exhausted
        for msg in reversed(messages[1:-1]):  # Skip system and last
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if budget - msg_tokens >= 0:
                trimmed.insert(1, msg)  # Insert after system
                budget -= msg_tokens
            else:
                break

        # Add last message
        trimmed.append(messages[-1])

        removed = len(messages) - len(trimmed)
        logger.info(f"Trimmed {removed} messages. New total: {len(trimmed)} messages")

        return trimmed

    def get_context_limit(self, provider: str) -> int:
        """Get context limit for provider"""
        return self.CONTEXT_LIMITS.get(provider, 8192)


from typing import Optional  # Add missing import


