"""
Phase 7 – Observability & Operational Controls

AI HEALTH SERVICE

This module provides read-only health and metrics aggregation for the AI subsystem.

PHASE 7 SCOPE:
- Read model container heartbeats from filesystem
- Aggregate per-camera metrics (when StreamAgents integrated)
- Determine health status based on heartbeat freshness
- Expose metrics via read-only APIs

WHAT THIS IS:
- Read-only metrics collector
- Health status aggregator
- Best-effort observability service
- Fail-safe and non-blocking

WHAT THIS IS NOT:
- Health monitoring system (no alerts, no actions)
- Auto-remediation logic
- Configuration manager
- StreamAgent orchestrator

CRITICAL CONSTRAINTS:
- MUST be read-only
- MUST NOT affect AI inference or video pipelines
- MUST fail silently on errors
- MUST NOT retry or block
- MUST accept stale or missing metrics
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas.ai_health import (
    AISystemHealth,
    CameraMetrics,
    ModelContainerHealth,
    ModelContainerMetrics,
    SubscriptionMetrics,
)


class AIHealthService:
    """
    Phase 7: AI system health and metrics aggregation service.

    This service provides read-only visibility into AI subsystem health
    by aggregating metrics from:
    1. Model container heartbeat files (/tmp/vas_heartbeat_{model_id}.json)
    2. StreamAgent metrics (when integrated with VAS backend)

    CRITICAL: This service is BEST-EFFORT and READ-ONLY.
    - All operations must be non-blocking
    - All errors must be silently handled
    - Missing metrics are acceptable
    - Stale data is acceptable
    """

    # Heartbeat staleness threshold (seconds)
    # If heartbeat older than this, container is considered degraded
    HEARTBEAT_STALE_THRESHOLD_SECONDS = 30

    def __init__(self, heartbeat_dir: str = "/tmp"):
        """
        Initialize AI health service.

        Args:
            heartbeat_dir: Directory where model container heartbeats are written
                          (default: /tmp)
        """
        self.heartbeat_dir = Path(heartbeat_dir)

    def get_system_health(self) -> AISystemHealth:
        """
        Phase 7: Get overall AI system health.

        Aggregates health from all cameras and model containers.

        Returns:
            AISystemHealth: System-wide health status and metrics

        CRITICAL: This is best-effort. Missing or stale metrics are acceptable.
        All errors are silently handled.
        """
        try:
            # Get model container health
            models = self._get_all_model_health()

            # Get camera metrics (placeholder - integration pending)
            cameras = self._get_all_camera_metrics()

            # Determine overall system status
            system_status = self._determine_system_status(models)

            return AISystemHealth(
                status=system_status,
                timestamp=datetime.utcnow().isoformat() + "Z",
                camera_count=len(cameras),
                model_count=len(models),
                cameras=cameras,
                models=models
            )
        except Exception:
            # Phase 7: Silent failure - return degraded status on error
            return AISystemHealth(
                status="unknown",
                timestamp=datetime.utcnow().isoformat() + "Z",
                camera_count=0,
                model_count=0,
                cameras=[],
                models=[]
            )

    def get_model_health(self, model_id: str) -> Optional[ModelContainerHealth]:
        """
        Phase 7: Get health status for a specific model container.

        Args:
            model_id: Model identifier

        Returns:
            ModelContainerHealth if heartbeat exists, None otherwise

        CRITICAL: This is best-effort. Missing heartbeat returns None.
        All errors are silently handled.
        """
        try:
            return self._read_model_heartbeat(model_id)
        except Exception:
            # Phase 7: Silent failure - return None on error
            return None

    def get_camera_metrics(self, camera_id: str) -> Optional[CameraMetrics]:
        """
        Phase 7: Get metrics for a specific camera.

        Args:
            camera_id: Camera identifier

        Returns:
            CameraMetrics if available, None otherwise

        NOTE: This is a placeholder for future StreamAgent integration.
        Currently returns None until StreamAgents are integrated with VAS backend.

        CRITICAL: This is best-effort. Missing metrics return None.
        All errors are silently handled.
        """
        try:
            # TODO: Integrate with StreamAgent registry when available
            # For now, return None (no StreamAgent integration yet)
            return None
        except Exception:
            # Phase 7: Silent failure
            return None

    def _get_all_model_health(self) -> List[ModelContainerHealth]:
        """
        Phase 7: Get health status for all model containers.

        Scans heartbeat directory for all heartbeat files.

        Returns:
            List of ModelContainerHealth (may be empty)

        CRITICAL: This is best-effort. Scan errors are silently handled.
        """
        models = []
        try:
            # Scan for heartbeat files matching pattern: vas_heartbeat_*.json
            heartbeat_files = self.heartbeat_dir.glob("vas_heartbeat_*.json")

            for heartbeat_file in heartbeat_files:
                try:
                    # Extract model_id from filename
                    # Format: vas_heartbeat_{model_id}.json
                    model_id = heartbeat_file.stem.replace("vas_heartbeat_", "")

                    # Read heartbeat
                    model_health = self._read_model_heartbeat(model_id)
                    if model_health is not None:
                        models.append(model_health)
                except Exception:
                    # Phase 7: Silent failure for individual heartbeat read
                    continue

            return models
        except Exception:
            # Phase 7: Silent failure - return empty list on scan error
            return []

    def _get_all_camera_metrics(self) -> List[CameraMetrics]:
        """
        Phase 7: Get metrics for all cameras.

        NOTE: This is a placeholder for future StreamAgent integration.
        Currently returns empty list until StreamAgents are integrated.

        Returns:
            List of CameraMetrics (empty until integration)

        CRITICAL: This is best-effort.
        """
        try:
            # TODO: Integrate with StreamAgent registry when available
            # For now, return empty list (no StreamAgent integration yet)
            return []
        except Exception:
            # Phase 7: Silent failure
            return []

    def _read_model_heartbeat(self, model_id: str) -> Optional[ModelContainerHealth]:
        """
        Phase 7: Read model container heartbeat from filesystem.

        Args:
            model_id: Model identifier

        Returns:
            ModelContainerHealth if heartbeat exists and is valid, None otherwise

        CRITICAL: This is best-effort. Read errors return None.
        """
        try:
            heartbeat_path = self.heartbeat_dir / f"vas_heartbeat_{model_id}.json"

            # Check if heartbeat file exists
            if not heartbeat_path.exists():
                return None

            # Read heartbeat JSON
            with heartbeat_path.open("r") as f:
                heartbeat = json.load(f)

            # Extract metrics
            metrics_data = heartbeat.get("metrics", {})
            metrics = ModelContainerMetrics(
                total_requests=metrics_data.get("total_requests", 0),
                total_errors=metrics_data.get("total_errors", 0),
                avg_latency_ms=metrics_data.get("avg_latency_ms", 0.0),
                uptime_seconds=metrics_data.get("uptime_seconds", 0)
            )

            # Get timestamp and determine staleness
            heartbeat_timestamp_str = heartbeat.get("timestamp")
            status = self._determine_model_status(heartbeat_timestamp_str)

            return ModelContainerHealth(
                model_id=model_id,
                status=status,
                last_heartbeat=heartbeat_timestamp_str,
                metrics=metrics
            )

        except Exception:
            # Phase 7: Silent failure - return None on any error
            return None

    def _determine_model_status(self, heartbeat_timestamp_str: Optional[str]) -> str:
        """
        Phase 7: Determine model container health status based on heartbeat freshness.

        Args:
            heartbeat_timestamp_str: ISO timestamp string from heartbeat

        Returns:
            Status string: "healthy", "degraded", or "unknown"

        CRITICAL: This is best-effort. Parse errors return "unknown".
        """
        try:
            if heartbeat_timestamp_str is None:
                return "unknown"

            # Parse timestamp (remove trailing 'Z' if present)
            timestamp_str = heartbeat_timestamp_str.rstrip('Z')
            heartbeat_time = datetime.fromisoformat(timestamp_str)

            # Calculate age
            now = datetime.utcnow()
            age_seconds = (now - heartbeat_time).total_seconds()

            # Determine status based on staleness
            if age_seconds < self.HEARTBEAT_STALE_THRESHOLD_SECONDS:
                return "healthy"
            else:
                return "degraded"

        except Exception:
            # Phase 7: Silent failure - return unknown on parse error
            return "unknown"

    def _determine_system_status(self, models: List[ModelContainerHealth]) -> str:
        """
        Phase 7: Determine overall system health status.

        Args:
            models: List of model container health statuses

        Returns:
            Status string: "healthy", "degraded", or "unknown"

        Logic:
        - If no models: "unknown"
        - If any model degraded/unknown: "degraded"
        - If all models healthy: "healthy"

        CRITICAL: This is best-effort.
        """
        try:
            if not models:
                return "unknown"

            # Check if all models are healthy
            all_healthy = all(m.status == "healthy" for m in models)
            if all_healthy:
                return "healthy"
            else:
                return "degraded"

        except Exception:
            # Phase 7: Silent failure
            return "unknown"
