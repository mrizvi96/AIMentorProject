"""
Analytics Service

Provides async logging service for interaction analytics.
Captures all required data points with non-blocking background processing.
"""
import sqlite3
import json
import asyncio
import aiosqlite
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from ..models.analytics import InteractionLog, UserFeedback, PerformanceMetric, AnalyticsDashboard, EndpointType
from ..core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Async analytics service with background queue processing

    Features:
    - Non-blocking interaction logging
    - Background database writes via queue
    - Automatic table creation and indexing
    - Data retention and cleanup
    - Privacy compliance
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or getattr(settings, 'analytics_db_path', 'analytics.db')
        self._queue = asyncio.Queue()
        self._worker_task = None
        self._initialized = False

    async def initialize(self):
        """Initialize database and start background worker"""
        if self._initialized:
            return

        try:
            await self._create_tables()
            self._worker_task = asyncio.create_task(self._background_writer())
            self._initialized = True
            logger.info(f"✓ Analytics service initialized with database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")
            raise

    async def _create_tables(self):
        """Create database tables with proper indexes"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")

            # Create interactions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id TEXT UNIQUE NOT NULL,
                    conversation_id TEXT NOT NULL,
                    session_id TEXT,
                    user_github_id INTEGER,

                    -- Core requirements
                    user_query TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    slm_prompt TEXT,
                    pedagogical_state TEXT,
                    source_materials TEXT,

                    -- Metadata
                    endpoint_type TEXT NOT NULL,
                    workflow_path TEXT,
                    response_time_ms INTEGER,
                    token_count INTEGER,
                    retrieval_count INTEGER,
                    was_rewritten BOOLEAN DEFAULT FALSE,
                    rewrites_count INTEGER DEFAULT 0,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create user_feedback table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    feedback_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id) ON DELETE CASCADE
                )
            """)

            # Create performance_metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_conversation_id ON interactions(conversation_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_endpoint_type ON interactions(endpoint_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_interaction_id ON interactions(interaction_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_feedback_interaction_id ON user_feedback(interaction_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_interaction_id ON performance_metrics(interaction_id)")

            await db.commit()
            logger.info("✓ Database tables and indexes created")

    async def log_interaction(self, interaction: InteractionLog):
        """Queue interaction for logging (non-blocking)"""
        if not self._initialized:
            logger.warning("Analytics service not initialized, dropping interaction log")
            return

        try:
            await self._queue.put(("interaction", interaction))
        except Exception as e:
            logger.error(f"Failed to queue interaction log: {e}")

    async def log_feedback(self, feedback: UserFeedback):
        """Queue feedback for logging"""
        if not self._initialized:
            logger.warning("Analytics service not initialized, dropping feedback log")
            return

        try:
            await self._queue.put(("feedback", feedback))
        except Exception as e:
            logger.error(f"Failed to queue feedback log: {e}")

    async def log_metric(self, metric: PerformanceMetric):
        """Queue performance metric for logging"""
        if not self._initialized:
            logger.warning("Analytics service not initialized, dropping metric log")
            return

        try:
            await self._queue.put(("metric", metric))
        except Exception as e:
            logger.error(f"Failed to queue metric log: {e}")

    async def _background_writer(self):
        """Background worker to write to database"""
        logger.info("Analytics background writer started")

        while True:
            try:
                # Process items in batches for efficiency
                batch = []
                try:
                    # Wait for first item
                    item_type, data = await self._queue.get()
                    batch.append((item_type, data))
                    self._queue.task_done()

                    # Try to get more items quickly (batch processing)
                    for _ in range(49):  # Process up to 50 items per batch
                        try:
                            item_type, data = self._queue.get_nowait()
                            batch.append((item_type, data))
                            self._queue.task_done()
                        except asyncio.QueueEmpty:
                            break

                except Exception as e:
                    logger.error(f"Error getting items from queue: {e}")
                    continue

                # Process batch
                if batch:
                    await self._write_batch(batch)

            except Exception as e:
                logger.error(f"Analytics worker error: {e}")
                await asyncio.sleep(1)  # Brief pause on error

    async def _write_batch(self, batch: List[tuple]):
        """Write a batch of items to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")

                # Group by type for efficient batch inserts
                interactions = []
                feedbacks = []
                metrics = []

                for item_type, data in batch:
                    if item_type == "interaction":
                        interactions.append(data)
                    elif item_type == "feedback":
                        feedbacks.append(data)
                    elif item_type == "metric":
                        metrics.append(data)

                # Batch insert interactions
                if interactions:
                    await db.executemany("""
                        INSERT OR REPLACE INTO interactions
                        (interaction_id, conversation_id, session_id, user_github_id,
                         user_query, ai_response, slm_prompt, pedagogical_state,
                         source_materials, endpoint_type, workflow_path, response_time_ms,
                         token_count, retrieval_count, was_rewritten, rewrites_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        (
                            interaction.interaction_id, interaction.conversation_id,
                            interaction.session_id, interaction.user_github_id,
                            interaction.user_query, interaction.ai_response,
                            interaction.slm_prompt,
                            json.dumps(interaction.pedagogical_state) if interaction.pedagogical_state else None,
                            json.dumps(interaction.source_materials) if interaction.source_materials else None,
                            interaction.endpoint_type.value, interaction.workflow_path,
                            interaction.response_time_ms, interaction.token_count,
                            interaction.retrieval_count, interaction.was_rewritten,
                            interaction.rewrites_count
                        ) for interaction in interactions
                    ])

                # Batch insert feedbacks
                if feedbacks:
                    await db.executemany("""
                        INSERT INTO user_feedback (interaction_id, rating, feedback_text)
                        VALUES (?, ?, ?)
                    """, [
                        (feedback.interaction_id, feedback.rating, feedback.feedback_text)
                        for feedback in feedbacks
                    ])

                # Batch insert metrics
                if metrics:
                    await db.executemany("""
                        INSERT INTO performance_metrics (interaction_id, metric_type, metric_value, metric_unit)
                        VALUES (?, ?, ?, ?)
                    """, [
                        (metric.interaction_id, metric.metric_type, metric.metric_value, metric.metric_unit)
                        for metric in metrics
                    ])

                await db.commit()

        except Exception as e:
            logger.error(f"Batch write failed: {e}")

    async def get_analytics(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          conversation_id: Optional[str] = None,
                          limit: int = 100) -> Dict[str, Any]:
        """Retrieve analytics data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Build query conditions
                conditions = []
                params = []

                if start_date:
                    conditions.append("created_at >= ?")
                    params.append(start_date.isoformat())

                if end_date:
                    conditions.append("created_at <= ?")
                    params.append(end_date.isoformat())

                if conversation_id:
                    conditions.append("conversation_id = ?")
                    params.append(conversation_id)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # Get summary statistics
                stats_query = f"""
                    SELECT
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT conversation_id) as total_conversations,
                        COUNT(DISTINCT user_github_id) as total_users,
                        AVG(CAST(response_time_ms AS REAL)) as avg_response_time,
                        endpoint_type
                    FROM interactions
                    WHERE {where_clause}
                    GROUP BY endpoint_type
                """

                cursor = await db.execute(stats_query, params)
                stats_rows = await cursor.fetchall()

                # Get recent interactions
                recent_query = f"""
                    SELECT * FROM interactions
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params.append(limit)
                cursor = await db.execute(recent_query, params)
                recent_rows = await cursor.fetchall()

                # Convert to response format
                total_interactions = sum(row[0] for row in stats_rows)
                total_users = max(row[3] for row in stats_rows) if stats_rows else 0
                endpoint_usage = {row[4]: row[0] for row in stats_rows}
                avg_response_time = sum(
                    (row[3] or 0) * row[0] for row in stats_rows
                ) / total_interactions if total_interactions > 0 else 0

                # Get average rating
                rating_query = f"""
                    SELECT AVG(CAST(rating AS REAL)) as avg_rating
                    FROM user_feedback uf
                    JOIN interactions i ON uf.interaction_id = i.interaction_id
                    WHERE {where_clause}
                """
                cursor = await db.execute(rating_query, params[:-1])  # Remove limit param
                rating_row = await cursor.fetchone()
                avg_rating = rating_row[0] if rating_row and rating_row[0] else None

                return {
                    "total_interactions": total_interactions,
                    "total_users": total_users,
                    "average_rating": avg_rating,
                    "average_response_time_ms": avg_response_time,
                    "endpoint_usage": endpoint_usage,
                    "recent_interactions_count": len(recent_rows),
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                }

        except Exception as e:
            logger.error(f"Failed to retrieve analytics: {e}")
            return {"error": str(e)}

    async def get_interaction_by_id(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific interaction by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get interaction
                cursor = await db.execute(
                    "SELECT * FROM interactions WHERE interaction_id = ?",
                    (interaction_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                # Convert to dict
                columns = [desc[0] for desc in cursor.description]
                interaction = dict(zip(columns, row))

                # Parse JSON fields
                if interaction['pedagogical_state']:
                    interaction['pedagogical_state'] = json.loads(interaction['pedagogical_state'])
                if interaction['source_materials']:
                    interaction['source_materials'] = json.loads(interaction['source_materials'])

                # Get feedback
                cursor = await db.execute(
                    "SELECT rating, feedback_text, created_at FROM user_feedback WHERE interaction_id = ?",
                    (interaction_id,)
                )
                feedback_row = await cursor.fetchone()
                if feedback_row:
                    interaction['feedback'] = {
                        'rating': feedback_row[0],
                        'feedback_text': feedback_row[1],
                        'created_at': feedback_row[2]
                    }

                return interaction

        except Exception as e:
            logger.error(f"Failed to get interaction {interaction_id}: {e}")
            return None

    async def cleanup_old_data(self, days_to_keep: int = None):
        """Clean up old analytics data for privacy compliance"""
        if not days_to_keep:
            days_to_keep = getattr(settings, 'analytics_retention_days', 90)

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Delete old interactions (cascade will delete feedback and metrics)
                await db.execute(
                    "DELETE FROM interactions WHERE created_at < ?",
                    (cutoff_date.isoformat(),)
                )

                # Get count of deleted records
                changes = db.total_changes

                await db.commit()
                logger.info(f"Cleaned up {changes} old analytics records older than {cutoff_date}")

                # Vacuum database to reclaim space
                await db.execute("VACUUM")
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

    async def shutdown(self):
        """Shutdown the analytics service"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Analytics service shutdown complete")


# Global instance
analytics_service = AnalyticsService()