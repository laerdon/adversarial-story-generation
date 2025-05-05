# Metrics Compilation and Analysis Tool

This tool compiles and analyzes metrics from simulation results, providing detailed breakdowns by treatment, story topic, and individual facts.

## Features

- **BERTScore Analysis**: Comprehensive analysis of BERTScore metrics (precision, recall, F1) across treatments and story topics
- **Fact Presence Analysis**: Detailed examination of how well each fact is represented in the final stories
- **Cross-sectional Analysis**: View metrics across different combinations of treatments and story topics
- **Multiple Visualizations**: Heatmaps, bar charts, and scatter plots to help interpret the results

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure the script is executable:

```bash
chmod +x compile_raw_metrics.py
```

## Usage

```bash
python compile_raw_metrics.py path/to/metrics.json --output results/
```

Parameters:

- `metrics_file`: Path to the metrics JSON file (required)
- `--output`, `-o`: Directory to save the compiled results (optional, will print to console if not specified)

## Output Files

When run with an output directory, the script generates several files:

### CSV Summary Files

- **overall_metrics.csv**: All metrics for each simulation
- **bertscore_by_treatment.csv**: BERTScore metrics aggregated by treatment
- **bertscore_by_story.csv**: BERTScore metrics aggregated by story topic
- **bertscore_by_treatment_story.csv**: BERTScore metrics cross-tabulated by treatment and story
- **story_fact_summary.csv**: Fact presence aggregated by story and fact
- **treatment_fact_summary.csv**: Fact presence aggregated by treatment and fact
- **full_summary.csv**: Fact presence cross-tabulated by story, treatment, and fact

### Visualizations

- **bertscore_heatmap.png**: Heatmap of BERTScore F1 by story and treatment
- **bertscore_precision_heatmap.png**: Heatmap of BERTScore precision by story and treatment
- **bertscore_recall_heatmap.png**: Heatmap of BERTScore recall by story and treatment
- **bertscore_by_treatment.png**: Bar chart comparing precision, recall, and F1 across treatments
- **bertscore_by_story.png**: Bar chart comparing precision, recall, and F1 across story topics
- **bertscore_vs_fact_presence.png**: Scatter plot showing relationship between BERTScore and fact presence
- **fact_heatmap.png**: Heatmap of fact presence by story, fact, and treatment
- **fact*bars*[story].png**: Bar charts of fact presence for each story topic

### Text Report

- **metrics_summary_report.txt**: Human-readable report summarizing key findings, including:
  - BERTScore statistics by treatment and story
  - Fact presence statistics by treatment and story
  - Top and bottom treatments for fact preservation
  - Detailed breakdown of each fact's presence by treatment and story

## Example

```bash
python compile_raw_metrics.py final_all_combinations_20250502_013930_metrics.json --output metrics_analysis/
```

This will analyze the metrics file and save all outputs to the `metrics_analysis/` directory.

## Interpreting the Results

### BERTScore Metrics

- **Precision**: How much of the final story is semantically present in the initial story
- **Recall**: How much of the initial story is semantically preserved in the final story
- **F1**: Balanced combination of precision and recall

Higher values indicate closer semantic similarity between initial and final stories.

### Fact Presence

Measures how well each fact from the original set is represented in the final story.
Higher values indicate the fact is better preserved or emphasized in the final story.
