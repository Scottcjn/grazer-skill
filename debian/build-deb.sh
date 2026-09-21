#!/bin/bash
# Build .deb package for grazer-skill
set -e

# Single-source version from package.json
VERSION=$(node -p "require('./package.json').version" 2>/dev/null || grep -m1 version setup.py | cut -d'"' -f2 || echo "2.0.1")
PKG="grazer_${VERSION}_all"

rm -rf "/tmp/${PKG}"
mkdir -p "/tmp/${PKG}/DEBIAN"
mkdir -p "/tmp/${PKG}/usr/lib/python3/dist-packages/grazer"
mkdir -p "/tmp/${PKG}/usr/bin"

# Generate/copy control file with current version
sed "s/^Version:.*/Version: ${VERSION}/" debian/control > "/tmp/${PKG}/DEBIAN/control"

# Copy Python package
cp grazer/__init__.py "/tmp/${PKG}/usr/lib/python3/dist-packages/grazer/"
cp grazer/cli.py "/tmp/${PKG}/usr/lib/python3/dist-packages/grazer/"
cp grazer/imagegen.py "/tmp/${PKG}/usr/lib/python3/dist-packages/grazer/"
cp grazer/clawhub.py "/tmp/${PKG}/usr/lib/python3/dist-packages/grazer/"

# Create entry point
cat > "/tmp/${PKG}/usr/bin/grazer" << 'ENTRY'
#!/usr/bin/env python3
from grazer.cli import main
main()
ENTRY
chmod +x "/tmp/${PKG}/usr/bin/grazer"

# Build
dpkg-deb --build "/tmp/${PKG}" .
echo "Built: ${PKG}.deb"
