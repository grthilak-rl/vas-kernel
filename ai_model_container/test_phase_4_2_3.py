"""
Phase 4.2.3 Validation Tests

This script validates the Phase 4.2.3 implementation:
- model.yaml parsing and validation
- Filesystem model discovery
- GPU requirement enforcement
- Container integration

Run with:
    python3 ai_model_container/test_phase_4_2_3.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path


def test_model_config_parsing():
    """Test model.yaml parsing and validation."""
    print("\n" + "=" * 60)
    print("TEST 1: model.yaml Parsing and Validation")
    print("=" * 60)

    from ai_model_container import ModelConfig

    # Create temporary test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        model_dir = os.path.join(tmpdir, "test_model")
        os.makedirs(model_dir)

        # Create valid model.yaml
        yaml_path = os.path.join(model_dir, "model.yaml")
        with open(yaml_path, 'w') as f:
            f.write("""
model_id: test_yolov8n
model_name: Test YOLOv8 Nano
model_version: 1.0.0
description: Test model for validation
author: Test Author
license: MIT

supported_tasks:
  - object_detection

input_format: NV12
expected_resolution: [640, 640]

resource_requirements:
  gpu_required: false
  gpu_memory_mb: 500
  cpu_fallback_allowed: true

model_type: pytorch
model_weights: weights/test.pt
confidence_threshold: 0.5
nms_iou_threshold: 0.45

output_schema:
  type: object_detection
  format: xyxy
  classes: 80
""")

        # Create weights directory and file
        weights_dir = os.path.join(model_dir, "weights")
        os.makedirs(weights_dir)
        weights_path = os.path.join(weights_dir, "test.pt")
        with open(weights_path, 'w') as f:
            f.write("mock weights")

        # Test parsing
        print("\nParsing valid model.yaml...")
        config = ModelConfig.from_yaml_file(yaml_path, model_dir)

        if config is None:
            print("✗ FAIL: Valid model.yaml failed to parse")
            return False

        print(f"✓ PASS: Parsed successfully")
        print(f"  Model ID: {config.model_id}")
        print(f"  Model Name: {config.model_name}")
        print(f"  Model Version: {config.model_version}")
        print(f"  Model Type: {config.model_type}")
        print(f"  GPU Required: {config.gpu_required}")
        print(f"  CPU Fallback: {config.cpu_fallback_allowed}")
        print(f"  Model Path: {config.model_path}")

        # Test runtime config conversion
        print("\nConverting to runtime config...")
        runtime_config = config.to_runtime_config()
        print(f"✓ PASS: Runtime config: {runtime_config}")

    return True


def test_invalid_model_configs():
    """Test validation of invalid model.yaml configurations."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid Configuration Detection")
    print("=" * 60)

    from ai_model_container import ModelConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Missing required field
        print("\nTest 2.1: Missing required field (model_id)...")
        model_dir = os.path.join(tmpdir, "test1")
        os.makedirs(model_dir)
        yaml_path = os.path.join(model_dir, "model.yaml")
        with open(yaml_path, 'w') as f:
            f.write("""
model_name: Test Model
model_version: 1.0.0
""")

        config = ModelConfig.from_yaml_file(yaml_path, model_dir)
        if config is None:
            print("✓ PASS: Correctly rejected missing model_id")
        else:
            print("✗ FAIL: Should have rejected missing model_id")
            return False

        # Test 2: Contradictory GPU settings
        print("\nTest 2.2: Contradictory GPU settings...")
        model_dir = os.path.join(tmpdir, "test2")
        os.makedirs(model_dir)
        yaml_path = os.path.join(model_dir, "model.yaml")
        os.makedirs(os.path.join(model_dir, "weights"))
        with open(os.path.join(model_dir, "weights/test.pt"), 'w') as f:
            f.write("mock")

        with open(yaml_path, 'w') as f:
            f.write("""
model_id: test_contradictory
model_name: Test Model
model_version: 1.0.0
supported_tasks: [object_detection]
input_format: NV12
expected_resolution: [640, 640]
resource_requirements:
  gpu_required: true
  cpu_fallback_allowed: true
model_type: pytorch
model_weights: weights/test.pt
confidence_threshold: 0.5
output_schema:
  type: object_detection
""")

        config = ModelConfig.from_yaml_file(yaml_path, model_dir)
        if config is None:
            print("✓ PASS: Correctly rejected contradictory GPU settings")
        else:
            print("✗ FAIL: Should have rejected contradictory GPU settings")
            return False

        # Test 3: Missing weights file
        print("\nTest 2.3: Missing weights file...")
        model_dir = os.path.join(tmpdir, "test3")
        os.makedirs(model_dir)
        yaml_path = os.path.join(model_dir, "model.yaml")

        with open(yaml_path, 'w') as f:
            f.write("""
model_id: test_missing_weights
model_name: Test Model
model_version: 1.0.0
supported_tasks: [object_detection]
input_format: NV12
expected_resolution: [640, 640]
resource_requirements:
  gpu_required: false
  cpu_fallback_allowed: true
model_type: pytorch
model_weights: weights/nonexistent.pt
confidence_threshold: 0.5
output_schema:
  type: object_detection
""")

        config = ModelConfig.from_yaml_file(yaml_path, model_dir)
        if config is None:
            print("✓ PASS: Correctly rejected missing weights file")
        else:
            print("✗ FAIL: Should have rejected missing weights file")
            return False

    return True


def test_model_discovery():
    """Test filesystem-based model discovery."""
    print("\n" + "=" * 60)
    print("TEST 3: Filesystem Model Discovery")
    print("=" * 60)

    from ai_model_container import ModelDiscovery

    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = os.path.join(tmpdir, "models")
        os.makedirs(models_dir)

        # Create valid model 1
        model1_dir = os.path.join(models_dir, "model1")
        os.makedirs(model1_dir)
        os.makedirs(os.path.join(model1_dir, "weights"))
        with open(os.path.join(model1_dir, "weights/model1.pt"), 'w') as f:
            f.write("mock")

        with open(os.path.join(model1_dir, "model.yaml"), 'w') as f:
            f.write("""
model_id: model1
model_name: Model 1
model_version: 1.0.0
supported_tasks: [object_detection]
input_format: NV12
expected_resolution: [640, 640]
resource_requirements:
  gpu_required: false
  cpu_fallback_allowed: true
model_type: pytorch
model_weights: weights/model1.pt
confidence_threshold: 0.5
output_schema:
  type: object_detection
""")

        # Create valid model 2
        model2_dir = os.path.join(models_dir, "model2")
        os.makedirs(model2_dir)
        os.makedirs(os.path.join(model2_dir, "weights"))
        with open(os.path.join(model2_dir, "weights/model2.onnx"), 'w') as f:
            f.write("mock")

        with open(os.path.join(model2_dir, "model.yaml"), 'w') as f:
            f.write("""
model_id: model2
model_name: Model 2
model_version: 2.0.0
supported_tasks: [image_classification]
input_format: NV12
expected_resolution: [224, 224]
resource_requirements:
  gpu_required: false
  cpu_fallback_allowed: true
model_type: onnx
model_weights: weights/model2.onnx
confidence_threshold: 0.7
output_schema:
  type: classification
""")

        # Create invalid model (missing model.yaml)
        model3_dir = os.path.join(models_dir, "model3")
        os.makedirs(model3_dir)

        # Create invalid model (invalid YAML)
        model4_dir = os.path.join(models_dir, "model4")
        os.makedirs(model4_dir)
        with open(os.path.join(model4_dir, "model.yaml"), 'w') as f:
            f.write("invalid: yaml: content:")

        # Run discovery
        print(f"\nDiscovering models in: {models_dir}")
        discovery = ModelDiscovery(models_dir=models_dir)
        available_models = discovery.discover_models()

        print(f"\nDiscovery Results:")
        print(f"  Available models: {len(available_models)}")
        print(f"  Unavailable models: {len(discovery._unavailable_models)}")

        # Validate results
        if len(available_models) != 2:
            print(f"✗ FAIL: Expected 2 available models, got {len(available_models)}")
            return False

        if "model1" not in available_models:
            print("✗ FAIL: model1 should be available")
            return False

        if "model2" not in available_models:
            print("✗ FAIL: model2 should be available")
            return False

        print("✓ PASS: Correct number of models discovered")

        # Check unavailable models
        if "model3" not in discovery._unavailable_models:
            print("✗ FAIL: model3 should be unavailable")
            return False

        reason = discovery.get_unavailable_reason("model3")
        if reason != "missing_model_yaml":
            print(f"✗ FAIL: model3 should be unavailable due to 'missing_model_yaml', got {reason}")
            return False

        print("✓ PASS: Unavailable models tracked correctly")

        # Test discovery methods
        print("\nTesting discovery methods...")
        available_ids = discovery.list_available_models()
        print(f"  Available model IDs: {available_ids}")

        if set(available_ids) != {"model1", "model2"}:
            print("✗ FAIL: list_available_models() incorrect")
            return False

        if not discovery.is_available("model1"):
            print("✗ FAIL: is_available('model1') should be True")
            return False

        if discovery.is_available("model3"):
            print("✗ FAIL: is_available('model3') should be False")
            return False

        print("✓ PASS: Discovery methods working correctly")

    return True


def test_gpu_requirement_enforcement():
    """Test GPU requirement enforcement in container startup."""
    print("\n" + "=" * 60)
    print("TEST 4: GPU Requirement Enforcement")
    print("=" * 60)

    from ai_model_container import ModelContainer

    # Check if GPU is available
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except ImportError:
        gpu_available = False

    print(f"\nGPU available: {gpu_available}")

    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = os.path.join(tmpdir, "models")
        os.makedirs(models_dir)

        # Create GPU-required model
        model_dir = os.path.join(models_dir, "gpu_required_model")
        os.makedirs(model_dir)
        os.makedirs(os.path.join(model_dir, "weights"))
        with open(os.path.join(model_dir, "weights/model.pt"), 'w') as f:
            f.write("mock")

        with open(os.path.join(model_dir, "model.yaml"), 'w') as f:
            f.write("""
model_id: gpu_required_model
model_name: GPU Required Model
model_version: 1.0.0
supported_tasks: [object_detection]
input_format: NV12
expected_resolution: [640, 640]
resource_requirements:
  gpu_required: true
  cpu_fallback_allowed: false
model_type: pytorch
model_weights: weights/model.pt
confidence_threshold: 0.5
output_schema:
  type: object_detection
""")

        # Try to create container with GPU-required model
        print("\nAttempting to create container with GPU-required model...")

        if gpu_available:
            # Should succeed
            try:
                container = ModelContainer(
                    model_id="gpu_required_model",
                    models_dir=models_dir
                )
                print("✓ PASS: Container created successfully (GPU available)")
            except RuntimeError as e:
                print(f"✗ FAIL: Container should succeed when GPU available: {e}")
                return False
        else:
            # Should fail fast
            try:
                container = ModelContainer(
                    model_id="gpu_required_model",
                    models_dir=models_dir
                )
                print("✗ FAIL: Container should have failed without GPU")
                return False
            except RuntimeError as e:
                if "requires GPU" in str(e):
                    print(f"✓ PASS: Container correctly failed without GPU")
                    print(f"  Error: {e}")
                else:
                    print(f"✗ FAIL: Wrong error message: {e}")
                    return False

    return True


def test_backward_compatibility():
    """Test backward compatibility with Phase 4.2.1/4.2.2."""
    print("\n" + "=" * 60)
    print("TEST 5: Backward Compatibility")
    print("=" * 60)

    from ai_model_container import ModelContainer

    print("\nTesting legacy model_config parameter...")

    # This should work without discovery (Phase 4.2.1/4.2.2 mode)
    try:
        # Don't actually start the container (would need real model)
        # Just verify initialization succeeds
        container = ModelContainer(
            model_id="legacy_test",
            model_config={
                "model_type": "pytorch",
                "model_path": "/nonexistent/path.pt",  # Won't be loaded during init
                "device": "cpu"
            }
        )
        print("✓ PASS: Legacy model_config parameter still works")
    except Exception as e:
        # Expected to fail during InferenceHandler init due to missing file or PyTorch
        # But should get past discovery logic (that's what we're testing)
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["model_path", "no such file", "pytorch not available", "model loading failed"]):
            print("✓ PASS: Legacy config accepted (failed at model load as expected)")
            print(f"  Note: {e}")
        else:
            print(f"✗ FAIL: Unexpected error: {e}")
            return False

    return True


def main():
    """Run all Phase 4.2.3 validation tests."""
    print("\n" + "=" * 60)
    print("PHASE 4.2.3 VALIDATION TESTS")
    print("=" * 60)
    print("\nValidating:")
    print("- model.yaml parsing and validation")
    print("- Filesystem model discovery")
    print("- GPU requirement enforcement")
    print("- Container integration")
    print("- Backward compatibility")

    tests = [
        ("model.yaml Parsing", test_model_config_parsing),
        ("Invalid Config Detection", test_invalid_model_configs),
        ("Model Discovery", test_model_discovery),
        ("GPU Requirement Enforcement", test_gpu_requirement_enforcement),
        ("Backward Compatibility", test_backward_compatibility),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ All Phase 4.2.3 validation tests PASSED")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
