#!/bin/bash
# Build documentation for deployment

set -e

echo "Installing documentation dependencies..."
pip install -r requirements-docs.txt

echo "Building documentation..."
mkdocs build

echo "Documentation built successfully!"
echo "To deploy, run: npm run deploy"