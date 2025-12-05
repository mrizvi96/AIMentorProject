"""
Analytics Data Models

Pydantic models for analytics data validation and serialization.
Captures all required data points for interaction logging.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class EndpointType(str, Enum):
    """Types of chat endpoints"""
    SIMPLE = "simple"
    AGENTIC = "agentic"
    PEDAGOGICAL = "pedagogical"


class InteractionLog(BaseModel):
    """
    Comprehensive interaction log for analytics

    Captures all six required data points:
    1. User's initial query
    2. AI's response
    3. The specific prompt sent to the SLM
    4. The learner's pedagogical state at the time of the query
    5. Source materials used for the response
    6. A user-provided rating of the response's usefulness (via feedback table)
    """
    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    session_id: Optional[str] = None
    user_github_id: Optional[int] = None

    # Core requirements (1-5)
    user_query: str = Field(..., min_length=1, max_length=5000)
    ai_response: str = Field(..., min_length=1, max_length=10000)
    slm_prompt: Optional[str] = Field(None, max_length=20000)
    pedagogical_state: Optional[Dict[str, Any]] = None
    source_materials: Optional[List[Dict[str, Any]]] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)

    # Metadata for enhanced analytics
    endpoint_type: EndpointType
    workflow_path: Optional[str] = None
    response_time_ms: Optional[int] = Field(None, ge=0)
    token_count: Optional[int] = Field(None, ge=0)
    retrieval_count: Optional[int] = Field(None, ge=0)
    was_rewritten: bool = False
    rewrites_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserFeedback(BaseModel):
    """
    User feedback for an interaction
    Captures rating #6 from requirements
    """
    interaction_id: str
    rating: int = Field(..., ge=1, le=5, description="User rating from 1 (poor) to 5 (excellent)")
    feedback_text: Optional[str] = Field(None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceMetric(BaseModel):
    """
    Performance metrics for detailed analytics
    """
    interaction_id: str
    metric_type: str = Field(..., description="Type of metric: latency, retrieval_time, generation_time, etc.")
    metric_value: float = Field(..., description="Numerical value of the metric")
    metric_unit: str = Field(..., description="Unit of measurement: ms, tokens, count, etc.")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsDashboard(BaseModel):
    """
    Analytics dashboard response model
    """
    total_interactions: int
    total_users: int
    average_rating: Optional[float] = None
    average_response_time_ms: Optional[float] = None
    endpoint_usage: Dict[str, int]
    phase_distribution: Dict[str, int]
    recent_interactions: List[InteractionLog]
    top_rated_interactions: List[InteractionLog]
    needs_improvement: List[InteractionLog]


class AnalyticsSummary(BaseModel):
    """
    Summary statistics for analytics
    """
    date: str
    endpoint_type: EndpointType
    total_interactions: int
    avg_rating: Optional[float] = None
    avg_response_time_ms: Optional[float] = None
    unique_users: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Response model extensions for including interaction_id
class ChatResponseWithAnalytics:
    """Mixin to add interaction_id to existing response models"""

    def add_interaction_id(self, interaction_id: str):
        """Add interaction_id to response if not already present"""
        if hasattr(self, 'dict'):
            response_dict = self.dict()
            response_dict['interaction_id'] = interaction_id
            # Update the object with interaction_id
            if hasattr(self, '__dict__'):
                self.__dict__['interaction_id'] = interaction_id
        return interaction_id