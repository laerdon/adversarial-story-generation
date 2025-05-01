import os
import json
import glob
from datetime import datetime


def collect_results(slurm_results_dir="slurm_results"):
    """
    Collect and combine results from all SLURM jobs into a single file.
    """
    # Create output directory for combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"combined_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # Find all job directories
    job_dirs = glob.glob(os.path.join(slurm_results_dir, "job_*"))

    all_results = {
        "metadata": {"collection_timestamp": timestamp, "num_jobs": len(job_dirs)},
        "simulations": [],
    }

    # Collect results from each job
    for job_dir in job_dirs:
        # Find all task directories in this job
        task_dirs = glob.glob(os.path.join(job_dir, "task_*"))

        for task_dir in task_dirs:
            # Find the combined results file
            combined_file = os.path.join(task_dir, "combined_results.json")
            if os.path.exists(combined_file):
                with open(combined_file, "r") as f:
                    task_results = json.load(f)
                    all_results["simulations"].extend(task_results["simulations"])

    # Add summary statistics
    all_results["summary"] = {
        "total_simulations": len(all_results["simulations"]),
        "treatments": {},
    }

    # Count simulations per treatment
    for sim in all_results["simulations"]:
        treatment_key = sim["treatment"]["key"]
        if treatment_key not in all_results["summary"]["treatments"]:
            all_results["summary"]["treatments"][treatment_key] = 0
        all_results["summary"]["treatments"][treatment_key] += 1

    # Save combined results
    output_file = os.path.join(output_dir, "all_results.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n=== Results Collection Complete ===")
    print(f"Total simulations: {all_results['summary']['total_simulations']}")
    print(f"Results saved to: {output_file}")
    print("\nSimulations per treatment:")
    for treatment, count in all_results["summary"]["treatments"].items():
        print(f"  {treatment}: {count}")


if __name__ == "__main__":
    collect_results()
