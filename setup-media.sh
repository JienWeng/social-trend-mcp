#!/usr/bin/env bash
set -euo pipefail
if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null && command -v tesseract >/dev/null; then
  echo 'FFmpeg, FFprobe and Tesseract are available.'
  exit 0
fi
if ! command -v apt-get >/dev/null; then
  echo 'Install FFmpeg (including FFprobe) and Tesseract using your system package manager.' >&2
  exit 1
fi
if [ "$(id -u)" -eq 0 ]; then
  apt-get update
  apt-get install -y ffmpeg tesseract-ocr
elif sudo -n true 2>/dev/null; then
  sudo -n apt-get update
  sudo -n apt-get install -y ffmpeg tesseract-ocr
else
  echo 'System packages require an administrator. Run sudo apt-get install ffmpeg tesseract-ocr.' >&2
  exit 1
fi
