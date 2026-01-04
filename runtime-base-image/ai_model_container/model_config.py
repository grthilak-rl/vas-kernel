"""
Phase 4.2.3 – Model Onboarding & Discovery

MODEL CONFIGURATION PARSER

This module handles model.yaml parsing and validation.

CRITICAL RULES:
- model.yaml is the SINGLE SOURCE OF TRUTH
- Discovery happens ONCE at startup
- Invalid config → model UNAVAILABLE (no retries)
- GPU requirements strictly enforced
- No runtime discovery or hot-reload

WHAT THIS IS:
- model.yaml parser and validator
- Model metadata container
- GPU requirement enforcement

WHAT THIS IS NOT:
- Model registry (just validation)
- Health monitoring
- Runtime configuration updates
- Model version management
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # Will fail gracefully if not available


@dataclass
class ModelConfig:
    """
    Parsed and validated model configuration from model.yaml.

    This represents the SINGLE SOURCE OF TRUTH for a model's:
    - Identity (model_id, name, version)
    - Requirements (GPU, input format, resolution)
    - Capabilities (supported tasks, output schema)

    IMMUTABLE after parsing.
    """

    # Identity
    model_id: str
    model_name: str
    model_version: str

    # Capabilities
    supported_tasks: List[str]  # e.g., ["object_detection", "tracking"]

    # Input requirements
    input_format: str  # e.g., "NV12", "RGB24"
    expected_resolution: List[int]  # [width, height], e.g., [640, 640]

    # Resource requirements
    gpu_required: bool  # If True, MUST have GPU (no CPU fallback)
    gpu_memory_mb: Optional[int]  # Minimum GPU memory required
    cpu_fallback_allowed: bool  # If True, can run on CPU when GPU unavailable

    # Runtime configuration
    model_type: str  # "pytorch" or "onnx"
    model_path: str  # Absolute path to weights file
    confidence_threshold: float  # Default confidence threshold
    nms_iou_threshold: Optional[float]  # NMS IOU threshold (if applicable)

    # Output schema
    output_schema: Dict[str, Any]  # Describes detection output format

    # Optional metadata
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None

    @classmethod
    def from_yaml_file(cls, yaml_path: str, model_dir: str) -> Optional['ModelConfig']:
        """
        Parse and validate model.yaml file.

        Args:
            yaml_path: Path to model.yaml
            model_dir: Directory containing the model

        Returns:
            ModelConfig if valid, None if invalid

        FAILURE SEMANTICS:
        - Missing file → None
        - Invalid YAML → None
        - Missing required fields → None
        - Invalid field types → None
        - No exceptions raised (fail silently)
        """
        if yaml is None:
            print(f"ERROR: PyYAML not available. Install with: pip install pyyaml")
            return None

        try:
            # Read YAML file
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                print(f"ERROR: model.yaml is not a valid YAML dict: {yaml_path}")
                return None

            # Extract required fields
            model_id = data.get('model_id')
            if not model_id or not isinstance(model_id, str):
                print(f"ERROR: model_id missing or invalid in {yaml_path}")
                return None

            model_name = data.get('model_name')
            if not model_name or not isinstance(model_name, str):
                print(f"ERROR: model_name missing or invalid in {yaml_path}")
                return None

            model_version = data.get('model_version')
            if not model_version or not isinstance(model_version, str):
                print(f"ERROR: model_version missing or invalid in {yaml_path}")
                return None

            supported_tasks = data.get('supported_tasks', [])
            if not isinstance(supported_tasks, list):
                print(f"ERROR: supported_tasks must be a list in {yaml_path}")
                return None

            input_format = data.get('input_format', 'NV12')
            if not isinstance(input_format, str):
                print(f"ERROR: input_format must be a string in {yaml_path}")
                return None

            expected_resolution = data.get('expected_resolution', [640, 640])
            if not isinstance(expected_resolution, list) or len(expected_resolution) != 2:
                print(f"ERROR: expected_resolution must be [width, height] in {yaml_path}")
                return None

            # Extract resource requirements
            resource_reqs = data.get('resource_requirements', {})
            if not isinstance(resource_reqs, dict):
                print(f"ERROR: resource_requirements must be a dict in {yaml_path}")
                return None

            gpu_required = resource_reqs.get('gpu_required', False)
            gpu_memory_mb = resource_reqs.get('gpu_memory_mb')
            cpu_fallback_allowed = resource_reqs.get('cpu_fallback_allowed', True)

            # Validate GPU requirements logic
            if gpu_required and cpu_fallback_allowed:
                print(f"ERROR: gpu_required=true and cpu_fallback_allowed=true is contradictory in {yaml_path}")
                return None

            # Extract runtime configuration
            model_type = data.get('model_type')
            if not model_type or model_type not in ['pytorch', 'onnx']:
                print(f"ERROR: model_type must be 'pytorch' or 'onnx' in {yaml_path}")
                return None

            # Model path can be relative to model_dir or absolute
            model_weights = data.get('model_weights')
            if not model_weights or not isinstance(model_weights, str):
                print(f"ERROR: model_weights missing or invalid in {yaml_path}")
                return None

            # Resolve model path
            if os.path.isabs(model_weights):
                model_path = model_weights
            else:
                model_path = os.path.join(model_dir, model_weights)

            # Check if model file exists
            if not os.path.exists(model_path):
                print(f"ERROR: Model weights not found: {model_path}")
                return None

            confidence_threshold = data.get('confidence_threshold', 0.5)
            if not isinstance(confidence_threshold, (int, float)) or not (0.0 <= confidence_threshold <= 1.0):
                print(f"ERROR: confidence_threshold must be between 0.0 and 1.0 in {yaml_path}")
                return None

            nms_iou_threshold = data.get('nms_iou_threshold')
            if nms_iou_threshold is not None:
                if not isinstance(nms_iou_threshold, (int, float)) or not (0.0 <= nms_iou_threshold <= 1.0):
                    print(f"ERROR: nms_iou_threshold must be between 0.0 and 1.0 in {yaml_path}")
                    return None

            output_schema = data.get('output_schema', {})
            if not isinstance(output_schema, dict):
                print(f"ERROR: output_schema must be a dict in {yaml_path}")
                return None

            # Optional metadata
            description = data.get('description')
            author = data.get('author')
            license_info = data.get('license')

            # Create ModelConfig
            return cls(
                model_id=model_id,
                model_name=model_name,
                model_version=model_version,
                supported_tasks=supported_tasks,
                input_format=input_format,
                expected_resolution=expected_resolution,
                gpu_required=gpu_required,
                gpu_memory_mb=gpu_memory_mb,
                cpu_fallback_allowed=cpu_fallback_allowed,
                model_type=model_type,
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                nms_iou_threshold=nms_iou_threshold,
                output_schema=output_schema,
                description=description,
                author=author,
                license=license_info
            )

        except FileNotFoundError:
            print(f"ERROR: model.yaml not found: {yaml_path}")
            return None
        except yaml.YAMLError as e:
            print(f"ERROR: Invalid YAML in {yaml_path}: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to parse model.yaml at {yaml_path}: {e}")
            return None

    def to_runtime_config(self) -> Dict[str, Any]:
        """
        Convert to runtime configuration dict for InferenceHandler.

        Returns:
            Dict compatible with Phase 4.2.1/4.2.2 InferenceHandler
        """
        # Determine device based on GPU requirements
        if self.gpu_required:
            device = "cuda"  # Will fail if GPU unavailable
        elif self.cpu_fallback_allowed:
            device = "cuda"  # Will fallback to CPU if unavailable
        else:
            device = "cpu"  # Explicit CPU only

        return {
            "model_type": self.model_type,
            "model_path": self.model_path,
            "device": device,
            "input_size": self.expected_resolution,
            "confidence_threshold": self.confidence_threshold,
            "nms_iou_threshold": self.nms_iou_threshold,
        }

    def __repr__(self) -> str:
        return (
            f"ModelConfig(id={self.model_id!r}, "
            f"name={self.model_name!r}, "
            f"version={self.model_version!r}, "
            f"type={self.model_type!r}, "
            f"gpu_required={self.gpu_required})"
        )


# EXAMPLE model.yaml:
#
# model_id: yolov8n
# model_name: YOLOv8 Nano
# model_version: 8.0.0
# description: Lightweight object detection model
# author: Ultralytics
# license: AGPL-3.0
#
# supported_tasks:
#   - object_detection
#   - instance_segmentation
#
# input_format: NV12
# expected_resolution: [640, 640]
#
# resource_requirements:
#   gpu_required: false
#   gpu_memory_mb: 500
#   cpu_fallback_allowed: true
#
# model_type: pytorch
# model_weights: weights/yolov8n.pt
# confidence_threshold: 0.5
# nms_iou_threshold: 0.45
#
# output_schema:
#   type: object_detection
#   format: xyxy
#   classes: 80
#   class_names_file: coco_classes.txt
