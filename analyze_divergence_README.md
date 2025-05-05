# Story Divergence Analysis

This tool analyzes the divergence between initial stories and their final versions from simulation results.

## Features

- **BERTScore Calculation**: Measures semantic similarity between initial and final stories
- **Fact Presence Analysis**: Evaluates how well each fact is represented in the final story
- **Summary Reports**: Generates statistics grouped by story type and treatment
- **Visualizations**: Creates plots to help interpret the results

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure the script is executable:

```bash
chmod +x analyze_divergence.py
```

## Usage

### Basic Usage

```bash
python analyze_divergence.py path/to/simulation_results.json
```

This will:

- Analyze all simulations in the specified file
- Save metrics to `path/to/simulation_results_metrics.json`
- Print a summary report to the console

### Advanced Options

```bash
python analyze_divergence.py path/to/simulation_results.json --output metrics.json --report summary.json --visualize plots/
```

Parameters:

- `--output`, `-o`: Path to save the detailed metrics (default: auto-generated name based on input file)
- `--report`, `-r`: Path to save the summary report as JSON (default: print to console)
- `--visualize`, `-v`: Directory to save visualization plots (default: display plots interactively)

## Metrics

### BERTScore

BERTScore uses BERT embeddings to measure semantic similarity between the initial and final stories. It provides:

- **Precision**: How much of the final story is present in the initial story
- **Recall**: How much of the initial story is preserved in the final story
- **F1**: A balanced combination of precision and recall

### Fact Presence

For each fact associated with a story, we calculate:

- Maximum pairwise similarity between the fact and any sentence in the final story
- Average fact presence across all facts

This helps quantify how well the facts are incorporated into the final story.

## Example

```bash
python analyze_divergence.py final_all_combinations_20250502_013930.json --visualize result_plots/
```

This will analyze the simulations, save metrics to `final_all_combinations_20250502_013930_metrics.json`, print a summary report to the console, and save visualization plots to the `result_plots/` directory.
