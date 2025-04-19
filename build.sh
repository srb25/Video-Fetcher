#!/bin/bash
set -e

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies with specific constraints..."
pip install -r requirements.txt --use-pep517

echo "Verifying installation..."
pip list

echo "Creating directories..."
mkdir -p downloads 