"""
Phase 4.4 - Ruth AI Model Runtime Base Image
Setup script for ai_model_container package

This package provides the IPC infrastructure and base runtime
for all Ruth AI model containers.
"""

from setuptools import setup, find_packages

setup(
    name="ai_model_container",
    version="0.4.0",
    description="Ruth AI Model Container IPC Infrastructure",
    author="VAS AI Platform",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "opencv-python-headless>=4.5.0",
        "PyYAML>=5.4.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
