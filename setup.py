"""
Setup script for grazer-skill PyPI package
"""

from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="grazer-skill",
    version="1.8.0",
    author="Elyan Labs",
    author_email="scott@elyanlabs.ai",
    description="Claude Code skill for grazing content across BoTTube, Moltbook, 4claw, The Colony, MoltX, MoltExchange, PinchedIn, ClawHub, AgentChan, and 15 more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Scottcjn/grazer-skill",
    project_urls={
        "Bug Tracker": "https://github.com/Scottcjn/grazer-skill/issues",
        "Homepage": "https://bottube.ai/skills/grazer",
        "Documentation": "https://github.com/Scottcjn/grazer-skill#readme",
        "Dev.to": "https://dev.to/scottcjn",
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
        "pinchedin",
        "clawtasks",
        "clawnews",
        "ai-agents",
        "content-discovery",
        "clawhub",
        "agentchan",
        "hiring",
        "bounties",
        "thecolony",
        "moltx",
        "moltexchange",
    ],
)
