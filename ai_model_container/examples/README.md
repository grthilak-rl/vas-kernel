# Phase 4.2.3 Model Configuration Examples

This directory contains example `model.yaml` templates for onboarding AI models.

## Quick Start

To onboard a new model:

1. Create a directory under `/opt/ruth-ai/models/` with your model ID:
   ```bash
   mkdir -p /opt/ruth-ai/models/yolov8n
   ```

2. Copy an appropriate template to `model.yaml`:
   ```bash
   cp examples/yolov8n_model.yaml /opt/ruth-ai/models/yolov8n/model.yaml
   ```

3. Create a `weights/` subdirectory and add your model file:
   ```bash
   mkdir -p /opt/ruth-ai/models/yolov8n/weights
   cp /path/to/yolov8n.pt /opt/ruth-ai/models/yolov8n/weights/
   ```

4. Start your container:
   ```python
   from ai_model_container import ModelContainer

   # Container will automatically discover model from filesystem
   container = ModelContainer(model_id="yolov8n")
   container.start()
   ```

## Available Templates

### [yolov8n_model.yaml](yolov8n_model.yaml)
- **Model Type**: Object Detection
- **Framework**: PyTorch
- **GPU Required**: No (CPU fallback allowed)
- **Use Case**: Lightweight real-time object detection

### [resnet50_model.yaml](resnet50_model.yaml)
- **Model Type**: Image Classification
- **Framework**: PyTorch
- **GPU Required**: No (CPU fallback allowed)
- **Use Case**: General-purpose image classification

### [gpu_required_model.yaml](gpu_required_model.yaml)
- **Model Type**: Object Detection
- **Framework**: PyTorch
- **GPU Required**: YES (fail-fast if unavailable)
- **Use Case**: Large models that MUST run on GPU

### [onnx_model.yaml](onnx_model.yaml)
- **Model Type**: Image Classification
- **Framework**: ONNX Runtime
- **GPU Required**: No (CPU fallback allowed)
- **Use Case**: ONNX-exported models for cross-platform inference

## Directory Structure

Expected layout for each model:

```
/opt/ruth-ai/models/
├── yolov8n/
│   ├── model.yaml              # REQUIRED: Model configuration
│   ├── weights/
│   │   └── yolov8n.pt         # Model weights file
│   └── coco_classes.txt       # Optional: Class names
├── resnet50/
│   ├── model.yaml
│   ├── weights/
│   │   └── resnet50.pt
│   └── imagenet_classes.txt
└── custom_model/
    ├── model.yaml
    └── weights/
        └── custom_model.onnx
```

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | Unique identifier (matches directory name) |
| `model_name` | string | Human-readable name |
| `model_version` | string | Version string |
| `supported_tasks` | list | Tasks this model can perform |
| `input_format` | string | Expected input format (usually "NV12") |
| `expected_resolution` | list | [width, height] for model input |
| `resource_requirements` | dict | GPU and CPU requirements |
| `model_type` | string | "pytorch" or "onnx" |
| `model_weights` | string | Path to weights file |
| `confidence_threshold` | float | Default confidence (0.0-1.0) |
| `output_schema` | dict | Output format description |

### Resource Requirements

| Field | Type | Description |
|-------|------|-------------|
| `gpu_required` | bool | If true, container fails without GPU |
| `gpu_memory_mb` | int | Minimum GPU memory (hint only) |
| `cpu_fallback_allowed` | bool | If true, runs on CPU when GPU unavailable |

**CRITICAL**: `gpu_required=true` and `cpu_fallback_allowed=true` is **contradictory** and will fail validation.

## GPU Requirement Semantics

### Scenario 1: GPU Preferred, CPU Fallback Allowed
```yaml
resource_requirements:
  gpu_required: false
  cpu_fallback_allowed: true
```
- Container attempts to use GPU if available
- Falls back to CPU if GPU unavailable
- Container always starts successfully

### Scenario 2: GPU Strictly Required
```yaml
resource_requirements:
  gpu_required: true
  cpu_fallback_allowed: false
```
- Container REQUIRES GPU to start
- Container **fails fast** if no GPU available
- No fallback, no degraded mode

### Scenario 3: CPU Only
```yaml
resource_requirements:
  gpu_required: false
  cpu_fallback_allowed: false
```
- Container runs on CPU only
- Never attempts GPU initialization

## Validation Rules

The model.yaml parser enforces:

1. All required fields must be present
2. Field types must match expected types
3. `model_weights` file must exist at specified path
4. `confidence_threshold` must be between 0.0 and 1.0
5. `expected_resolution` must be `[width, height]`
6. `model_type` must be "pytorch" or "onnx"
7. GPU requirements must not be contradictory
8. Numeric fields must have valid ranges

Invalid configurations result in model being marked **UNAVAILABLE** (no retries).

## Discovery Process

Model discovery happens **ONCE** at container startup:

1. Container starts with `model_id` parameter
2. Discovery scans `/opt/ruth-ai/models/`
3. For each subdirectory:
   - Look for `model.yaml`
   - Parse and validate configuration
   - Check if weights file exists
   - Validate GPU requirements
4. Model marked AVAILABLE or UNAVAILABLE
5. If UNAVAILABLE, reason is logged

**No hot-reload**: Changes to model.yaml require container restart.

## Common Errors

### Error: "model.yaml not found"
**Cause**: No `model.yaml` in model directory
**Fix**: Create `model.yaml` using a template from this directory

### Error: "Model weights not found: /path/to/model.pt"
**Cause**: `model_weights` path is incorrect or file missing
**Fix**: Verify weights file exists at specified path (relative to model directory)

### Error: "gpu_required=true and cpu_fallback_allowed=true is contradictory"
**Cause**: Conflicting GPU settings
**Fix**: Set `cpu_fallback_allowed: false` when `gpu_required: true`

### Error: "Model unavailable: invalid_model_yaml"
**Cause**: YAML syntax error or missing required fields
**Fix**: Validate YAML syntax and check all required fields are present

### Container fails with "FATAL: Model requires GPU but no GPU is available"
**Cause**: `gpu_required: true` but no CUDA GPU detected
**Fix**: Either install GPU drivers or set `gpu_required: false` with `cpu_fallback_allowed: true`

## Testing Your Configuration

Before deploying, validate your model.yaml:

```python
from ai_model_container import ModelConfig

# Parse model.yaml
config = ModelConfig.from_yaml_file(
    yaml_path="/opt/ruth-ai/models/yolov8n/model.yaml",
    model_dir="/opt/ruth-ai/models/yolov8n"
)

if config is None:
    print("ERROR: Invalid model.yaml")
else:
    print(f"Model configuration valid: {config}")

    # Convert to runtime config
    runtime_config = config.to_runtime_config()
    print(f"Runtime config: {runtime_config}")
```

## Next Steps

After creating your model.yaml:

1. Test the configuration locally
2. Start the container and verify model loads
3. Send inference requests via IPC
4. Monitor logs for warnings or errors

For integration with Ruth AI Core, see Phase 4.2.4+ documentation.
