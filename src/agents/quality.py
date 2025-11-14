"""
Response Quality Validator

Validates LLM responses and triggers auto-escalation to better providers
if quality is insufficient.
"""

import logging
from typing import Optional, List
from enum import Enum

from ..models.provider import LLMResponse


logger = logging.getLogger(__name__)


class ProviderTier(str, Enum):
    """Provider quality tier classification"""
    WORKER = "worker"      # Fast, lower quality (Cerebras, small models)
    BOSS = "boss"          # Slower, higher quality (Groq 70B, Gemini Pro)
    ULTIMATE = "ultimate"  # Best quality, expensive (GPT-4, Claude 3)


class QualityIssue(str, Enum):
    """Types of quality issues"""
    TOO_SHORT = "too_short"
    ERROR_MARKER = "error_marker"
    LOW_CONFIDENCE = "low_confidence"
    INCOMPLETE = "incomplete"
    CORRUPTED = "corrupted"


class QualityValidationResult:
    """Result of quality validation"""
    
    def __init__(
        self,
        is_valid: bool,
        quality_score: float,
        issues: List[QualityIssue],
        should_escalate: bool,
        reason: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.quality_score = quality_score
        self.issues = issues
        self.should_escalate = should_escalate
        self.reason = reason


class QualityValidator:
    """
    Validates LLM response quality
    
    Features:
    - Length validation (not too short/empty)
    - Error marker detection (failure indicators)
    - Confidence level parsing
    - Format validation (not corrupted)
    - Tier-specific quality thresholds
    - Auto-escalation recommendations
    
    Usage:
        validator = QualityValidator()
        result = validator.validate(response, tier=ProviderTier.WORKER)
        if result.should_escalate:
            # Retry with boss-tier provider
            response = await fallback_executor.execute_with_tier(ProviderTier.BOSS)
    """
    
    # Error markers that indicate low quality
    ERROR_MARKERS = [
        "I cannot",
        "I don't know",
        "I'm unable to",
        "Unable to",
        "I apologize, but",
        "[ERROR]",
        "Failed to",
        "I don't have enough information",
        "I'm not sure",
        "I can't help with"
    ]
    
    # Low confidence markers
    LOW_CONFIDENCE_MARKERS = [
        "maybe",
        "perhaps",
        "I think",
        "I believe",
        "possibly",
        "might be",
        "could be",
        "uncertain"
    ]
    
    def __init__(
        self,
        min_length_worker: int = 50,
        min_length_boss: int = 200,
        min_quality_score: float = 0.6
    ):
        """
        Initialize quality validator
        
        Args:
            min_length_worker: Minimum response length for worker tier
            min_length_boss: Minimum response length for boss tier
            min_quality_score: Minimum acceptable quality score (0-1)
        """
        self.min_length_worker = min_length_worker
        self.min_length_boss = min_length_boss
        self.min_quality_score = min_quality_score
        
        logger.info(
            f"Quality validator initialized: "
            f"worker_min={min_length_worker}, "
            f"boss_min={min_length_boss}"
        )
    
    def validate(
        self,
        response: LLMResponse,
        tier: ProviderTier = ProviderTier.WORKER,
        task_complexity: Optional[str] = None
    ) -> QualityValidationResult:
        """
        Validate response quality
        
        Args:
            response: LLM response to validate
            tier: Provider tier that generated the response
            task_complexity: Optional task complexity indicator
            
        Returns:
            QualityValidationResult with validation details
        """
        issues = []
        quality_score = 1.0
        
        content = response.content
        
        # 1. Length validation (tier-specific)
        min_length = (
            self.min_length_boss if tier == ProviderTier.BOSS
            else self.min_length_worker
        )
        
        if len(content) < min_length:
            issues.append(QualityIssue.TOO_SHORT)
            quality_score -= 0.3
            logger.debug(
                f"Quality issue: Response too short ({len(content)} < {min_length})"
            )
        
        # 2. Error marker detection
        error_found = False
        for marker in self.ERROR_MARKERS:
            if marker.lower() in content.lower():
                issues.append(QualityIssue.ERROR_MARKER)
                quality_score -= 0.4
                error_found = True
                logger.debug(f"Quality issue: Error marker found '{marker}'")
                break
        
        # 3. Low confidence detection
        confidence_count = sum(
            1 for marker in self.LOW_CONFIDENCE_MARKERS
            if marker.lower() in content.lower()
        )
        
        if confidence_count >= 3:
            issues.append(QualityIssue.LOW_CONFIDENCE)
            quality_score -= 0.2
            logger.debug(
                f"Quality issue: Low confidence ({confidence_count} markers)"
            )
        
        # 4. Incompleteness check
        if content.endswith("...") or len(content) > 0 and content[-1] not in ".!?":
            # Response might be truncated
            if response.finish_reason == "length":
                issues.append(QualityIssue.INCOMPLETE)
                quality_score -= 0.1
                logger.debug("Quality issue: Response incomplete (truncated)")
        
        # 5. Corruption check (basic)
        if content.count("{") != content.count("}"):
            issues.append(QualityIssue.CORRUPTED)
            quality_score -= 0.3
            logger.debug("Quality issue: Unbalanced braces (possibly corrupted)")
        
        # Calculate final quality score
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Determine if should escalate
        should_escalate = (
            quality_score < self.min_quality_score
            or error_found
            or (tier == ProviderTier.WORKER and len(issues) >= 2)
        )
        
        is_valid = quality_score >= self.min_quality_score
        
        reason = None
        if should_escalate:
            reason = f"Quality score {quality_score:.2f} below threshold, issues: {[i.value for i in issues]}"
        
        logger.info(
            f"Quality validation: "
            f"score={quality_score:.2f}, "
            f"valid={is_valid}, "
            f"escalate={should_escalate}, "
            f"issues={len(issues)}"
        )
        
        return QualityValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            should_escalate=should_escalate,
            reason=reason
        )
    
    def get_escalation_tier(self, current_tier: ProviderTier) -> Optional[ProviderTier]:
        """
        Get next tier for escalation
        
        Args:
            current_tier: Current provider tier
            
        Returns:
            Next tier to escalate to, or None if already at highest
        """
        if current_tier == ProviderTier.WORKER:
            return ProviderTier.BOSS
        elif current_tier == ProviderTier.BOSS:
            return ProviderTier.ULTIMATE
        else:
            # Already at highest tier
            return None

