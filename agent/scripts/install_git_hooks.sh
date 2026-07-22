#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"

git -C "$repo_root" config core.hooksPath .githooks
echo "Configured core.hooksPath=.githooks"
