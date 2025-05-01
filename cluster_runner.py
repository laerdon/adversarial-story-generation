import argparse
from multiprocessing import Pool, cpu_count
import os
import json
from datetime import datetime
from run_simulations import TREATMENTS, INITIAL_STORY, FACTS
from agent_dialogue import simulate_dialogue


def run_single_simulation(params):
    """
    Run a single simulation with the given parameters.
    Designed to be used with multiprocessing.Pool.
    """
    treatment_key, treatment, sim_num, num_turns, delay = params

    # Create a unique identifier for this simulation
    sim_id = f"{treatment_key}_{sim_num}"

    print(f"\nStarting simulation {sim_id}")

    # Run the simulation
    sim_result = simulate_dialogue(
        num_turns=num_turns,
        delay=delay,
        author_directive=treatment["author_directive"],
        editor_directive=treatment["editor_directive"],
        initial_story=INITIAL_STORY,
        facts=FACTS,
    )

    # Add metadata
    sim_result["treatment"] = {
        "key": treatment_key,
        "name": treatment["name"],
        "author_directive": treatment["author_directive"],
        "editor_directive": treatment["editor_directive"],
    }
    sim_result["simulation_number"] = sim_num + 1

    # Save individual simulation result
    output_dir = f"simulation_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"sim_{sim_id}.json")

    with open(output_file, "w") as f:
        json.dump(sim_result, f, indent=2)

    print(f"Completed simulation {sim_id}")
    return sim_result


def run_parallel_simulations(
    treatments=None, num_simulations=3, num_turns=3, delay=0.1, num_processes=None
):
    """
    Run simulations in parallel using multiple processes.

    Args:
        treatments (list): List of treatment keys to run. If None, runs all treatments.
        num_simulations (int): Number of simulations per treatment.
        num_turns (int): Number of turns per simulation.
        delay (float): Delay between turns in seconds.
        num_processes (int): Number of processes to use. If None, uses CPU count.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"simulation_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # Save experiment metadata
    metadata = {
        "timestamp": timestamp,
        "num_simulations": num_simulations,
        "num_turns": num_turns,
        "delay": delay,
        "num_processes": num_processes or cpu_count(),
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Prepare simulation parameters
    treatments_to_run = treatments if treatments else TREATMENTS.keys()
    simulation_params = []

    for treatment_key in treatments_to_run:
        treatment = TREATMENTS[treatment_key]
        for sim_num in range(num_simulations):
            simulation_params.append(
                (treatment_key, treatment, sim_num, num_turns, delay)
            )

    # Run simulations in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.map(run_single_simulation, simulation_params)

    # Combine all results
    combined_results = {"metadata": metadata, "simulations": results}

    # Save combined results
    with open(os.path.join(output_dir, "combined_results.json"), "w") as f:
        json.dump(combined_results, f, indent=2)

    print(f"\n=== All simulations complete ===")
    print(f"Results saved to {output_dir}/")
    return combined_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run story generation simulations in parallel"
    )
    parser.add_argument("--treatments", nargs="+", help="List of treatments to run")
    parser.add_argument(
        "--num-simulations",
        type=int,
        default=3,
        help="Number of simulations per treatment",
    )
    parser.add_argument(
        "--num-turns", type=int, default=3, help="Number of turns per simulation"
    )
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between turns")
    parser.add_argument("--num-processes", type=int, help="Number of processes to use")

    args = parser.parse_args()

    results = run_parallel_simulations(
        treatments=args.treatments,
        num_simulations=args.num_simulations,
        num_turns=args.num_turns,
        delay=args.delay,
        num_processes=args.num_processes,
    )
