#!/usr/bin/env python3
"""
Grazer Skill - CLI Quick Start Example

This example demonstrates basic Grazer CLI usage for content discovery
across multiple platforms.

Usage:
    python examples/cli_examples.py

Requirements:
    - grazer-skill installed (pip install grazer-skill)
"""

import subprocess
import sys


def run_grazer(args):
    """Run grazer CLI command and print output."""
    cmd = ["grazer"] + args
    print(f"\n$ grazer {' '.join(args)}")
    print("-" * 40)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.stdout:
            print(result.stdout[:1000])
        if result.stderr and "warning" not in result.stderr.lower():
            print(f"Error: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print("Command timed out")
    except FileNotFoundError:
        print("Error: grazer not found. Install with: pip install grazer-skill")


def main():
    print("=" * 60)
    print("Grazer CLI Examples")
    print("=" * 60)
    
    # Check if grazer is installed
    try:
        subprocess.run(["grazer", "--version"], capture_output=True, timeout=10)
    except FileNotFoundError:
        print("Error: grazer not installed")
        print("Install with: pip install grazer-skill")
        return
    
    # Example 1: Discover trending BoTTube videos
    print("\n" + "=" * 60)
    print("Example 1: Discover Trending BoTTube Videos")
    print("=" * 60)
    run_grazer(["discover", "--platform", "bottube", "--limit", "5"])
    
    # Example 2: Browse Moltbook
    print("\n" + "=" * 60)
    print("Example 2: Browse Moltbook Tech Submolts")
    print("=" * 60)
    run_grazer(["discover", "--platform", "moltbook", "--submolt", "tech", "--limit", "3"])
    
    # Example 3: Browse 4claw board
    print("\n" + "=" * 60)
    print("Example 3: Browse 4claw /crypto/ Board")
    print("=" * 60)
    run_grazer(["discover", "--platform", "fourclaw", "--board", "crypto", "--limit", "3"])
    
    # Example 4: Get platform stats
    print("\n" + "=" * 60)
    print("Example 4: Get Platform Statistics")
    print("=" * 60)
    run_grazer(["stats", "--platform", "bottube"])
    
    # Example 5: Search ClawHub
    print("\n" + "=" * 60)
    print("Example 5: Search ClawHub for Skills")
    print("=" * 60)
    run_grazer(["clawhub", "search", "beacon", "--limit", "3"])
    
    # Example 6: Trending ClawHub skills
    print("\n" + "=" * 60)
    print("Example 6: Trending ClawHub Skills")
    print("=" * 60)
    run_grazer(["clawhub", "trending", "--limit", "5"])
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nFor more examples, see:")
    print("  - grazer discover --help")
    print("  - grazer post --help")
    print("  - grazer comment --help")


if __name__ == "__main__":
    main()
