#!/bin/bash
# Package complete bundle with data, schemas, and documentation

set -e

DIST_DIR="dist/srd_5_1"

echo "📦 Packaging SRD 5.1 bundle..."

# Ensure dist directory exists
if [ ! -d "$DIST_DIR/data" ]; then
    echo "❌ Error: $DIST_DIR/data not found. Run 'python -m srd_builder.build --ruleset srd_5_1 --out dist' first."
    exit 1
fi

# Copy README (from BUNDLE_README.md)
echo "  ✓ Copying README.md"
cp docs/BUNDLE_README.md "$DIST_DIR/README.md"

# Copy schemas
echo "  ✓ Copying schemas/"
mkdir -p "$DIST_DIR/schemas"
cp schemas/monster.schema.json "$DIST_DIR/schemas/"
cp schemas/equipment.schema.json "$DIST_DIR/schemas/"

# Copy documentation
echo "  ✓ Copying docs/"
mkdir -p "$DIST_DIR/docs"
cp docs/SCHEMAS.md "$DIST_DIR/docs/"
cp docs/DATA_DICTIONARY.md "$DIST_DIR/docs/"

echo "✅ Bundle complete: $DIST_DIR/"
echo ""
echo "Bundle contents:"
ls -lh "$DIST_DIR"
echo ""
echo "To create archive:"
echo "  cd dist && tar -czf srd-builder-output-v0.4.2.tar.gz srd_5_1/"
