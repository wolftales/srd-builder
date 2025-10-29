#!/bin/bash
# Cleanup unused files and directories from the project

set -e

echo "🧹 Cleaning up cruft from srd-builder..."

# Remove empty data directory (output goes to dist/)
if [ -d "rulesets/srd_5_1/data" ]; then
    rmdir rulesets/srd_5_1/data 2>/dev/null && echo "✓ Removed empty rulesets/srd_5_1/data/"
fi

# Remove unused template files
if [ -d "docs/templates" ]; then
    rm -rf docs/templates && echo "✓ Removed docs/templates/"
fi

# Remove placeholder schemas
if [ -f "schemas/equipment.schema.json" ]; then
    rm schemas/equipment.schema.json && echo "✓ Removed schemas/equipment.schema.json"
fi
if [ -f "schemas/spell.schema.json" ]; then
    rm schemas/spell.schema.json && echo "✓ Removed schemas/spell.schema.json"
fi

# Remove legacy patch script
if [ -d "scripts/_refs" ]; then
    rm -rf scripts/_refs && echo "✓ Removed scripts/_refs/"
fi

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "Note: Keeping test fixtures for future entities (equipment, spells, etc.)"
echo "      These will be needed when implementing v0.5.0+"
