#!/bin/bash
echo "Starting GPU monitoring..."
while true; do
    gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
    gpu_mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    echo "$(date '+%H:%M:%S') - GPU Util: ${gpu_util}% - GPU Mem: ${gpu_mem}MB"
    sleep 2
done
