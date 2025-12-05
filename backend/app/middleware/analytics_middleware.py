"""
Analytics Middleware and Decorators

Provides middleware and decorators for capturing detailed interaction data.
Ensures all six required data points are captured with minimal performance impact.
"""
import time
import uuid
import json
from functools import wraps
from typing import Callable, Any, Dict, Optional, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..services.analytics_service import analytics_service
from ..models.analytics import InteractionLog, EndpointType, PerformanceMetric
from ..models.pedagogical_state import PedagogicalState
from ..core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to capture basic request metrics and setup analytics context"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Generate interaction ID for request tracking
        interaction_id = str(uuid.uuid4())
        request.state.interaction_id = interaction_id
        request.state.start_time = start_time

        # Process request
        response = await call_next(request)

        # Log basic metrics for chat endpoints
        response_time_ms = int((time.time() - start_time) * 1000)

        if "/api/chat" in request.url.path and settings.analytics_enabled:
            await analytics_service.log_metric(PerformanceMetric(
                interaction_id=interaction_id,
                metric_type="total_latency",
                metric_value=response_time_ms,
                metric_unit="ms"
            ))

            # Log response size as additional metric
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                await analytics_service.log_metric(PerformanceMetric(
                    interaction_id=interaction_id,
                    metric_type="response_size",
                    metric_value=int(response.headers['content-length']),
                    metric_unit="bytes"
                ))

        return response


def log_interaction(endpoint_type: EndpointType):
    """
    Decorator to log detailed interaction data for chat endpoints

    Automatically captures all required data points:
    1. User's initial query
    2. AI's response
    3. The specific prompt sent to the SLM (extracted from service layer)
    4. The learner's pedagogical state at the time of the query
    5. Source materials used for the response
    6. User rating (via separate feedback endpoint)

    Args:
        endpoint_type: Type of chat endpoint (simple, agentic, pedagogical)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not settings.analytics_enabled:
                # If analytics disabled, just call the function
                return await func(*args, **kwargs)

            start_time = time.time()
            interaction_id = str(uuid.uuid4())

            # Extract request data
            request = None
            for arg in args:
                if hasattr(arg, 'json') or hasattr(arg, 'query_params'):
                    request = arg
                    break

            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')

            # Extract basic interaction data
            conversation_id = "unknown"
            user_query = ""
            user_github_id = None
            session_id = None

            try:
                if request:
                    # Try to get request body
                    if hasattr(request, 'json'):
                        try:
                            body = await request.json()
                            conversation_id = body.get('conversation_id', 'unknown')
                            user_query = body.get('message', '')
                        except Exception:
                            # If JSON parsing fails, try form data
                            try:
                                form_data = await request.form()
                                conversation_id = form_data.get('conversation_id', 'unknown')
                                user_query = form_data.get('message', '')
                            except Exception:
                                pass
                    elif hasattr(request, 'query_params'):
                        # For GET requests
                        conversation_id = request.query_params.get('conversation_id', 'unknown')
                        user_query = request.query_params.get('message', '')

                    # Get user info from session/state
                    if hasattr(request.state, 'user') and request.state.user:
                        user_github_id = getattr(request.state.user, 'github_id', None)
                    if hasattr(request.state, 'session_id'):
                        session_id = request.state.session_id

            except Exception as e:
                logger.warning(f"Failed to extract request data for analytics: {e}")

            # Execute the function
            try:
                result = await func(*args, **kwargs)

                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)

                # Extract response and metadata based on endpoint type
                ai_response = ""
                slm_prompt = None
                pedagogical_state = None
                source_materials = None
                workflow_path = None
                was_rewritten = False
                rewrites_count = 0
                token_count = None
                retrieval_count = None

                try:
                    # Extract based on endpoint type and response structure
                    if hasattr(result, 'dict'):
                        result_dict = result.dict()
                    elif hasattr(result, '__dict__'):
                        result_dict = result.__dict__
                    elif isinstance(result, dict):
                        result_dict = result
                    else:
                        # Try to convert to dictionary
                        try:
                            result_dict = dict(result)
                        except Exception:
                            result_dict = {}

                    # Common fields
                    ai_response = result_dict.get('answer', '') or result_dict.get('response', '')

                    # Endpoint-specific extraction
                    if endpoint_type == EndpointType.AGENTIC:
                        source_materials = result_dict.get('sources', [])
                        workflow_path = result_dict.get('workflow_path', '')
                        was_rewritten = result_dict.get('was_rewritten', False)
                        rewrites_count = result_dict.get('rewrites_used', 0)

                        # Try to get SLM prompt from agentic service if available
                        if 'slm_prompt' in result_dict:
                            slm_prompt = result_dict['slm_prompt']

                    elif endpoint_type == EndpointType.PEDAGOGICAL:
                        # Get pedagogical state from state manager
                        try:
                            from ..services.state_manager import state_manager
                            state = state_manager.get_state(conversation_id)
                            if state:
                                pedagogical_state = {
                                    'current_phase': state.current_phase.value,
                                    'phase_history': state.phase_history,
                                    'problem_statement': state.problem_statement,
                                    'last_user_message': state.last_user_message
                                }
                        except Exception as e:
                            logger.warning(f"Failed to get pedagogical state: {e}")

                    elif endpoint_type == EndpointType.SIMPLE:
                        source_materials = result_dict.get('sources', [])

                    # Extract additional metadata
                    token_count = result_dict.get('token_count')
                    retrieval_count = len(source_materials) if source_materials else result_dict.get('retrieval_count')

                except Exception as e:
                    logger.warning(f"Failed to extract response data for analytics: {e}")

                # Create and log interaction
                try:
                    interaction = InteractionLog(
                        interaction_id=interaction_id,
                        conversation_id=conversation_id,
                        session_id=session_id,
                        user_github_id=user_github_id,
                        user_query=user_query if settings.log_raw_queries else "[REDACTED]",
                        ai_response=ai_response if settings.log_ai_responses else "[REDACTED]",
                        slm_prompt=slm_prompt if (slm_prompt and settings.log_prompts) else None,
                        pedagogical_state=pedagogical_state,
                        source_materials=source_materials,
                        endpoint_type=endpoint_type,
                        workflow_path=workflow_path,
                        response_time_ms=response_time_ms,
                        token_count=token_count,
                        retrieval_count=retrieval_count,
                        was_rewritten=was_rewritten,
                        rewrites_count=rewrites_count
                    )

                    await analytics_service.log_interaction(interaction)

                    # Add interaction ID to response for feedback tracking
                    if hasattr(result, 'dict'):
                        result_dict = result.dict()
                        result_dict['interaction_id'] = interaction_id
                        # Try to update the result object
                        try:
                            for key, value in result_dict.items():
                                if hasattr(result, key):
                                    setattr(result, key, value)
                        except Exception:
                            pass
                    elif isinstance(result, dict):
                        result['interaction_id'] = interaction_id

                except Exception as e:
                    logger.error(f"Failed to log interaction: {e}")

                return result

            except Exception as e:
                # Log error but don't break the main function
                logger.error(f"Analytics logging failed: {e}")
                raise

        return wrapper
    return decorator


async def log_websocket_interaction(
    conversation_id: str,
    user_message: str,
    ai_response: str,
    interaction_id: str = None,
    source_materials: List[Dict] = None,
    workflow_events: List[str] = None,
    endpoint_type: EndpointType = EndpointType.AGENTIC,
    slm_prompt: str = None
):
    """
    Log WebSocket interaction data for streaming endpoints

    Args:
        conversation_id: Conversation identifier
        user_message: User's message
        ai_response: AI's response
        interaction_id: Unique interaction identifier
        source_materials: List of source documents used
        workflow_events: List of workflow events/stages
        endpoint_type: Type of endpoint
        slm_prompt: Prompt sent to SLM
    """
    if not settings.analytics_enabled:
        return

    if not interaction_id:
        interaction_id = str(uuid.uuid4())

    try:
        # Create pedagogical state if available
        pedagogical_state = None
        if endpoint_type == EndpointType.PEDAGOGICAL:
            try:
                from ..services.state_manager import state_manager
                state = state_manager.get_state(conversation_id)
                if state:
                    pedagogical_state = {
                        'current_phase': state.current_phase.value,
                        'phase_history': state.phase_history,
                        'problem_statement': state.problem_statement,
                        'last_user_message': state.last_user_message
                    }
            except Exception as e:
                logger.warning(f"Failed to get pedagogical state for WebSocket: {e}")

        # Create workflow path from events
        workflow_path = " → ".join(workflow_events) if workflow_events else None

        interaction = InteractionLog(
            interaction_id=interaction_id,
            conversation_id=conversation_id,
            user_query=user_message if settings.log_raw_queries else "[REDACTED]",
            ai_response=ai_response if settings.log_ai_responses else "[REDACTED]",
            slm_prompt=slm_prompt if (slm_prompt and settings.log_prompts) else None,
            pedagogical_state=pedagogical_state,
            source_materials=source_materials,
            endpoint_type=endpoint_type,
            workflow_path=workflow_path,
            retrieval_count=len(source_materials) if source_materials else 0,
            was_rewritten=bool(workflow_events and "rewrite" in str(workflow_events).lower()),
            rewrites_count=sum(1 for event in workflow_events or [] if "rewrite" in str(event).lower())
        )

        await analytics_service.log_interaction(interaction)

    except Exception as e:
        logger.error(f"Failed to log WebSocket interaction: {e}")


def extract_prompt_from_service(service_result: Any) -> Optional[str]:
    """
    Extract SLM prompt from service result for agentic endpoints

    Args:
        service_result: Result from RAG service containing potential prompt

    Returns:
        Extracted prompt or None
    """
    try:
        if hasattr(service_result, 'dict'):
            result_dict = service_result.dict()
        elif hasattr(service_result, '__dict__'):
            result_dict = service_result.__dict__
        elif isinstance(service_result, dict):
            result_dict = service_result
        else:
            return None

        # Look for prompt in various possible fields
        prompt_fields = ['slm_prompt', 'prompt', 'generation_prompt', 'llm_prompt']

        for field in prompt_fields:
            if field in result_dict and result_dict[field]:
                return result_dict[field]

        return None

    except Exception as e:
        logger.warning(f"Failed to extract prompt from service result: {e}")
        return None


class AnalyticsContext:
    """Context manager for analytics operations"""

    def __init__(self, interaction_id: str = None):
        self.interaction_id = interaction_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.metrics = []

    async def log_metric(self, metric_type: str, value: float, unit: str = "ms"):
        """Log a performance metric"""
        metric = PerformanceMetric(
            interaction_id=self.interaction_id,
            metric_type=metric_type,
            metric_value=value,
            metric_unit=unit
        )
        self.metrics.append(metric)
        await analytics_service.log_metric(metric)

    async def finish(self):
        """Log completion time and flush metrics"""
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        await self.log_metric("total_time", elapsed_ms, "ms")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.finish()