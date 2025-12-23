#!/bin/bash
# Rebuild dist/ archives from git history for version tracking
# Usage: ./scripts/rebuild_dist_archives.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Target versions to rebuild (keeping last 5 major versions)
VERSIONS=(
  "v0.15.0"
  "v0.16.0"
  "v0.17.0"
  "v0.18.0"
  "v0.18.1"
)

echo "🔄 Rebuilding dist/ archives for version tracking..."
echo ""

for VERSION in "${VERSIONS[@]}"; do
  # Check if tag exists
  if ! git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "⚠️  Skipping $VERSION (tag not found)"
    continue
  fi

  echo "📦 Building $VERSION..."

  # Create temp branch
  BRANCH="temp-rebuild-$VERSION"
  git branch -D "$BRANCH" 2>/dev/null || true
  git checkout -b "$BRANCH" "$VERSION" --quiet

  # Build if make target exists
  if make bundle 2>&1 | grep -q "No rule"; then
    echo "   ⚠️  No bundle target, trying legacy build..."
    if [ -f "scripts/build.py" ]; then
      python3 scripts/build.py || echo "   ❌ Build failed"
    fi
  fi

  # Archive dist if it was created
  if [ -d "dist/srd_5_1" ]; then
    ARCHIVE_NAME="dist_${VERSION//./_}"
    mkdir -p "archive/dist_versions/$ARCHIVE_NAME"
    cp -r dist/srd_5_1/* "archive/dist_versions/$ARCHIVE_NAME/"
    echo "   ✅ Archived to archive/dist_versions/$ARCHIVE_NAME/"
  else
    echo "   ⚠️  No dist/ created"
  fi

  # Return to main
  git checkout main --quiet
  git branch -D "$BRANCH" --quiet
  echo ""
done

echo "✅ Archive rebuild complete!"
echo ""
echo "Archived versions:"
ls -1d archive/dist_versions/dist_v* 2>/dev/null || echo "  (none created)"
