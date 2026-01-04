"""
Phase 4.2.3 – Model Onboarding & Discovery

MODEL DISCOVERY SYSTEM

This module handles filesystem-based model discovery.

CRITICAL RULES:
- Discovery happens ONCE at startup
- Scan fixed directory: /opt/ruth-ai/models/
- Each subdirectory = one model
- model.yaml MUST exist
- Invalid models → UNAVAILABLE (no retries)

WHAT THIS IS:
- Startup-time model discovery
- Filesystem scanning
- model.yaml validation
- Availability determination

WHAT THIS IS NOT:
- Hot-reload or dynamic discovery
- Health monitoring
- Model registry service
- Runtime configuration updates
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .model_config import ModelConfig


class ModelDiscovery:
    """
    Filesystem-based model discovery.

    DISCOVERY SEMANTICS:
    - Scan directory ONCE at startup
    - Each subdirectory represents ONE model
    - model.yaml MUST exist
    - Invalid models marked UNAVAILABLE

    NO runtime discovery occurs.
    """

    # Fixed discovery path (LOCKED)
    DEFAULT_MODELS_DIR = "/opt/ruth-ai/models"

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize model discovery.

        Args:
            models_dir: Directory to scan (default: /opt/ruth-ai/models)
        """
        self.models_dir = models_dir or self.DEFAULT_MODELS_DIR
        self._discovered_models: Dict[str, ModelConfig] = {}
        self._unavailable_models: Dict[str, str] = {}  # model_id -> reason

    def discover_models(self) -> Dict[str, ModelConfig]:
        """
        Discover all models in models directory.

        This is called ONCE at container startup.

        Returns:
            Dict mapping model_id to ModelConfig for AVAILABLE models

        DISCOVERY ALGORITHM:
        1. Check if models_dir exists
        2. For each subdirectory:
           a. Look for model.yaml
           b. Parse and validate
           c. Check model weights exist
           d. Mark AVAILABLE or UNAVAILABLE
        3. Return AVAILABLE models only

        FAILURE HANDLING:
        - Missing models_dir → empty dict (no models available)
        - Missing model.yaml → model UNAVAILABLE
        - Invalid model.yaml → model UNAVAILABLE
        - Missing weights → model UNAVAILABLE
        - No exceptions raised (fail silently)
        """
        print(f"Discovering models in: {self.models_dir}")

        # Check if models directory exists
        if not os.path.exists(self.models_dir):
            print(f"WARNING: Models directory does not exist: {self.models_dir}")
            print(f"         No models will be available.")
            return {}

        if not os.path.isdir(self.models_dir):
            print(f"ERROR: Models path is not a directory: {self.models_dir}")
            return {}

        # Scan subdirectories
        try:
            entries = os.listdir(self.models_dir)
        except PermissionError:
            print(f"ERROR: Permission denied reading models directory: {self.models_dir}")
            return {}
        except Exception as e:
            print(f"ERROR: Failed to list models directory: {e}")
            return {}

        # Discover each model
        for entry in sorted(entries):
            model_dir = os.path.join(self.models_dir, entry)

            # Skip if not a directory
            if not os.path.isdir(model_dir):
                continue

            # Look for model.yaml
            yaml_path = os.path.join(model_dir, "model.yaml")

            if not os.path.exists(yaml_path):
                print(f"WARNING: model.yaml not found in {model_dir}")
                print(f"         Model '{entry}' marked UNAVAILABLE")
                self._unavailable_models[entry] = "missing_model_yaml"
                continue

            # Parse model.yaml
            model_config = ModelConfig.from_yaml_file(yaml_path, model_dir)

            if model_config is None:
                print(f"WARNING: Invalid model.yaml in {model_dir}")
                print(f"         Model '{entry}' marked UNAVAILABLE")
                self._unavailable_models[entry] = "invalid_model_yaml"
                continue

            # Model is AVAILABLE
            print(f"✓ Discovered model: {model_config.model_id} ({model_config.model_name} v{model_config.model_version})")
            print(f"  Path: {model_config.model_path}")
            print(f"  Type: {model_config.model_type}")
            print(f"  GPU required: {model_config.gpu_required}")
            print(f"  CPU fallback: {model_config.cpu_fallback_allowed}")

            self._discovered_models[model_config.model_id] = model_config

        # Summary
        available_count = len(self._discovered_models)
        unavailable_count = len(self._unavailable_models)
        print(f"\nModel discovery complete:")
        print(f"  Available: {available_count}")
        print(f"  Unavailable: {unavailable_count}")

        return self._discovered_models

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """
        Get model configuration by ID.

        Args:
            model_id: Model identifier

        Returns:
            ModelConfig if available, None if unavailable or not found
        """
        return self._discovered_models.get(model_id)

    def list_available_models(self) -> List[str]:
        """
        List IDs of all available models.

        Returns:
            List of model IDs
        """
        return list(self._discovered_models.keys())

    def is_available(self, model_id: str) -> bool:
        """
        Check if model is available.

        Args:
            model_id: Model identifier

        Returns:
            True if available, False otherwise
        """
        return model_id in self._discovered_models

    def get_unavailable_reason(self, model_id: str) -> Optional[str]:
        """
        Get reason why model is unavailable.

        Args:
            model_id: Model identifier

        Returns:
            Reason string if unavailable, None if available or not found
        """
        return self._unavailable_models.get(model_id)


# EXAMPLE USAGE:
#
# # At container startup
# discovery = ModelDiscovery()
# available_models = discovery.discover_models()
#
# # Check if model available
# if discovery.is_available("yolov8n"):
#     model_config = discovery.get_model("yolov8n")
#     print(f"Model path: {model_config.model_path}")
#     print(f"GPU required: {model_config.gpu_required}")
#
#     # Create runtime config
#     runtime_config = model_config.to_runtime_config()
#
#     # Initialize handler (Phase 4.2.1/4.2.2)
#     handler = InferenceHandler(
#         model_id=model_config.model_id,
#         model_config=runtime_config
#     )
# else:
#     reason = discovery.get_unavailable_reason("yolov8n")
#     print(f"Model unavailable: {reason}")
