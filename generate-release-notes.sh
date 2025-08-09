#!/bin/bash

# Generate Release Notes from Commit
# Usage: ./generate-release-notes.sh <commit-hash> [tag-name]

COMMIT_HASH=${1:-"a395c6ffe5d6383d6c6d58e4b77c8c803f366180"}
TAG_NAME=${2:-"v1.0.0"}

echo "Generating release notes from commit: $COMMIT_HASH"
echo "Tag name: $TAG_NAME"
echo ""

# Get commits from the specified commit to HEAD
echo "## What's New in $TAG_NAME" > RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md
echo "### Changes since commit $COMMIT_HASH" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md

# Get all commits from the specified commit to HEAD
COMMITS=$(git log --oneline --no-merges $COMMIT_HASH..HEAD)

if [ -z "$COMMITS" ]; then
    echo "No commits found since $COMMIT_HASH"
    echo "### No changes since $COMMIT_HASH" >> RELEASE_NOTES.md
else
    echo "$COMMITS" | while read -r commit; do
        if [ ! -z "$commit" ]; then
            echo "- $commit" >> RELEASE_NOTES.md
        fi
    done
fi

# Add Docker image information
echo "" >> RELEASE_NOTES.md
echo "### Docker Image" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md
echo "The Docker image is available at:" >> RELEASE_NOTES.md
echo "\`\`\`bash" >> RELEASE_NOTES.md
echo "ghcr.io/brendanbank/gpsd-prometheus-exporter:$TAG_NAME" >> RELEASE_NOTES.md
echo "\`\`\`" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md

# Add usage example
echo "### Usage" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md
echo "\`\`\`bash" >> RELEASE_NOTES.md
echo "docker run -d \\" >> RELEASE_NOTES.md
echo "  --name gpsd-exporter \\" >> RELEASE_NOTES.md
echo "  -p 9015:9015 \\" >> RELEASE_NOTES.md
echo "  -e GPSD_HOST=host.docker.internal \\" >> RELEASE_NOTES.md
echo "  ghcr.io/brendanbank/gpsd-prometheus-exporter:$TAG_NAME" >> RELEASE_NOTES.md
echo "\`\`\`" >> RELEASE_NOTES.md

# Add multi-platform information
echo "" >> RELEASE_NOTES.md
echo "### Multi-Platform Support" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md
echo "This release includes Docker images for:" >> RELEASE_NOTES.md
echo "- **linux/amd64**: Intel/AMD 64-bit processors" >> RELEASE_NOTES.md
echo "- **linux/arm64/v8**: Apple Silicon, modern ARM64 servers" >> RELEASE_NOTES.md
echo "- **linux/arm/v7**: Raspberry Pi, older ARM devices" >> RELEASE_NOTES.md
echo "" >> RELEASE_NOTES.md
echo "Docker will automatically select the correct image for your platform." >> RELEASE_NOTES.md

echo ""
echo "Release notes generated in RELEASE_NOTES.md"
echo "Content:"
echo "----------------------------------------"
cat RELEASE_NOTES.md

