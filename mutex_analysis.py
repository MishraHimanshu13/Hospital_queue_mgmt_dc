#!/usr/bin/env python3
"""
Mutex Analysis Visualization Tool

This script analyzes mutex logs from the hospital queue management system
and generates visualizations to help understand the distributed mutual exclusion events.
"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import numpy as np
import os
import argparse
from collections import defaultdict

# Default database path
DEFAULT_DB_PATH = 'hospital_queue.db'

def connect_to_db(db_path):
    """Connect to the SQLite database and return the connection."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        exit(1)

def get_mutex_logs(conn):
    """Retrieve mutex logs from the database."""
    try:
        query = """
        SELECT id, node_id, event, timestamp, target_node, created_at
        FROM mutex_logs
        ORDER BY created_at ASC
        """
        return pd.read_sql_query(query, conn)
    except sqlite3.Error as e:
        print(f"Error retrieving mutex logs: {e}")
        exit(1)

def create_timeline_plot(logs):
    """Create a timeline plot of mutex events."""
    plt.figure(figsize=(12, 6))
    
    # Define colors for different event types
    event_colors = {
        'REQUEST': 'red',
        'REPLY': 'green',
        'CRITICAL_SECTION': 'blue',
        'RELEASE': 'purple',
        'DEFER': 'orange',
        'RECEIVED_REPLY': 'cyan',
        'PATIENT_REGISTERED': 'magenta'
    }
    
    # Plot events
    for event_type in event_colors:
        mask = logs['event'] == event_type
        if mask.any():
            plt.scatter(logs[mask]['created_at'], logs[mask]['node_id'],
                       c=event_colors[event_type], label=event_type, alpha=0.6)
    
    # Connect REQUEST and REPLY events with dashed lines
    for _, request in logs[logs['event'] == 'REQUEST'].iterrows():
        replies = logs[(logs['event'] == 'REPLY') & 
                      (logs['target_node'] == request['node_id'])]
        for _, reply in replies.iterrows():
            plt.plot([request['created_at'], reply['created_at']],
                    [request['node_id'], reply['node_id']],
                    'k--', alpha=0.3)
    
    plt.xlabel('Time')
    plt.ylabel('Node ID')
    plt.title('Mutex Events Timeline')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return plt.gcf()

def create_distribution_plot(logs):
    """Create a plot showing the distribution of event types."""
    plt.figure(figsize=(10, 6))
    
    event_counts = logs['event'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(event_counts)))
    
    plt.bar(event_counts.index, event_counts.values, color=colors)
    plt.xlabel('Event Type')
    plt.ylabel('Count')
    plt.title('Distribution of Mutex Events')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return plt.gcf()

def create_interaction_plot(logs):
    """Create a heatmap showing node interactions."""
    plt.figure(figsize=(10, 8))
    
    # Create interaction matrix
    nodes = sorted(set(logs['node_id'].unique()) | set(logs['target_node'].dropna().unique()))
    interaction_matrix = pd.DataFrame(0, index=nodes, columns=nodes)
    
    # Count interactions
    for _, row in logs.iterrows():
        if pd.notna(row['target_node']):
            interaction_matrix.loc[row['node_id'], row['target_node']] += 1
    
    plt.imshow(interaction_matrix, cmap='YlOrRd')
    plt.colorbar(label='Number of Interactions')
    plt.xlabel('Target Node')
    plt.ylabel('Source Node')
    plt.title('Node Interaction Heatmap')
    plt.xticks(range(len(nodes)), nodes)
    plt.yticks(range(len(nodes)), nodes)
    plt.tight_layout()
    return plt.gcf()

def create_clock_plot(logs):
    """Create a plot showing logical clock progression."""
    plt.figure(figsize=(12, 6))
    
    for node in logs['node_id'].unique():
        node_logs = logs[logs['node_id'] == node]
        plt.plot(node_logs['created_at'], node_logs['timestamp'],
                label=f'Node {node}', marker='o', markersize=4)
    
    plt.xlabel('Time')
    plt.ylabel('Logical Clock Value')
    plt.title('Logical Clock Progression')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return plt.gcf()

def create_critical_section_plot(logs):
    """Create plots analyzing critical section access patterns."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot critical section access over time
    cs_logs = logs[logs['event'] == 'CRITICAL_SECTION']
    ax1.scatter(cs_logs['created_at'], cs_logs['node_id'],
               c='blue', alpha=0.6)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Node ID')
    ax1.set_title('Critical Section Access Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Plot histogram of time between critical section accesses
    if len(cs_logs) > 1:
        time_diffs = cs_logs['created_at'].diff().dropna()
        ax2.hist(time_diffs, bins=30, color='blue', alpha=0.6)
        ax2.set_xlabel('Time Between Critical Section Accesses')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Distribution of Time Between Critical Section Accesses')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analyze mutex logs and generate visualizations')
    parser.add_argument('--db', default='hospital_queue.db',
                      help='Path to SQLite database (default: hospital_queue.db)')
    parser.add_argument('--output', help='Directory to save output plots')
    parser.add_argument('--plot', choices=['timeline', 'distribution', 'interaction',
                                         'clock', 'critical', 'all'],
                      default='all', help='Type of plot to generate')
    
    args = parser.parse_args()
    
    # Connect to database and get logs
    conn = connect_to_db(args.db)
    logs = get_mutex_logs(conn)
    conn.close()
    
    # Convert timestamps to datetime
    logs['created_at'] = pd.to_datetime(logs['created_at'])
    
    # Generate plots
    plots = {}
    if args.plot in ['timeline', 'all']:
        plots['timeline'] = create_timeline_plot(logs)
    if args.plot in ['distribution', 'all']:
        plots['distribution'] = create_distribution_plot(logs)
    if args.plot in ['interaction', 'all']:
        plots['interaction'] = create_interaction_plot(logs)
    if args.plot in ['clock', 'all']:
        plots['clock'] = create_clock_plot(logs)
    if args.plot in ['critical', 'all']:
        plots['critical'] = create_critical_section_plot(logs)
    
    # Save or display plots
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        for name, fig in plots.items():
            fig.savefig(os.path.join(args.output, f'mutex_{name}.png'))
        print(f"Plots saved to {args.output}")
    else:
        plt.show()

if __name__ == '__main__':
    main() 