#!/usr/bin/env python3
"""
Setup script for GUIDE Multi-Agent Framework (guide-mas).
"""

from setuptools import setup, find_packages

setup(
    name="guide-mas",
    version="2.4.0",
    description="GUIDE: Policy-Aware Orchestration Framework for Enterprise LLM Multi-Agent Workflows",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Shafin Ahmad",
    author_email="tp0126417@mail.apu.edu.my",
    url="https://github.com/shafin0id/guide",
    packages=find_packages(include=["guide_mas", "guide_mas.*"]),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "cryptography>=41.0.0",
        "scipy>=1.10.0",
        "numpy>=1.24.0",
        "litellm>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "guide-eval=guide_mas.evaluation.runner:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
