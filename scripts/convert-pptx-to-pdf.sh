#!/usr/bin/env bash
# Convert PPTX to PDF using LibreOffice (soffice). Usage:
# ./scripts/convert-pptx-to-pdf.sh <input-pptx> <output-dir>
set -euo pipefail
if [ $# -lt 2 ]; then
  echo "Usage: $0 <input-pptx> <output-dir>"
  exit 2
fi
INPUT="$1"
OUTDIR="$2"
if ! command -v soffice >/dev/null 2>&1; then
  echo "Error: soffice (LibreOffice) is not installed or not on PATH."
  echo "Install LibreOffice (brew install --cask libreoffice) or run this on a machine with soffice available."
  exit 3
fi
mkdir -p "$OUTDIR"
soffice --headless --convert-to pdf --outdir "$OUTDIR" "$INPUT"
echo "Converted: $INPUT -> $OUTDIR"