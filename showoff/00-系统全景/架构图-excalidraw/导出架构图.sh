#!/usr/bin/env bash
set -euo pipefail

# 可通过 EXCALIDRAW_RENDERER_DIR 覆盖本机技能目录。
renderer_dir="${EXCALIDRAW_RENDERER_DIR:-/Users/lidongyuan/ai-ide-shared-config/skills/excalidraw-diagram/references}"
diagram_dir="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -f "$renderer_dir/render_excalidraw.py" ]]; then
  echo "找不到 render_excalidraw.py：$renderer_dir" >&2
  echo "请设置 EXCALIDRAW_RENDERER_DIR 后重试。" >&2
  exit 1
fi

cd "$renderer_dir"
for source in "$diagram_dir"/*.excalidraw; do
  output="${source%.excalidraw}.png"
  uv run python render_excalidraw.py "$source" --output "$output" --scale 2
done
