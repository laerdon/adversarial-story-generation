import multiprocessing

# Set the start method to 'spawn' before any CUDA initialization
multiprocessing.set_start_method("spawn", force=True)

import argparse
import os
from datetime import datetime
from run_simulations import TREATMENTS
from cluster_runner import run_parallel_simulations


def get_treatment_for_task(task_id):
    """Map SLURM task ID to treatment key."""
    treatment_keys = list(TREATMENTS.keys())
    if task_id >= len(treatment_keys):
        raise ValueError(
            f"Task ID {task_id} exceeds number of treatments {len(treatment_keys)}"
        )
    return [treatment_keys[task_id]]


def setup_output_directory():
    """Create a unique output directory for this SLURM job."""
    job_id = os.environ.get("SLURM_ARRAY_JOB_ID", "local")
    task_id = os.environ.get("SLURM_ARRAY_TASK_ID", "0")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = f"slurm_results/job_{job_id}/task_{task_id}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def check_gpu_availability():
    """Check if GPU is available and print its information."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"GPU available: {gpu_name}")
            return True
        else:
            print("No GPU available, falling back to CPU")
            return False
    except ImportError:
        print("PyTorch not installed, falling back to CPU")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run simulations on SLURM cluster")
    parser.add_argument(
        "--task-id", type=int, required=True, help="SLURM array task ID"
    )
    parser.add_argument(
        "--num-simulations",
        type=int,
        default=20,
        help="Number of simulations per treatment",
    )
    parser.add_argument(
        "--num-turns", type=int, default=5, help="Number of turns per simulation"
    )
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between turns")
    parser.add_argument(
        "--use-gpu", action="store_true", help="Whether to use GPU for processing"
    )

    args = parser.parse_args()

    # Check GPU availability if requested
    if args.use_gpu:
        gpu_available = check_gpu_availability()
        if gpu_available:
            # Set environment variables for GPU usage
            os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("SLURM_JOB_GPUS", "0")
            # Always use single process for GPU to avoid memory issues
            num_processes = 1
            print("Using GPU - forcing single process mode")
        else:
            print("GPU requested but not available - falling back to CPU")
            num_processes = int(os.environ.get("SLURM_CPUS_PER_TASK", "1"))
    else:
        num_processes = int(os.environ.get("SLURM_CPUS_PER_TASK", "1"))

    # Get the treatment for this task
    treatments = get_treatment_for_task(args.task_id)

    # Set up output directory
    output_dir = setup_output_directory()
    os.environ["SIMULATION_OUTPUT_DIR"] = output_dir

    print(f"Starting task {args.task_id} with treatments: {treatments}")
    print(f"Output directory: {output_dir}")
    print(f"Using {num_processes} processes")

    # Run the simulations
    results = run_parallel_simulations(
        treatments=treatments,
        num_simulations=args.num_simulations,
        num_turns=args.num_turns,
        delay=args.delay,
        num_processes=num_processes,
    )

    print(f"Task {args.task_id} complete. Results saved to {output_dir}")


if __name__ == "__main__":
    main()
