"""
Cost Optimization Service
Intelligent provider routing to minimize costs while maintaining quality

Features:
- Automatic routing based on task complexity
- Budget tracking and enforcement
- Fallback to free tier when budget exceeded
- Cost metrics and reporting
"""

import logging
import yaml
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CostOptimizer:
    """
    Manages cost optimization for LLM provider usage

    Strategy:
    1. Route simple tasks to free providers
    2. Use paid providers only when necessary
    3. Track spending and enforce budgets
    4. Provide cost visibility and alerts
    """

    # Provider costs (USD per 1M tokens)
    PROVIDER_COSTS = {
        'groq': {'input': 0.0, 'output': 0.0},
        'cerebras': {'input': 0.0, 'output': 0.0},
        'gemini': {'input': 0.0, 'output': 0.0},
        'openrouter': {'input': 0.0, 'output': 0.0},
        'openai_mini': {'input': 0.15, 'output': 0.60},
        'gemini_pro': {'input': 0.35, 'output': 1.05},
        'openai': {'input': 2.50, 'output': 10.00},
        'anthropic': {'input': 3.00, 'output': 15.00},
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize cost optimizer

        Args:
            config_path: Path to cost_optimization.yaml
        """
        self.config_path = config_path or Path("config/cost_optimization.yaml")
        self.config = self._load_config()

        # Cost tracking
        self.daily_costs: Dict[str, float] = defaultdict(float)
        self.user_costs: Dict[str, float] = defaultdict(float)
        self.conversation_costs: Dict[str, float] = defaultdict(float)
        self.last_reset = datetime.now()

        # Request tracking
        self.paid_requests_today = 0
        self.free_requests_today = 0

        logger.info("Cost optimizer initialized with daily budget: $%.2f",
                   self.config.get('cost_limits', {}).get('daily_budget', 5.0))

    def _load_config(self) -> dict:
        """Load cost optimization configuration"""
        if not self.config_path.exists():
            logger.warning(f"Cost config not found: {self.config_path}, using defaults")
            return self._default_config()

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        """Default configuration when file not found"""
        return {
            'cost_limits': {
                'daily_budget': 5.0,
                'alert_at_percent': 80,
                'budget_exceeded_action': 'fallback_to_free'
            },
            'routing_rules': {
                'simple': {'providers': ['groq', 'cerebras', 'gemini']},
                'medium': {'providers': ['groq', 'gemini', 'openai_mini']},
                'complex': {'providers': ['groq', 'openai_mini', 'openai']},
                'critical': {'providers': ['anthropic', 'openai']}
            }
        }

    def select_provider(
        self,
        task_complexity: str = 'simple',
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        available_providers: Optional[List[str]] = None
    ) -> str:
        """
        Select optimal provider based on task complexity and budget

        Args:
            task_complexity: simple, medium, complex, or critical
            agent_id: Agent making the request
            user_id: User ID for cost tracking
            available_providers: List of available provider names

        Returns:
            Selected provider name
        """
        self._check_daily_reset()

        # Get routing rules for this task
        routing = self.config.get('routing_rules', {}).get(task_complexity, {})
        preferred_providers = routing.get('providers', ['groq', 'gemini'])

        # Check if budget exceeded
        budget = self.config.get('cost_limits', {}).get('daily_budget', 5.0)
        current_spend = sum(self.daily_costs.values())

        if current_spend >= budget:
            logger.warning(f"Daily budget exceeded: ${current_spend:.2f} / ${budget:.2f}")
            action = self.config.get('cost_limits', {}).get('budget_exceeded_action', 'fallback_to_free')

            if action == 'fallback_to_free':
                # Force free providers only
                preferred_providers = [p for p in preferred_providers
                                     if self.PROVIDER_COSTS.get(p, {}).get('input', 0) == 0]
                logger.info(f"Restricting to free providers: {preferred_providers}")

        # Filter by available providers
        if available_providers:
            preferred_providers = [p for p in preferred_providers if p in available_providers]

        if not preferred_providers:
            logger.error("No available providers after filtering!")
            return 'groq'  # Safe default

        # Select first available provider
        selected = preferred_providers[0]
        logger.info(f"Selected provider '{selected}' for {task_complexity} task")

        return selected

    def calculate_cost(
        self,
        provider: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """
        Calculate cost for a provider call

        Args:
            provider: Provider name
            tokens_input: Input tokens
            tokens_output: Output tokens

        Returns:
            Cost in USD
        """
        costs = self.PROVIDER_COSTS.get(provider, {'input': 0, 'output': 0})

        cost = (
            (tokens_input / 1_000_000) * costs['input'] +
            (tokens_output / 1_000_000) * costs['output']
        )

        return cost

    def record_usage(
        self,
        provider: str,
        tokens_input: int,
        tokens_output: int,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ):
        """
        Record usage and update cost tracking

        Args:
            provider: Provider used
            tokens_input: Input tokens
            tokens_output: Output tokens
            user_id: User ID
            conversation_id: Conversation ID
        """
        cost = self.calculate_cost(provider, tokens_input, tokens_output)

        # Track daily costs
        self.daily_costs[provider] += cost

        # Track per-user costs
        if user_id:
            self.user_costs[user_id] += cost

        # Track per-conversation costs
        if conversation_id:
            self.conversation_costs[conversation_id] += cost

        # Count requests
        if cost > 0:
            self.paid_requests_today += 1
        else:
            self.free_requests_today += 1

        # Log if significant cost
        if cost > 0.01:
            logger.info(
                f"Cost recorded: ${cost:.4f} ({provider}, "
                f"{tokens_input} in / {tokens_output} out tokens)"
            )

        # Check budget alerts
        self._check_budget_alerts()

    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        now = datetime.now()

        if now.date() > self.last_reset.date():
            logger.info(
                f"Daily reset - Total spent yesterday: ${sum(self.daily_costs.values()):.2f}"
            )
            self.daily_costs.clear()
            self.paid_requests_today = 0
            self.free_requests_today = 0
            self.last_reset = now

    def _check_budget_alerts(self):
        """Check if budget alert threshold reached"""
        budget = self.config.get('cost_limits', {}).get('daily_budget', 5.0)
        alert_threshold = self.config.get('cost_limits', {}).get('alert_at_percent', 80)

        current_spend = sum(self.daily_costs.values())
        percent_used = (current_spend / budget) * 100

        if percent_used >= alert_threshold:
            logger.warning(
                f"⚠️  BUDGET ALERT: {percent_used:.1f}% of daily budget used "
                f"(${current_spend:.2f} / ${budget:.2f})"
            )

    def get_stats(self) -> dict:
        """
        Get current cost statistics

        Returns:
            Dict with cost stats
        """
        budget = self.config.get('cost_limits', {}).get('daily_budget', 5.0)
        current_spend = sum(self.daily_costs.values())

        return {
            'daily_budget': budget,
            'daily_spend': current_spend,
            'budget_remaining': budget - current_spend,
            'percent_used': (current_spend / budget) * 100 if budget > 0 else 0,
            'paid_requests': self.paid_requests_today,
            'free_requests': self.free_requests_today,
            'costs_by_provider': dict(self.daily_costs),
            'top_users': sorted(
                [(user, cost) for user, cost in self.user_costs.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def print_report(self):
        """Print cost report to console"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("💰 COST OPTIMIZATION REPORT")
        print("="*60)
        print(f"Daily Budget:     ${stats['daily_budget']:.2f}")
        print(f"Current Spend:    ${stats['daily_spend']:.4f}")
        print(f"Remaining:        ${stats['budget_remaining']:.4f}")
        print(f"Budget Used:      {stats['percent_used']:.1f}%")
        print(f"\nRequests Today:")
        print(f"  Free:           {stats['free_requests']}")
        print(f"  Paid:           {stats['paid_requests']}")
        print(f"\nCosts by Provider:")
        for provider, cost in stats['costs_by_provider'].items():
            print(f"  {provider:15s} ${cost:.4f}")
        print("="*60 + "\n")
