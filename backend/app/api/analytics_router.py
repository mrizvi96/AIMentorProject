"""
Analytics API Router

Provides endpoints for user feedback submission and analytics data retrieval.
Completes the 6th required data point: user-provided ratings.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from ..services.analytics_service import analytics_service
from ..models.analytics import UserFeedback, AnalyticsDashboard, InteractionLog
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class FeedbackRequest(BaseModel):
    """Request model for user feedback submission"""
    interaction_id: str = Field(..., description="Unique identifier for the interaction being rated")
    rating: int = Field(..., ge=1, le=5, description="User rating from 1 (poor) to 5 (excellent)")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Optional detailed feedback")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "interaction_id": "123e4567-e89b-12d3-a456-426614174000",
                    "rating": 5,
                    "feedback_text": "Very helpful explanation! The step-by-step approach was perfect."
                }
            ]
        }
    }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    status: str = Field(..., description="Submission status")
    message: str = Field(..., description="Response message")
    interaction_id: str = Field(..., description="The interaction ID that was rated")


class AnalyticsQuery(BaseModel):
    """Query parameters for analytics requests"""
    start_date: Optional[datetime] = Field(None, description="Start date for analytics period")
    end_date: Optional[datetime] = Field(None, description="End date for analytics period")
    conversation_id: Optional[str] = Field(None, description="Filter by specific conversation")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results to return")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback for an interaction

    Completes the 6th required data point from UNIMPLEMENTED_FEATURES.md:
    "A user-provided rating of the response's usefulness"

    Args:
        feedback: Feedback data including rating (1-5) and optional comment

    Returns:
        Confirmation of successful feedback submission

    Raises:
        400: Invalid rating or interaction_id
        500: Server error during submission
    """
    if not settings.analytics_enabled:
        raise HTTPException(status_code=403, detail="Analytics features are disabled")

    try:
        # Validate feedback data
        if feedback.rating < 1 or feedback.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        if not feedback.interaction_id:
            raise HTTPException(status_code=400, detail="Interaction ID is required")

        # Create feedback object
        user_feedback = UserFeedback(
            interaction_id=feedback.interaction_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text
        )

        # Log feedback via analytics service
        await analytics_service.log_feedback(user_feedback)

        logger.info(f"User feedback submitted: interaction_id={feedback.interaction_id}, rating={feedback.rating}")

        return FeedbackResponse(
            status="success",
            message="Feedback recorded successfully. Thank you for your input!",
            interaction_id=feedback.interaction_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/dashboard")
async def get_analytics_dashboard(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    limit: int = Query(50, ge=1, le=200, description="Maximum recent interactions to show")
):
    """
    Get analytics dashboard data

    Returns comprehensive analytics including:
    - Total interactions and users
    - Average ratings and response times
    - Endpoint usage statistics
    - Recent high-rated and low-rated interactions
    - Pedagogical phase distribution

    Args:
        start_date: Filter interactions from this date
        end_date: Filter interactions until this date
        limit: Maximum number of recent interactions to return

    Returns:
        Analytics dashboard data

    Raises:
        403: Analytics disabled
        500: Server error during retrieval
    """
    if not settings.analytics_enabled:
        raise HTTPException(status_code=403, detail="Analytics features are disabled")

    try:
        # Get basic analytics
        analytics_data = await analytics_service.get_analytics(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        if "error" in analytics_data:
            raise HTTPException(status_code=500, detail=analytics_data["error"])

        # Add additional analytics data
        dashboard_data = {
            **analytics_data,
            "analytics_enabled": True,
            "data_period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "privacy_settings": {
                "anonymize_user_data": settings.anonymize_user_data,
                "log_raw_queries": settings.log_raw_queries,
                "log_ai_responses": settings.log_ai_responses
            }
        }

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics data")


@router.get("/interaction/{interaction_id}")
async def get_interaction_details(interaction_id: str):
    """
    Get detailed information about a specific interaction

    Returns all captured data points for the interaction:
    - User query and AI response
    - SLM prompt (if available)
    - Pedagogical state (if applicable)
    - Source materials used
    - User feedback (if provided)
    - Performance metrics

    Args:
        interaction_id: Unique identifier for the interaction

    Returns:
        Complete interaction data

    Raises:
        404: Interaction not found
        403: Analytics disabled
        500: Server error during retrieval
    """
    if not settings.analytics_enabled:
        raise HTTPException(status_code=403, detail="Analytics features are disabled")

    try:
        # Get interaction details
        interaction = await analytics_service.get_interaction_by_id(interaction_id)

        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")

        # Apply privacy filters if needed
        if settings.anonymize_user_data and interaction.get('user_github_id'):
            interaction['user_github_id'] = None

        if not settings.log_raw_queries and interaction.get('user_query'):
            interaction['user_query'] = "[REDACTED FOR PRIVACY]"

        if not settings.log_ai_responses and interaction.get('ai_response'):
            interaction['ai_response'] = "[REDACTED FOR PRIVACY]"

        if not settings.log_prompts and interaction.get('slm_prompt'):
            interaction['slm_prompt'] = "[REDACTED FOR PRIVACY]"

        return interaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interaction {interaction_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interaction")


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize")
):
    """
    Get analytics summary for the specified time period

    Returns aggregated statistics and trends:
    - Daily interaction counts
    - Rating trends over time
    - Endpoint usage patterns
    - Performance metrics summary

    Args:
        days: Number of days to include in the summary

    Returns:
        Aggregated analytics summary

    Raises:
        403: Analytics disabled
        500: Server error during retrieval
    """
    if not settings.analytics_enabled:
        raise HTTPException(status_code=403, detail="Analytics features are disabled")

    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get analytics for the period
        analytics_data = await analytics_service.get_analytics(
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Get comprehensive data
        )

        if "error" in analytics_data:
            raise HTTPException(status_code=500, detail=analytics_data["error"])

        # Add summary metadata
        summary = {
            **analytics_data,
            "summary_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics summary")


@router.delete("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(90, ge=1, le=365, description="Days of data to retain")
):
    """
    Clean up old analytics data (admin only)

    Removes interactions and associated data older than the specified
    number of days to comply with privacy regulations and manage storage.

    Args:
        days_to_keep: Number of days of recent data to retain

    Returns:
        Cleanup confirmation and statistics

    Raises:
        403: Analytics disabled or insufficient permissions
        500: Server error during cleanup
    """
    if not settings.analytics_enabled:
        raise HTTPException(status_code=403, detail="Analytics features are disabled")

    # TODO: Add admin authentication check here
    # For now, we'll allow the endpoint but in production this should be restricted

    try:
        # Perform cleanup
        await analytics_service.cleanup_old_data(days_to_keep)

        logger.info(f"Analytics cleanup completed: keeping {days_to_keep} days of data")

        return {
            "status": "success",
            "message": f"Analytics cleanup completed successfully",
            "days_retained": days_to_keep,
            "cleanup_date": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old analytics data")


@router.get("/status")
async def get_analytics_status():
    """
    Get current analytics system status

    Returns information about:
    - Analytics enabled/disabled status
    - Privacy settings
    - Data retention configuration
    - Service health status

    Returns:
        Analytics system status information
    """
    try:
        return {
            "analytics_enabled": settings.analytics_enabled,
            "privacy_settings": {
                "anonymize_user_data": settings.anonymize_user_data,
                "log_raw_queries": settings.log_raw_queries,
                "log_ai_responses": settings.log_ai_responses,
                "log_prompts": settings.log_prompts,
                "require_consent": settings.require_consent_for_analytics
            },
            "retention_settings": {
                "days_to_keep": settings.analytics_retention_days,
                "batch_size": settings.analytics_batch_size,
                "max_queue_size": settings.analytics_max_queue_size
            },
            "database_path": settings.analytics_db_path,
            "status": "healthy" if analytics_service._initialized else "disabled"
        }

    except Exception as e:
        logger.error(f"Failed to get analytics status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics status")