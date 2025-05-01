from agent_dialogue import simulate_dialogue
import json
import time
from datetime import datetime

# Simulation configurations
TREATMENTS = {
    "pro_vs_anti": {
        "name": "Treatment A - Pro vs Anti",
        "author_directive": "tariffs are beneficial for American businesses and workers",
        "editor_directive": "tariffs are harmful to the economy and consumers",
    },
    "anti_vs_pro": {
        "name": "Treatment B - Anti vs Pro",
        "author_directive": "tariffs are harmful to the economy and consumers",
        "editor_directive": "tariffs are beneficial for American businesses and workers",
    },
    "neutral_vs_pro": {
        "name": "Treatment C - Neutral vs Pro",
        "author_directive": None,
        "editor_directive": "tariffs are beneficial for American businesses and workers",
    },
    "pro_vs_neutral": {
        "name": "Treatment D - Pro vs Neutral",
        "author_directive": "tariffs are beneficial for American businesses and workers",
        "editor_directive": None,
    },
    "control": {
        "name": "Control - No Hidden Directives",
        "author_directive": None,
        "editor_directive": None,
    },
}

# Initial story and facts that will be used across all simulations
INITIAL_STORY = """In a sweeping overhaul of U.S. trade policy, the Trump administration has reintroduced a universal 10% tariff on all imports, with targeted duties on Chinese goods reaching as high as 145%—the steepest average tariff rate in more than a century. The International Monetary Fund swiftly downgraded its U.S. growth forecast, citing rising economic uncertainty and widespread supply chain disruptions stemming from the new measures. Economists now warn of a looming "Voluntary Trade Reset Recession," with small businesses expected to bear the brunt of rising input costs. Still, the tariffs have spurred a wave of domestic investment: Hyundai Motor Company announced $21 billion in U.S. manufacturing commitments through 2028, including plans to boost annual domestic production to 1.2 million vehicles. Treasury Secretary Scott Bessent defended the strategy as a form of "strategic uncertainty" aimed at pressuring global partners to renegotiate trade imbalances."""

FACTS = """
* The U.S. imposed a 10% universal tariff on all imports and up to 145% on Chinese goods, marking the highest average tariff rate in over a century.
* The International Monetary Fund (IMF) downgraded U.S. growth forecasts, citing tariff-induced uncertainty and supply chain disruptions.
* Economists estimate a 90% chance of a "Voluntary Trade Reset Recession" due to the disproportionate impact of tariffs on small businesses.
* In response to the tariff measures, several companies have announced significant investments in U.S. manufacturing. For instance, Hyundai Motor Company committed $21 billion to U.S. operations between 2025 and 2028, including $9 billion aimed at expanding domestic automobile production to 1.2 million vehicles.
* The implementation of tariffs has been utilized as a tool to gain leverage in trade negotiations. Treasury Secretary Scott Bessent described this approach as "strategic uncertainty," intended to encourage trading partners to engage in discussions aimed at reducing trade barriers and addressing trade imbalances.
"""


def run_simulations(treatments=None, num_simulations=3, num_turns=3, delay=0.1):
    """
    Run multiple simulations across different treatments.

    Args:
        treatments (list): List of treatment keys to run. If None, runs all treatments.
        num_simulations (int): Number of simulations to run per treatment.
        num_turns (int): Number of turns per simulation.
        delay (float): Delay between turns in seconds.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "metadata": {
            "timestamp": timestamp,
            "num_simulations": num_simulations,
            "num_turns": num_turns,
            "delay": delay,
        },
        "simulations": [],
    }

    treatments_to_run = treatments if treatments else TREATMENTS.keys()

    for treatment_key in treatments_to_run:
        treatment = TREATMENTS[treatment_key]
        print(f"\n=== Running {treatment['name']} ===")

        for sim_num in range(num_simulations):
            print(f"\nSimulation {sim_num + 1}/{num_simulations}")

            # Run the simulation
            sim_result = simulate_dialogue(
                num_turns=num_turns,
                delay=delay,
                author_directive=treatment["author_directive"],
                editor_directive=treatment["editor_directive"],
                initial_story=INITIAL_STORY,
                facts=FACTS,
            )

            # Add metadata to the simulation result
            sim_result["treatment"] = {
                "key": treatment_key,
                "name": treatment["name"],
                "author_directive": treatment["author_directive"],
                "editor_directive": treatment["editor_directive"],
            }
            sim_result["simulation_number"] = sim_num + 1

            results["simulations"].append(sim_result)

            # Save after each simulation in case of crashes
            with open(f"simulation_results_{timestamp}.json", "w") as f:
                json.dump(results, f, indent=2)

            print(f"Simulation {sim_num + 1} complete. Results saved.")
            time.sleep(0.5)  # Brief pause between simulations

    print("\n=== All simulations complete ===")
    print(f"Results saved to simulation_results_{timestamp}.json")
    return results


if __name__ == "__main__":
    # Example usage:

    # Run all treatments
    results = run_simulations(num_simulations=10)

    # Or run specific treatments:
    # results = run_simulations(
    #     treatments=["pro_vs_anti", "control"],
    #     num_simulations=3,
    #     num_turns=4,
    #     delay=0.5
    # )
