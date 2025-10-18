"""Approval Gates for Workflow Control

This module implements approval gates for controlling workflow progression
based on rules, thresholds, and human review requirements.
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GateType(str, Enum):
    """Types of approval gates."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    CONDITIONAL = "conditional"


class GateStatus(str, Enum):
    """Status of a gate evaluation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass
class GateResult:
    """Result of a gate evaluation."""
    gate_id: str
    status: GateStatus
    reason: str
    evaluated_at: datetime
    evaluated_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ApprovalGate:
    """Base class for approval gates."""
    
    def __init__(self, gate_id: str, gate_type: GateType, description: str = ""):
        self.gate_id = gate_id
        self.gate_type = gate_type
        self.description = description
        self.history: List[GateResult] = []
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate the gate with given context.
        
        Args:
            context: Dictionary containing data needed for evaluation
            
        Returns:
            GateResult object with evaluation outcome
        """
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    def get_history(self) -> List[GateResult]:
        """Get evaluation history for this gate."""
        return self.history.copy()


class ScoreThresholdGate(ApprovalGate):
    """Gate that checks if score meets threshold."""
    
    def __init__(self, gate_id: str, threshold: float, description: str = ""):
        super().__init__(gate_id, GateType.AUTOMATIC, description)
        self.threshold = threshold
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate if score meets threshold."""
        score = context.get("score")
        
        if score is None:
            result = GateResult(
                gate_id=self.gate_id,
                status=GateStatus.REJECTED,
                reason="Score not available",
                evaluated_at=datetime.now(),
                evaluated_by="system"
            )
        elif score >= self.threshold:
            result = GateResult(
                gate_id=self.gate_id,
                status=GateStatus.APPROVED,
                reason=f"Score {score} meets threshold {self.threshold}",
                evaluated_at=datetime.now(),
                evaluated_by="system"
            )
        else:
            result = GateResult(
                gate_id=self.gate_id,
                status=GateStatus.REJECTED,
                reason=f"Score {score} below threshold {self.threshold}",
                evaluated_at=datetime.now(),
                evaluated_by="system"
            )
        
        self.history.append(result)
        logger.info(f"Gate {self.gate_id}: {result.status} - {result.reason}")
        return result


class ManualReviewGate(ApprovalGate):
    """Gate that requires manual human review."""
    
    def __init__(self, gate_id: str, reviewers: List[str], description: str = ""):
        super().__init__(gate_id, GateType.MANUAL, description)
        self.reviewers = reviewers
        self.pending_reviews: Dict[str, GateResult] = {}
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Mark as pending manual review."""
        result = GateResult(
            gate_id=self.gate_id,
            status=GateStatus.PENDING,
            reason="Awaiting manual review",
            evaluated_at=datetime.now(),
            metadata={
                "reviewers": self.reviewers,
                "context": context
            }
        )
        
        self.pending_reviews[context.get("flow_id", "unknown")] = result
        self.history.append(result)
        logger.info(f"Gate {self.gate_id}: Pending manual review by {self.reviewers}")
        return result
    
    def submit_review(
        self,
        flow_id: str,
        reviewer: str,
        approved: bool,
        comments: str = ""
    ) -> GateResult:
        """Submit a manual review decision.
        
        Args:
            flow_id: Flow identifier
            reviewer: Name/ID of reviewer
            approved: Whether to approve or reject
            comments: Optional review comments
            
        Returns:
            GateResult with final decision
        """
        if reviewer not in self.reviewers:
            raise ValueError(f"Reviewer {reviewer} not authorized")
        
        if flow_id not in self.pending_reviews:
            raise ValueError(f"No pending review for flow {flow_id}")
        
        status = GateStatus.APPROVED if approved else GateStatus.REJECTED
        result = GateResult(
            gate_id=self.gate_id,
            status=status,
            reason=comments or ("Approved by reviewer" if approved else "Rejected by reviewer"),
            evaluated_at=datetime.now(),
            evaluated_by=reviewer
        )
        
        del self.pending_reviews[flow_id]
        self.history.append(result)
        logger.info(f"Gate {self.gate_id}: {status} by {reviewer}")
        return result


class ConditionalGate(ApprovalGate):
    """Gate with custom conditional logic."""
    
    def __init__(
        self,
        gate_id: str,
        condition_func: Callable[[Dict[str, Any]], bool],
        description: str = ""
    ):
        super().__init__(gate_id, GateType.CONDITIONAL, description)
        self.condition_func = condition_func
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate custom condition."""
        try:
            passed = self.condition_func(context)
            
            result = GateResult(
                gate_id=self.gate_id,
                status=GateStatus.APPROVED if passed else GateStatus.REJECTED,
                reason=f"Condition {'passed' if passed else 'failed'}",
                evaluated_at=datetime.now(),
                evaluated_by="system"
            )
        except Exception as e:
            logger.error(f"Gate {self.gate_id} condition evaluation failed: {e}")
            result = GateResult(
                gate_id=self.gate_id,
                status=GateStatus.REJECTED,
                reason=f"Condition evaluation error: {e}",
                evaluated_at=datetime.now(),
                evaluated_by="system"
            )
        
        self.history.append(result)
        logger.info(f"Gate {self.gate_id}: {result.status}")
        return result


class GateChain:
    """Chain multiple gates together with AND/OR logic."""
    
    def __init__(self, chain_id: str, gates: List[ApprovalGate], require_all: bool = True):
        """
        Initialize gate chain.
        
        Args:
            chain_id: Unique identifier for this chain
            gates: List of gates to evaluate
            require_all: If True, all gates must pass (AND). If False, any gate can pass (OR)
        """
        self.chain_id = chain_id
        self.gates = gates
        self.require_all = require_all
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all gates in the chain.
        
        Args:
            context: Context for evaluation
            
        Returns:
            Dictionary with overall result and individual gate results
        """
        results = []
        
        for gate in self.gates:
            result = gate.evaluate(context)
            results.append(result)
            
            # Short-circuit for AND logic if any gate fails
            if self.require_all and result.status != GateStatus.APPROVED:
                break
            
            # Short-circuit for OR logic if any gate passes
            if not self.require_all and result.status == GateStatus.APPROVED:
                break
        
        # Determine overall status
        if self.require_all:
            # All must be approved
            overall_approved = all(r.status == GateStatus.APPROVED for r in results)
        else:
            # Any can be approved
            overall_approved = any(r.status == GateStatus.APPROVED for r in results)
        
        # Check for pending reviews
        has_pending = any(r.status == GateStatus.PENDING for r in results)
        
        return {
            "chain_id": self.chain_id,
            "approved": overall_approved,
            "pending": has_pending,
            "gate_results": results,
            "logic": "AND" if self.require_all else "OR"
        }
    
    def get_pending_gates(self) -> List[ApprovalGate]:
        """Get gates with pending reviews."""
        pending = []
        for gate in self.gates:
            if isinstance(gate, ManualReviewGate) and gate.pending_reviews:
                pending.append(gate)
        return pending


class GateManager:
    """Manage multiple gate chains and their lifecycle."""
    
    def __init__(self):
        self.chains: Dict[str, GateChain] = {}
        self.gates: Dict[str, ApprovalGate] = {}
    
    def register_gate(self, gate: ApprovalGate):
        """Register a gate for reuse."""
        self.gates[gate.gate_id] = gate
        logger.info(f"Registered gate: {gate.gate_id}")
    
    def register_chain(self, chain: GateChain):
        """Register a gate chain."""
        self.chains[chain.chain_id] = chain
        logger.info(f"Registered gate chain: {chain.chain_id}")
    
    def evaluate_chain(self, chain_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a registered gate chain."""
        if chain_id not in self.chains:
            raise ValueError(f"Chain {chain_id} not found")
        
        return self.chains[chain_id].evaluate(context)
    
    def get_gate(self, gate_id: str) -> Optional[ApprovalGate]:
        """Get a registered gate."""
        return self.gates.get(gate_id)
    
    def get_chain(self, chain_id: str) -> Optional[GateChain]:
        """Get a registered chain."""
        return self.chains.get(chain_id)


def create_default_gates() -> GateManager:
    """Create default gate configuration."""
    manager = GateManager()
    
    # Score threshold gate
    score_gate = ScoreThresholdGate(
        gate_id="score_threshold",
        threshold=0.7,
        description="Ensure candidate score is above 0.7"
    )
    manager.register_gate(score_gate)
    
    # Manual review gate
    review_gate = ManualReviewGate(
        gate_id="hiring_manager_review",
        reviewers=["hiring_manager", "team_lead"],
        description="Require hiring manager approval"
    )
    manager.register_gate(review_gate)
    
    # Custom conditional gate
    experience_gate = ConditionalGate(
        gate_id="experience_check",
        condition_func=lambda ctx: ctx.get("years_experience", 0) >= 3,
        description="Check minimum 3 years experience"
    )
    manager.register_gate(experience_gate)
    
    # Create default chain
    default_chain = GateChain(
        chain_id="standard_approval",
        gates=[score_gate, experience_gate],
        require_all=True
    )
    manager.register_chain(default_chain)
    
    return manager


if __name__ == "__main__":
    # Example usage
    manager = create_default_gates()
    
    # Test context
    context = {
        "flow_id": "test-001",
        "score": 0.85,
        "years_experience": 5
    }
    
    result = manager.evaluate_chain("standard_approval", context)
    print(f"Chain evaluation: {result}")
