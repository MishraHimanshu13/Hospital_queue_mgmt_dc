# Mutex Analysis Visualization Tool

This tool analyzes mutex logs from the Hospital Queue Management System and generates visualizations to help understand the distributed mutual exclusion events.

## Features

The tool generates five different types of visualizations:

1. **Timeline Plot**: Shows the sequence of mutex events over time, with different colors for different event types.
2. **Event Distribution Plot**: Displays the frequency of different mutex event types.
3. **Node Interaction Plot**: Visualizes the interactions between different nodes in the system.
4. **Logical Clock Plot**: Shows the progression of logical clocks for each node.
5. **Critical Section Analysis**: Analyzes patterns of critical section access.

## Requirements

- Python 3.6+
- Required Python packages (install using `pip install -r requirements_mutex_analysis.txt`):
  - matplotlib
  - pandas
  - numpy

## Installation

1. Clone the repository or download the script files.
2. Install the required dependencies:
   ```
   pip install -r requirements_mutex_analysis.txt
   ```

## Usage

Run the script with the following command:

```
python mutex_analysis.py [options]
```

### Options

- `--db PATH`: Path to the SQLite database (default: hospital_queue.db)
- `--output DIR`: Directory to save output plots (default: display plots)
- `--plot TYPE`: Type of plot to generate (choices: timeline, distribution, interaction, clock, critical, all; default: all)

### Examples

Generate all plots and display them:
```
python mutex_analysis.py
```

Generate only the timeline plot and save it to a file:
```
python mutex_analysis.py --plot timeline --output ./plots
```

Generate all plots and save them to a directory:
```
python mutex_analysis.py --output ./plots
```

Use a different database file:
```
python mutex_analysis.py --db /path/to/your/database.db
```

## Understanding the Visualizations

### Timeline Plot
- X-axis: Time
- Y-axis: Node ID
- Different colors represent different event types
- Dashed lines connect related REQUEST and REPLY events

### Event Distribution Plot
- X-axis: Event types
- Y-axis: Count of occurrences
- Different colors for different event types

### Node Interaction Plot
- Heatmap showing interactions between nodes
- Rows: Source nodes
- Columns: Target nodes
- Color intensity: Number of interactions

### Logical Clock Plot
- X-axis: Time
- Y-axis: Logical clock value
- Different lines for different nodes

### Critical Section Analysis
- Top plot: Critical section access over time
- Bottom plot: Histogram of time between critical section accesses

## Troubleshooting

If you encounter any issues:

1. Ensure the database file exists and is accessible
2. Check that the mutex_logs table exists in the database
3. Verify that all required dependencies are installed
4. Make sure you have write permissions if saving plots to a directory 