#!/bin/bash

# Load necessary modules
module load cuda/11.8
module load conda

# Initialize conda
eval "$(conda shell.bash hook)"
conda activate sshift

# Set cache directory and create if needed
export TRANSFORMERS_CACHE="/share/lee/semantic_shift_project/laerdon/.cache/huggingface"
export HF_HOME="/share/lee/semantic_shift_project/laerdon/.cache/huggingface"
mkdir -p "$TRANSFORMERS_CACHE"

# Clear CUDA cache
python -c "import torch; torch.cuda.empty_cache()"

# Clean up any partial downloads
find "$TRANSFORMERS_CACHE" -name "*.json.lock" -delete
find "$TRANSFORMERS_CACHE" -name "*.incomplete" -delete

# Create logs directory if it doesn't exist
mkdir -p logs

# Print GPU information
echo "=== GPU Information ==="
nvidia-smi
echo "====================="

# Create offload directory
mkdir -p offload_folder

# Run a single simulation
echo "=== Running Test Simulation ==="
CUDA_LAUNCH_BLOCKING=1 python slurm_runner.py --task-id 0 --num-simulations 1 --num-turns 3 --use-gpu

# Print location of results
echo "=== Simulation Complete ==="
echo "Check the most recent directory in slurm_results/ for output"

# Cleanup
rm -rf offload_folder 