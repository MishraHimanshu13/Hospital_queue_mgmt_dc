# Mutex Analysis Visualization Tool

This tool provides visualizations for analyzing mutex events in the Hospital Queue Management System. It helps understand the distributed mutual exclusion algorithm's behavior, node interactions, and critical section access patterns.

## Features

The tool generates five types of visualizations:

1. **Timeline Plot**: Shows the sequence of mutex events over time, with color-coded events and connecting lines between related REQUEST and REPLY events.
2. **Event Distribution Plot**: Displays the frequency of different mutex event types.
3. **Node Interaction Plot**: A heatmap showing the number of interactions between nodes.
4. **Logical Clock Plot**: Visualizes the progression of logical clocks for each node.
5. **Critical Section Analysis**: Shows critical section access patterns and timing distributions.

## Requirements

- Python 3.6+
- Required Python packages (install using `pip install -r requirements_mutex_analysis.txt`):
  - matplotlib
  - pandas
  - numpy

## Installation

1. Clone the repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements_mutex_analysis.txt
   ```

## Usage

Run the script with:
```bash
python mutex_analysis.py [options]
```

### Options

- `--db`: Path to SQLite database (default: hospital_queue.db)
- `--output`: Directory to save output plots (if not specified, plots are displayed)
- `--plot`: Type of plot to generate (choices: timeline, distribution, interaction, clock, critical, all)

### Examples

Generate all plots and save them to a directory:
```bash
python mutex_analysis.py --output plots/
```

Generate only the timeline plot:
```bash
python mutex_analysis.py --plot timeline
```

Use a different database file:
```bash
python mutex_analysis.py --db custom_database.db
```

## Understanding the Visualizations

### Timeline Plot
- X-axis: Time
- Y-axis: Node ID
- Colors indicate different event types:
  - Red: REQUEST
  - Green: REPLY
  - Blue: CRITICAL_SECTION
  - Purple: RELEASE
  - Orange: DEFER
  - Cyan: RECEIVED_REPLY
  - Magenta: PATIENT_REGISTERED
- Dashed lines connect related REQUEST and REPLY events

### Event Distribution Plot
- X-axis: Event types
- Y-axis: Count of occurrences
- Each bar represents a different event type

### Node Interaction Plot
- Heatmap showing interactions between nodes
- Darker colors indicate more interactions
- X-axis: Target node
- Y-axis: Source node

### Logical Clock Plot
- X-axis: Time
- Y-axis: Logical clock value
- Different lines for each node
- Shows how logical clocks progress over time

### Critical Section Analysis
- Top plot: Critical section access over time
- Bottom plot: Distribution of time between critical section accesses

## Troubleshooting

1. **Database not found**: Ensure the database file exists and the path is correct
2. **No mutex logs**: Check if the database contains mutex log entries
3. **Missing dependencies**: Install required packages using pip
4. **Permission errors**: Ensure write permissions for the output directory 