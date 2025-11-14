"""
Agent Execution Orchestrator
Story 1.7: Agent Execution Orchestrator

THE CORE MAGIC - Orchestrates agent execution via external LLMs
"""

import time
import logging
from collections import deque
from typing import Dict, List, Optional, Sequence, Set, Tuple
import uuid

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.plan_validator import ProcessComplianceError, validate_prompt_plan
from src.models.prompt_plan import PromptPlan, SpecialistTask
from src.models.request import AgentExecutionRequest
from src.models.response import AgentExecutionResponse, ExecutionMetadata
from src.models.provider import LLMResponse
from src.api.errors import AgentNotFoundException
from src.rate_limit.combined import CombinedRateLimiter
from src.rate_limit.semaphore import GlobalSemaphore
from src.security.pii import PIIDetector  # Story 9.1: PII Detection
from src.metrics.provider_status import ProviderStatusTracker  # Story 9.5: Provider status tracking
from src.providers.local_prompt_optimizer import LocalPromptOptimizer

# Observability (Epic 5)
from src.metrics.requests import (
    record_success,
    record_failure,
    record_429,
    record_request_success,
    record_request_failure,
    record_429_error,
    classify_error
)
from src.metrics.observability import record_latency, record_tokens, set_agent_active
from src.utils.logging import set_request_context, clear_request_context

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Core orchestrator for agent execution

    Coordinates:
    - Agent loading (AgentLoader)
    - System prompt building (SystemPromptBuilder)
    - Conversation management (ConversationManager)
    - Provider routing (AgentRouter)
    - LLM execution (Provider - Epic 3)
    """

    def __init__(
        self,
        agent_loader: AgentLoader,
        prompt_builder: SystemPromptBuilder,
        conversation_manager: ConversationManager,
        agent_router: AgentRouter,
        providers: Optional[dict] = None,  # Dict of provider_name -> provider instance
        rate_limiter: Optional[CombinedRateLimiter] = None,
        global_semaphore: Optional[GlobalSemaphore] = None,
        prompt_optimizer: Optional[LocalPromptOptimizer] = None,
        cost_optimizer=None,  # CostOptimizer for intelligent routing
        audit_logger=None,  # AuditLogger for logging executions
        provider_status_tracker: Optional[ProviderStatusTracker] = None,  # Story 9.5: Provider status tracking
    ):
        """
        Initialize Agent Orchestrator

        Args:
            agent_loader: Agent loader service
            prompt_builder: System prompt builder
            conversation_manager: Conversation state manager
            agent_router: Agent router
            rate_limiter: Combined rate limiter (optional, Epic 2)
            global_semaphore: Global concurrency semaphore (optional, Epic 2)
            provider_stub: Stub provider (temporary until Epic 3)
            audit_logger: AuditLogger for logging executions (optional, Epic 9)
        """
        self.loader = agent_loader
        self.prompt_builder = prompt_builder
        self.conv = conversation_manager
        self.router = agent_router
        self.rate_limiter = rate_limiter
        self.global_semaphore = global_semaphore
        self.audit_logger = audit_logger  # Store audit logger
        self.pii_detector = PIIDetector()  # Initialize PII detector (Story 9.1)
        self.provider_status_tracker = provider_status_tracker  # Story 9.5: Provider status tracking
        self.prompt_optimizer = prompt_optimizer
        self.cost_optimizer = cost_optimizer  # Cost optimization service

        # Multi-provider support (Epic 3)
        self.providers = providers or {}

        self.user_config = {
            "communication_language": "PT-BR",
            "user_name": "Dani"
        }

        # Log rate limiting status
        if rate_limiter:
            logger.info("Rate limiting enabled for agent orchestrator")
        else:
            logger.warning("Rate limiting DISABLED - not suitable for production!")

        if global_semaphore:
            logger.info(f"Global semaphore enabled: max {global_semaphore.max_concurrent} concurrent")
        else:
            logger.warning("Global semaphore DISABLED - no concurrency limiting!")

        if cost_optimizer:
            logger.info("Cost optimization enabled - intelligent provider routing")
        else:
            logger.info("Cost optimization disabled - using default routing")

    async def execute(
        self,
        request: AgentExecutionRequest
    ) -> AgentExecutionResponse:
        """
        Execute agent via external LLM

        This is THE CORE MAGIC that transforms external LLMs into BMad agents!

        Args:
            request: Agent execution request

        Returns:
            AgentExecutionResponse with agent's response

        Raises:
            ValueError: If agent not found
        """
        plan: Optional[PromptPlan] = None
        if self.prompt_optimizer and self.prompt_optimizer.enabled:
            plan = await self.prompt_optimizer.optimize(request.task)
            if plan is None:
                raise ProcessComplianceError("Prompt optimizer failed to produce a plan")
            validate_prompt_plan(plan, available_providers=self.providers.keys())

        # Determine task complexity and provider selection
        agent_id = request.agent

        # Determine task complexity for cost optimization
        task_complexity = self._determine_complexity(request, agent_id)

        # Select provider using cost optimizer if available
        if self.cost_optimizer:
            provider_name = self.cost_optimizer.select_provider(
                task_complexity=task_complexity,
                agent_id=agent_id,
                user_id=request.user_id,
                available_providers=list(self.providers.keys())
            )
        else:
            # Fallback to router
            provider_config = self.router.get_provider_for_agent(request.agent)
            provider_name = provider_config

        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Set request context for structured logging (Epic 5 - Story 5.4)
        set_request_context(request_id, request.agent, provider_name)

        try:

            logger.info(f"[{request_id}] Executing agent: {request.agent} for user: {request.user_id}")

            # 1. Load agent definition
            agent = await self.loader.get_agent(request.agent)

            if agent is None:
                raise AgentNotFoundException(request.agent)

            logger.debug(f"[{request_id}] Agent loaded: {agent.name} ({agent.title})")

            # 2. Build system prompt
            system_prompt = self.prompt_builder.build(agent, self.user_config)
            tokens_system = self.prompt_builder.estimate_tokens(system_prompt)

            logger.debug(f"[{request_id}] System prompt built: ~{tokens_system} tokens")

            # 3. Get conversation history
            history = await self.conv.get_messages(request.user_id, request.agent)

            logger.debug(f"[{request_id}] Conversation history: {len(history)} messages")

            # 4. Build messages array (OpenAI format)
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            messages.extend(history)
            messages.append({"role": "user", "content": request.task})

            # 4.5. Detect PII in user message (Story 9.1 - Production Readiness)
            pii_report = self.pii_detector.detect(request.task)
            if pii_report.has_pii:
                logger.warning(
                    f"[{request_id}] PII detected in user message",
                    extra={
                        "pii_types": pii_report.pii_types,
                        "pii_count": len(pii_report.matches),
                        "recommendation": pii_report.recommendation
                    }
                )
            else:
                logger.debug(f"[{request_id}] PII check passed: message is clean")

            if plan:
                (
                    response_content,
                    tokens_in,
                    tokens_out,
                    provider_name,
                    model_name,
                ) = await self._execute_prompt_plan(plan, request_id)
            elif self.providers:
                (
                    response_content,
                    tokens_in,
                    tokens_out,
                    provider_name,
                    model_name,
                ) = await self._call_single_provider(
                    provider_name,
                    messages,
                    request_id,
                    agent_id,
                    task_complexity,  # Pass complexity for smart fallback
                )
            else:
                # No providers configured - fail fast
                raise RuntimeError(
                    f"No LLM providers configured. Agent '{request.agent}' cannot be executed. "
                    "Please configure at least one LLM provider with valid API keys."
                )

            logger.info(f"[{request_id}] LLM response received: {len(response_content)} chars")

            # Record provider metrics (Story 9.5: Provider Status Tracking)
            if self.provider_status_tracker:
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.provider_status_tracker.record_request(
                    provider_name=provider_name,
                    latency_ms=elapsed_ms,
                    success=True
                )

            # 6. Save to conversation history
            await self.conv.add_message(request.user_id, request.agent, "user", request.task)
            await self.conv.add_message(request.user_id, request.agent, "assistant", response_content)

            # 7. Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(f"[{request_id}] Execution complete: {latency_ms}ms")

            # 8. Record metrics (Epic 5 - Stories 5.1, 5.2, 5.3)
            record_request_success(provider=provider_name, agent=agent_id)
            record_latency(provider_name, request.agent, latency_ms / 1000.0)  # Convert to seconds
            record_tokens(provider_name, tokens_in, tokens_out)  # No agent_id in this function

            # 8.3. Record cost usage (Cost Optimization)
            if self.cost_optimizer:
                self.cost_optimizer.record_usage(
                    provider=provider_name,
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    user_id=request.user_id,
                    conversation_id=request.conversation_id
                )

            # 8.5. Log to audit trail (Epic 9 - Story 9.3)
            if self.audit_logger:
                try:
                    await self.audit_logger.log_execution(
                        agent=request.agent,
                        provider=provider_name,
                        action="execute",
                        status="success",
                        latency_ms=latency_ms,
                        user_id=request.user_id,
                        conversation_id=request.conversation_id,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        request_id=request_id,
                        metadata=request.metadata,
                    )
                except Exception as audit_error:
                    # Don't break execution if audit logging fails
                    logger.error(f"[{request_id}] Audit logging failed: {audit_error}")

            # 9. Return response
            return AgentExecutionResponse(
                agent=request.agent,
                agent_name=agent.name,
                provider=provider_name,
                model=model_name,
                response=response_content,
                metadata=ExecutionMetadata(
                    request_id=request_id,
                    latency_ms=latency_ms,
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    fallback_used=False,
                    tool_calls_count=0,
                    turns=1
                )
            )

        except Exception as e:
            # Calculate latency for failed execution
            latency_ms = int((time.time() - start_time) * 1000)

            # Record provider metrics failure (Story 9.5: Provider Status Tracking)
            if self.provider_status_tracker:
                error_is_429 = isinstance(e, Exception) and "429" in str(e).upper()
                self.provider_status_tracker.record_request(
                    provider_name=provider_name,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e)[:100]  # Truncate error message
                )
                if error_is_429:
                    self.provider_status_tracker.record_rate_limit(provider_name)

            # Record failure metrics (Epic 5 - Story 5.1)
            error_type = classify_error(e)
            record_request_failure(
                provider=provider_name,
                agent=agent_id,
                error_type=error_type
            )

            # Record 429 metric if rate limit error (Epic 5 - Story 5.1)
            if error_type == 'rate_limit':
                record_429_error(provider=provider_name)

            # Log to audit trail (Epic 9 - Story 9.3)
            if self.audit_logger:
                try:
                    await self.audit_logger.log_execution(
                        agent=request.agent,
                        provider=provider_name,
                        action="execute",
                        status="failed",
                        latency_ms=latency_ms,
                        user_id=request.user_id,
                        conversation_id=request.conversation_id,
                        error_message=str(e),
                        request_id=request_id,
                        metadata=request.metadata,
                    )
                except Exception as audit_error:
                    # Don't break execution if audit logging fails
                    logger.error(f"[{request_id}] Audit logging failed: {audit_error}")

            # Re-raise for fallback handler
            raise

        finally:
            # Always clear request context (Epic 5 - Story 5.4)
            clear_request_context()

    async def _call_single_provider(
        self,
        provider_name: str,
        messages: List[dict],
        request_id: str,
        agent_id: str,
        task_complexity: str = 'simple',  # For smart fallback
    ) -> Tuple[str, int, int, str, str]:
        provider = self.providers.get(provider_name)

        if not provider:
            provider_name = next(iter(self.providers))
            provider = self.providers[provider_name]
            logger.warning(
                "Configured provider not found, falling back to %s",
                provider_name,
            )

        set_request_context(request_id, agent_id, provider_name)
        llm_response = await self._invoke_provider(
            provider_name, provider, messages, task_complexity
        )

        if isinstance(llm_response, LLMResponse):
            return (
                llm_response.content,
                llm_response.tokens_input,
                llm_response.tokens_output,
                llm_response.provider,
                llm_response.model,
            )

        if isinstance(llm_response, dict):
            # This should not happen with real providers, but handle gracefully
            content = llm_response.get("content", "Error: Invalid response format")
            tokens_in = llm_response.get("tokens_input", len(str(messages)) // 4)
            tokens_out = llm_response.get("tokens_output", len(content) // 4)
            return (content, tokens_in, tokens_out, provider_name, "unknown")

        raise TypeError(f"Unexpected provider response type: {type(llm_response)}")

    async def _invoke_provider(
        self,
        provider_name: str,
        provider,
        messages: List[dict],
        task_complexity: str = 'simple'
    ):
        # Determine task_type for OpenRouter smart fallback
        task_type = self._complexity_to_task_type(task_complexity)

        # Build kwargs for provider.call()
        call_kwargs = {'messages': messages}

        # Add task_type for OpenRouter (enables smart model selection)
        if 'openrouter' in provider_name.lower():
            call_kwargs['task_type'] = task_type
            call_kwargs['enable_fallback'] = True

        if self.global_semaphore and self.rate_limiter:
            async with self.global_semaphore.acquire():
                async with self.rate_limiter.acquire(provider_name):
                    return await provider.call(**call_kwargs)

        if self.global_semaphore:
            async with self.global_semaphore.acquire():
                return await provider.call(**call_kwargs)

        if self.rate_limiter:
            async with self.rate_limiter.acquire(provider_name):
                return await provider.call(**call_kwargs)

        logger.warning("Calling provider %s without rate limiting", provider_name)
        return await provider.call(**call_kwargs)

    async def _execute_prompt_plan(
        self,
        plan: PromptPlan,
        request_id: str,
    ) -> Tuple[str, int, int, str, str]:
        results: Dict[str, object] = {}
        remaining: List[SpecialistTask] = list(plan.tasks)

        while remaining:
            progress = False
            for task in list(remaining):
                if not set(task.inputs).issubset(results.keys()):
                    continue

                messages = self._build_task_messages(task, results)
                provider = self.providers.get(task.provider)
                if not provider:
                    raise ProcessComplianceError(
                        f"Provider '{task.provider}' referenced by task '{task.id}' is unavailable"
                    )

                response = await self._invoke_provider(task.provider, provider, messages)
                results[task.id] = response
                remaining.remove(task)
                progress = True

            if not progress:
                raise ProcessComplianceError(
                    "Cannot resolve task dependencies; check DAG ordering"
                )

        tokens_in = 0
        tokens_out = 0
        last_provider = "plan"
        last_model = "plan"
        specialist_outputs: List[str] = []

        for task in plan.tasks:
            entry = results[task.id]
            (
                content,
                task_tokens_in,
                task_tokens_out,
                task_provider,
                task_model,
            ) = self._extract_task_result(entry, task)

            specialist_outputs.append(
                f"Task {task.id} ({task.provider}) => {content}"
            )
            tokens_in += task_tokens_in
            tokens_out += task_tokens_out
            last_provider = task_provider
            last_model = task_model

        synthesized = await self._synthesize_plan_response(plan, specialist_outputs)
        if synthesized:
            response_content = synthesized
        else:
            response_content = "\n\n".join(specialist_outputs)
        return response_content, tokens_in, tokens_out, last_provider, last_model

    def _build_task_messages(
        self,
        task: SpecialistTask,
        results: Dict[str, object],
    ) -> List[dict]:
        user_prompt = [task.task_prompt]
        for dep in task.inputs:
            entry = results.get(dep)
            if isinstance(entry, LLMResponse):
                user_prompt.append(f"Context from {dep}: {entry.content}")
            elif isinstance(entry, dict):
                user_prompt.append(
                    f"Context from {dep}: {entry.get('content', 'Error: Invalid context')}"
                )

        return [
            {"role": "system", "content": task.expertise_context},
            {"role": "user", "content": "\n\n".join(user_prompt)},
        ]

    def _extract_task_result(
        self,
        entry: object,
        task: SpecialistTask,
    ) -> Tuple[str, int, int, str, str]:
        if isinstance(entry, LLMResponse):
            return (
                entry.content,
                entry.tokens_input,
                entry.tokens_output,
                entry.provider,
                entry.model,
            )

        if isinstance(entry, dict):
            content = entry.get("content", "Stub response")
            tokens_in = entry.get("tokens_input", len(content) // 4)
            tokens_out = entry.get("tokens_output", len(content) // 4)
            return content, tokens_in, tokens_out, task.provider, "stub"

        raise TypeError(
            f"Unexpected task result type for {task.id}: {type(entry)}"
        )

    async def _synthesize_plan_response(
        self,
        plan: PromptPlan,
        specialist_outputs: Sequence[str],
    ) -> Optional[str]:
        if not specialist_outputs:
            return None

        if not self.prompt_optimizer or not self.prompt_optimizer.enabled:
            return None

        try:
            return await self.prompt_optimizer.synthesize(plan, specialist_outputs)
        except NotImplementedError:
            logger.info(
                "Prompt optimizer synthesis not implemented; falling back to concatenation"
            )
        except Exception:
            logger.exception(
                "Prompt optimizer synthesis failed; falling back to concatenation"
            )
        return None

    def _determine_complexity(
        self,
        request: AgentExecutionRequest,
        agent_id: str
    ) -> str:
        """
        Determine task complexity for cost optimization

        Args:
            request: Agent execution request
            agent_id: Agent ID

        Returns:
            Complexity level: 'simple', 'code', 'medium', 'complex', or 'critical'
        """
        # Priority 1: Use explicit complexity from request if provided
        if hasattr(request, 'complexity') and request.complexity:
            return request.complexity

        # Priority 2: Infer from agent type
        agent_complexity_map = {
            'analyst': 'simple',
            'dev': 'code',
            'architect': 'complex',
            'reviewer': 'medium',
            'qa': 'simple',
            'pm': 'simple',
        }

        if agent_id in agent_complexity_map:
            return agent_complexity_map[agent_id]

        # Priority 3: Infer from task content
        task_lower = request.task.lower()

        # Code-related keywords
        if any(keyword in task_lower for keyword in [
            'code', 'function', 'class', 'implement', 'bug', 'debug',
            'refactor', 'python', 'javascript', 'typescript', 'api'
        ]):
            return 'code'

        # Complex/reasoning keywords
        if any(keyword in task_lower for keyword in [
            'architecture', 'design', 'system', 'database', 'security',
            'performance', 'scalability', 'review', 'analyze deeply'
        ]):
            return 'complex'

        # Critical keywords
        if any(keyword in task_lower for keyword in [
            'critical', 'production', 'emergency', 'urgent', 'security breach'
        ]):
            return 'critical'

        # Medium complexity
        if any(keyword in task_lower for keyword in [
            'explain', 'how to', 'why', 'compare', 'recommend'
        ]):
            return 'medium'

        # Default to simple
        return 'simple'

    def _complexity_to_task_type(self, complexity: str) -> str:
        """
        Convert complexity level to OpenRouter task_type

        Args:
            complexity: Task complexity ('simple', 'code', 'medium', 'complex', 'critical')

        Returns:
            Task type for OpenRouter: 'code', 'reasoning', or 'general'
        """
        mapping = {
            'code': 'code',
            'complex': 'reasoning',
            'critical': 'reasoning',
            'medium': 'general',
            'simple': 'general',
        }
        return mapping.get(complexity, 'general')


