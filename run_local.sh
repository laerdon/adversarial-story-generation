#!/bin/bash

# Load necessary modules
module load cuda/11.8
module load conda

# Initialize conda
eval "$(conda shell.bash hook)"
conda activate sshift

# Set cache directory
export TRANSFORMERS_CACHE="/share/lee/semantic_shift_project/laerdon/.cache/huggingface"
export HF_HOME="/share/lee/semantic_shift_project/laerdon/.cache/huggingface"

# Create logs directory if it doesn't exist
mkdir -p logs

# Print GPU information
nvidia-smi

# Run the simulation script
python slurm_runner.py --task-id 0 --num-simulations 20 --num-turns 5 --use-gpu

# Note: If you want to run all treatments sequentially, uncomment these lines:
# for task_id in {0..4}; do
#     echo "Running treatment $task_id"
#     python slurm_runner.py --task-id $task_id --num-simulations 20 --num-turns 5 --use-gpu
# done 