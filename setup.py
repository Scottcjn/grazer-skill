"""
Setup script for grazer-skill PyPI package
"""

from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Report install to BoTTube
def post_install():
    try:
        import requests
        requests.post(
            "https://bottube.ai/api/downloads/skill",
            json={
                "skill": "grazer",
                "platform": "pypi",
                "version": "1.0.0",
            },
            timeout=5,
        )
    except:
        pass

setup(
    name="grazer-skill",
    version="1.3.0",
    author="Elyan Labs",
    author_email="scott@elyanlabs.ai",
    description="Claude Code skill for grazing worthy content across social platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Scottcjn/grazer-skill",
    project_urls={
        "Bug Tracker": "https://github.com/Scottcjn/grazer-skill/issues",
        "Homepage": "https://bottube.ai/skills/grazer",
        "Documentation": "https://github.com/Scottcjn/grazer-skill#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "grazer=grazer.cli:main",
        ],
    },
    keywords=[
        "claude-code",
        "skill",
        "social-media",
        "bottube",
        "moltbook",
        "clawcities",
        "clawsta",
        "4claw",
        "ai-agents",
        "content-discovery",
    ],
)
