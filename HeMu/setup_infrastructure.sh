#!/bin/bash

# HeMu Infrastructure Setup Script
echo "🚀 Setting up HeMu infrastructure for Switzerland domain..."

# Create required directories
HEMU_ROOT="/Users/frischho/Documents/dev/heliomont_dml/app/HeMu"
mkdir -p "${HEMU_ROOT}/data/static/domainMatcher/CH"
mkdir -p "${HEMU_ROOT}/data/static/horayzon/CH"
mkdir -p "${HEMU_ROOT}/data/Helio/stats"
mkdir -p "${HEMU_ROOT}/runs/CH"
mkdir -p "${HEMU_ROOT}/configs"

echo "✅ Directory structure created"

# Check for HORAYZON dependency
if [ ! -d "${HEMU_ROOT}/deps/HORAYZON" ]; then
    echo "⚠️  HORAYZON not found. This needs to be installed manually."
    echo "   Expected path: ${HEMU_ROOT}/deps/HORAYZON"
fi

# Check for required config files
MISSING_FILES=()
if [ ! -f "${HEMU_ROOT}/configs/TSViT.yaml" ]; then
    MISSING_FILES+=("configs/TSViT.yaml")
fi
if [ ! -f "${HEMU_ROOT}/data/Helio/stats/stats_NC_2015_2020_sza80.csv" ]; then
    MISSING_FILES+=("data/Helio/stats/stats_NC_2015_2020_sza80.csv")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "⚠️  Missing required files:"
    printf '   %s\n' "${MISSING_FILES[@]}"
fi

echo "📋 Infrastructure setup complete!"
echo "Next steps:"
echo "1. Install HORAYZON dependency"
echo "2. Create Switzerland domain matcher"
echo "3. Prepare HORAYZON data for CH domain"
echo "4. Create model configurations"
