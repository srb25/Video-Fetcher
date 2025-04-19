#!/bin/bash
set -e

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing core dependencies first..."
pip install wheel setuptools

echo "Installing dependencies with constraints..."
# Install with constraints to help resolve dependency conflicts
pip install -r requirements.txt -c constraints.txt

echo "Verifying installation..."
pip list

echo "Installing yt-dlp specifically (if needed)..."
pip install yt-dlp==2023.11.14 --no-deps

echo "Creating directories..."
mkdir -p downloads 