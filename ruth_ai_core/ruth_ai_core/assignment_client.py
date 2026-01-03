"""
Phase 8.2 – Ruth AI Core Subscription Reconciliation

ASSIGNMENT CLIENT

This module provides read-only access to backend camera-to-model assignment APIs.
It fetches assignment INTENT from the backend (Phase 8.1 APIs).

CRITICAL CONSTRAINTS:
- Read-only access to backend APIs
- Best-effort fetching (failures are acceptable)
- No retries, no backoff
- No caching (always fetch fresh)
- Never blocks reconciliation on failure
"""

import aiohttp
from typing import List, Dict, Any, Optional
from loguru import logger


class AssignmentClient:
    """
    Client for fetching camera-to-model assignment intent from backend APIs.

    Phase 8.2: This client provides read-only access to Phase 8.1 assignment APIs.
    It does NOT modify backend state.

    FAILURE SEMANTICS:
    - Network failure → return empty list (fail-safe)
    - API error → return empty list (fail-safe)
    - Invalid response → return empty list (fail-safe)
    - No retries, no blocking
    """

    def __init__(self, backend_url: str, timeout_seconds: float = 5.0):
        """
        Initialize assignment client.

        Args:
            backend_url: Base URL of backend API (e.g., "http://localhost:8080")
            timeout_seconds: Request timeout in seconds (default: 5.0)
        """
        self.backend_url = backend_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def fetch_all_assignments(self) -> List[Dict[str, Any]]:
        """
        Fetch all camera-to-model assignments from backend.

        Calls: GET /api/v1/ai-model-assignments?enabled=true

        Returns:
            List of assignment dictionaries, each containing:
            - id: Assignment UUID (str)
            - camera_id: Camera UUID (str)
            - model_id: Model identifier (str)
            - enabled: Whether assignment is enabled (bool)
            - desired_fps: Desired FPS (int or None)
            - priority: Priority hint (int or None)
            - parameters: Model-specific config (dict or None)

        On failure:
            Returns empty list (fail-safe)

        CRITICAL: This MUST NOT raise exceptions.
        All errors must be caught and logged.
        """
        try:
            url = f"{self.backend_url}/api/v1/ai-model-assignments"
            params = {"enabled": "true", "limit": 1000}  # Only fetch enabled assignments

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Backend API returned non-200 status: {response.status} "
                            f"(Phase 8.2 assignment fetch)"
                        )
                        return []

                    data = await response.json()

                    # Extract assignments list from response
                    # Phase 8.1 API returns: {"assignments": [...], "total": N, ...}
                    assignments = data.get("assignments", [])

                    if not isinstance(assignments, list):
                        logger.warning(
                            "Backend API returned invalid assignments format "
                            "(expected list, Phase 8.2)"
                        )
                        return []

                    logger.info(
                        f"Fetched {len(assignments)} assignments from backend "
                        f"(Phase 8.2)"
                    )

                    return assignments

        except aiohttp.ClientError as e:
            # Network error, connection refused, timeout, etc.
            logger.warning(
                f"Failed to fetch assignments from backend (network error, Phase 8.2): {e}"
            )
            return []

        except Exception as e:
            # Unexpected error (JSON parsing, etc.)
            logger.error(
                f"Unexpected error fetching assignments from backend (Phase 8.2): {e}"
            )
            return []

    async def fetch_assignments_for_camera(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Fetch assignments for a specific camera.

        Calls: GET /api/v1/ai-model-assignments?camera_id={camera_id}&enabled=true

        Args:
            camera_id: Camera UUID string

        Returns:
            List of assignment dictionaries for this camera

        On failure:
            Returns empty list (fail-safe)

        CRITICAL: This MUST NOT raise exceptions.
        All errors must be caught and logged.
        """
        try:
            url = f"{self.backend_url}/api/v1/ai-model-assignments"
            params = {"camera_id": camera_id, "enabled": "true", "limit": 100}

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Backend API returned non-200 status for camera {camera_id}: "
                            f"{response.status} (Phase 8.2)"
                        )
                        return []

                    data = await response.json()
                    assignments = data.get("assignments", [])

                    if not isinstance(assignments, list):
                        logger.warning(
                            f"Invalid assignments format for camera {camera_id} (Phase 8.2)"
                        )
                        return []

                    return assignments

        except aiohttp.ClientError as e:
            logger.warning(
                f"Failed to fetch assignments for camera {camera_id} "
                f"(network error, Phase 8.2): {e}"
            )
            return []

        except Exception as e:
            logger.error(
                f"Unexpected error fetching assignments for camera {camera_id} "
                f"(Phase 8.2): {e}"
            )
            return []
