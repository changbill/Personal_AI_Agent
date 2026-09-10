#!/bin/sh
# Phase 0 - Mini PC environment probe
# Usage: sh phase0_probe.sh
# Collects CPU / RAM / Disk / GPU / OS info needed to pick a local LLM size.
# Read-only: installs nothing, changes nothing.

echo "=============================================="
echo " Phase 0 Environment Probe"
echo " date: $(date -Iseconds 2>/dev/null || date)"
echo " host: $(hostname 2>/dev/null)"
echo "=============================================="

echo
echo "----- [1] OS / KERNEL -----"
if [ -r /etc/os-release ]; then
  . /etc/os-release
  echo "distro      : $PRETTY_NAME"
fi
echo "kernel      : $(uname -r)"
echo "arch        : $(uname -m)"

echo
echo "----- [2] CPU -----"
if [ -r /proc/cpuinfo ]; then
  echo "model       : $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')"
  echo "logical cpus: $(grep -c '^processor' /proc/cpuinfo)"
fi
if command -v lscpu >/dev/null 2>&1; then
  lscpu | grep -E '^(Architecture|CPU\(s\)|Thread|Core|Socket|Model name|CPU max MHz|CPU min MHz|BogoMIPS|L3 cache|Flags)' \
        | sed 's/^/  /' | cut -c1-200
  # AVX/AVX2/AVX512 hugely affect llama.cpp CPU inference speed
  echo "  --- SIMD support (matters a lot for CPU inference) ---"
  for f in avx avx2 avx512f f16c fma; do
    if lscpu 2>/dev/null | grep -qw "$f" || grep -qw "$f" /proc/cpuinfo 2>/dev/null; then
      echo "    $f : YES"
    else
      echo "    $f : no"
    fi
  done
fi

echo
echo "----- [3] MEMORY -----"
if command -v free >/dev/null 2>&1; then
  free -h
else
  grep -E 'MemTotal|MemAvailable|SwapTotal' /proc/meminfo
fi
echo "  (MemAvailable is the number that decides which model fits)"

echo
echo "----- [4] DISK -----"
df -h / 2>/dev/null
[ -d /var/lib ] && df -h /var/lib 2>/dev/null | tail -n +2
echo "  (Ollama stores models under /usr/share/ollama/.ollama or ~/.ollama)"

echo
echo "----- [5] GPU / NPU / ACCELERATOR -----"
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "NVIDIA:"
  nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv 2>/dev/null | sed 's/^/  /'
else
  echo "NVIDIA: nvidia-smi not found"
fi
if command -v rocm-smi >/dev/null 2>&1; then
  echo "AMD ROCm: present"
else
  echo "AMD ROCm: not found"
fi
if command -v lspci >/dev/null 2>&1; then
  echo "PCI display/accel devices:"
  lspci 2>/dev/null | grep -Ei 'vga|3d|display|npu|neural' | sed 's/^/  /'
else
  echo "lspci not available"
fi
# Intel integrated GPU / NPU device nodes
[ -e /dev/dri ] && { echo "/dev/dri:"; ls -1 /dev/dri 2>/dev/null | sed 's/^/  /'; }
[ -e /dev/accel ] && { echo "/dev/accel (NPU):"; ls -1 /dev/accel 2>/dev/null | sed 's/^/  /'; }

echo
echo "----- [6] EXISTING TOOLING -----"
for t in docker "docker compose" ollama python3 pip3 git redis-server psql curl; do
  # shellcheck disable=SC2086
  bin=$(echo $t | cut -d' ' -f1)
  if command -v "$bin" >/dev/null 2>&1; then
    case "$t" in
      "docker compose") docker compose version 2>/dev/null | head -1 | sed 's/^/  docker compose : /' || echo "  docker compose : plugin missing" ;;
      docker)   echo "  docker         : $(docker --version 2>/dev/null)" ;;
      ollama)   echo "  ollama         : $(ollama --version 2>/dev/null)" ;;
      python3)  echo "  python3        : $(python3 --version 2>&1)" ;;
      pip3)     echo "  pip3           : $(pip3 --version 2>/dev/null | cut -d' ' -f1-2)" ;;
      git)      echo "  git            : $(git --version 2>/dev/null)" ;;
      redis-server) echo "  redis-server   : $(redis-server --version 2>/dev/null | cut -d' ' -f1-3)" ;;
      psql)     echo "  psql           : $(psql --version 2>/dev/null)" ;;
      curl)     echo "  curl           : present" ;;
    esac
  else
    echo "  $t : NOT FOUND"
  fi
done

echo
echo "----- [7] CURRENT LOAD -----"
uptime
echo "top memory consumers:"
ps -eo pmem,rss,comm --sort=-rss 2>/dev/null | head -6 | sed 's/^/  /'

echo
echo "=============================================="
echo " Probe complete. Paste this whole output back."
echo "=============================================="
