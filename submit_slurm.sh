#!/bin/bash
#SBATCH --job-name=sim          # Job name
#SBATCH --output=logs/sim_%A_%a.out  # Output file name (%A = job ID, %a = array index)
#SBATCH --error=logs/sim_%A_%a.err   # Error file name
#SBATCH --array=0-4                   # Job array with 5 tasks (one per treatment)
#SBATCH --time=01:00:00              # Time limit (1 hour - should be faster with GPU)
#SBATCH --nodes=1                     # Number of nodes
#SBATCH --ntasks=1                    # Number of tasks per node
#SBATCH --cpus-per-task=4            # Number of CPU cores per task
#SBATCH --mem=16G                     # Memory per node
#SBATCH --gres=gpu:titanrtx:1        # Request 1 Titan RTX GPU
#SBATCH --mail-type=END,FAIL         # Email notification
#SBATCH --mail-user=lyk25@cornell.edu  # Email address

# Load necessary modules
module load cuda/11.8
module load conda

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Activate conda environment
conda activate sshift

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export CUDA_VISIBLE_DEVICES=$SLURM_JOB_GPUS
export TRANSFORMERS_CACHE="/scratch/lyk25/.cache/huggingface"  # Adjust path as needed
export HF_HOME="/scratch/lyk25/.cache/huggingface"

# Print GPU information
nvidia-smi

# Run the simulation script with the current array task ID
python slurm_runner.py --task-id $SLURM_ARRAY_TASK_ID --num-simulations 20 --num-turns 5 --use-gpu 