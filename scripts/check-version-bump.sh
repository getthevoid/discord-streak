#!/bin/bash

# Check if source files are modified but version is not bumped

# Get staged files in src/ (excluding __init__.py which contains version)
src_changes=$(git diff --cached --name-only -- 'src/*.py' 'src/**/*.py' | grep -v '__init__.py')

if [ -z "$src_changes" ]; then
    # No source files changed, skip check
    exit 0
fi

missing_files=""

# Check if pyproject.toml has version change
if ! git diff --cached -- pyproject.toml | grep -qE '^\+version\s*='; then
    missing_files="$missing_files  - pyproject.toml\n"
fi

# Check if README.md has version change
if ! git diff --cached -- README.md | grep -qE '^\+.*"version":'; then
    missing_files="$missing_files  - README.md\n"
fi

# Check if src/__init__.py has version change
if ! git diff --cached -- src/__init__.py | grep -qE '^\+.*"version":'; then
    missing_files="$missing_files  - src/__init__.py\n"
fi

# Check if uv.lock has been updated (run uv sync)
if ! git diff --cached --name-only | grep -q 'uv.lock'; then
    missing_files="$missing_files  - uv.lock (run 'uv sync')\n"
fi

if [ -n "$missing_files" ]; then
    echo "ERROR: Source files modified but version not bumped in all required files"
    echo ""
    echo "Modified source files:"
    echo "$src_changes" | sed 's/^/  - /'
    echo ""
    echo "Missing version updates in:"
    echo -e "$missing_files"
    echo "Please update the version in all files and run 'uv sync' before committing."
    echo "To skip this check, use: git commit --no-verify"
    exit 1
fi

exit 0
