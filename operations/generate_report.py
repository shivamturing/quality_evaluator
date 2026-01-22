import pandas as pd
import json
from collections import defaultdict
import os
import shutil
import re
from pathlib import Path

# Get project root directory (parent of operations directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TRAJECTORY_DIR = PROJECT_ROOT / "data" / "trajectories"


def is_trajectory_file_path(value: str) -> bool:
    """Check if the value is a trajectory file path (ends with .json and doesn't start with { or [)."""
    if not isinstance(value, str):
        return False
    
    # Check if it's a filename (ends with .json) and doesn't look like JSON content
    return value.endswith('.json') and not value.strip().startswith(('{', '['))


def load_trajectory_file(filename: str) -> str:
    """Load trajectory file content as text from data/trajectories/ directory."""
    file_path = TRAJECTORY_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_tool_names_from_trajectory(golden_trajectory_str: str) -> list:
    """
    Extract all tool names from golden_trajectory JSON string using regex.
    
    Args:
        golden_trajectory_str: JSON string containing tool calls
        
    Returns:
        List of tool names in order of appearance
    """
    if not golden_trajectory_str or not isinstance(golden_trajectory_str, str):
        return []
    
    # Regex pattern to match "tool_name": "tool_name_value"
    pattern = r'"tool_name"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, golden_trajectory_str)
    
    return matches


def get_diversity_report(tasks):
    """
    Generate diversity report from CSV-loaded tasks.
    All tasks are sequential, so we only track sequential patterns.
    
    Args:
        tasks: List of task dicts with 'task_id' and 'golden_trajectory' fields
    
    Returns:
        Tuple of (total_tool_analysis, task_specific_tool_analysis, individual_tool_counts, task_data)
    """
    # Initialize tracking dictionaries
    sequential_counts = defaultdict(lambda: {'count': 0, 'task_ids': []})
    individual_tool_counts = defaultdict(int)  # Count individual tool calls
    task_data_rows = []  # Store task-level data

    for task in tasks:
        task_id = task.get('task_id', '')
        golden_trajectory = task.get('golden_trajectory', '')
        
        # Ensure golden_trajectory is a JSON string
        if isinstance(golden_trajectory, (list, dict)):
            golden_trajectory_str = json.dumps(golden_trajectory)
        else:
            golden_trajectory_str = str(golden_trajectory) if golden_trajectory else ''
        
        # Extract all tool names using regex
        tool_names = extract_tool_names_from_trajectory(golden_trajectory_str)
        
        if tool_names:
            # Count individual tool calls
            for tool_name in tool_names:
                individual_tool_counts[tool_name] += 1
            
            # Since all tasks are sequential, create pattern as ' > '.join(tool_names)
            pattern = ' > '.join(tool_names)
            print('Debugging: ', task_id, pattern)
            sequential_counts[pattern]['count'] += 1
            sequential_counts[pattern]['task_ids'].append(task_id)
            
            # Add to task data
            task_data_rows.append({
                'Task ID': task_id,
                'Sequential Call': pattern,
                'Number of Call': len(tool_names)
            })
        else:
            # Task with no tool calls
            task_data_rows.append({
                'Task ID': task_id,
                'Sequential Call': '',
                'Number of Call': 0
            })

    # Build DF1: Combined view with Call Type (all sequential)
    df1_rows = []
    for pattern, data in sequential_counts.items():
        df1_rows.append({
            'Tool Call': pattern,
            'Call Type': 'sequential',
            'Count': data['count']
        })

    total_tool_analysis = pd.DataFrame(df1_rows).sort_values('Count', ascending=False).reset_index(drop=True)

    # Build DF2: Sequential patterns with task IDs
    df2_rows = []
    for pattern, data in sequential_counts.items():
        df2_rows.append({
            'Sequential Call': pattern,
            'Count': data['count'],
            'Task IDs': ', '.join(set(data['task_ids']))  # Use set to dedupe if same task has multiple occurrences
        })

    task_specific_tool_analysis = pd.DataFrame(df2_rows).sort_values('Count', ascending=False).reset_index(drop=True)

    # Build DF3: Individual tool call counts
    df3_rows = []
    for tool_name, count in sorted(individual_tool_counts.items(), key=lambda x: x[1], reverse=True):
        df3_rows.append({
            'Tool Name': tool_name,
            'Count': count
        })

    individual_tool_analysis = pd.DataFrame(df3_rows).reset_index(drop=True)

    # Build DF4: Task-level data
    task_data_df = pd.DataFrame(task_data_rows).reset_index(drop=True)

    return total_tool_analysis, task_specific_tool_analysis, individual_tool_analysis, task_data_df


def generate_excel_report(csv_file=None, tasks_folder=None, output_excel_file=None):
    """
    Generate diversity report Excel file from CSV file or tasks folder.
    
    Args:
        csv_file: Path to CSV file (preferred, loads tasks from CSV)
        tasks_folder: Path to folder with individual task JSON files (fallback)
        output_excel_file: Path to output Excel file
    """
    tasks = []
    
    # Load tasks from CSV if provided, otherwise fall back to tasks_folder
    if csv_file:
        # Load tasks from CSV file
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # Check required columns
        required_columns = [
            'NEW TASK ID',
            'New Golden Trajectory \n(Human)'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: '{col}'")
        
        # Process each row
        for idx, row in df.iterrows():
            task_id = str(row['NEW TASK ID']).strip()
            golden_trajectory_raw = row['New Golden Trajectory \n(Human)']
            
            # Handle trajectory file loading
            if pd.notna(golden_trajectory_raw):
                golden_trajectory_value = str(golden_trajectory_raw)
                
                # Check if it's a file path and load it
                if is_trajectory_file_path(golden_trajectory_value):
                    try:
                        golden_trajectory_str = load_trajectory_file(golden_trajectory_value)
                    except FileNotFoundError as e:
                        print(f"Warning: {e}")
                        golden_trajectory_str = golden_trajectory_value
                    except Exception as e:
                        print(f"Error loading trajectory file {golden_trajectory_value}: {e}")
                        golden_trajectory_str = golden_trajectory_value
                else:
                    # Use value as-is (may be JSON string)
                    golden_trajectory_str = golden_trajectory_value
            else:
                golden_trajectory_str = ''
            
            task = {
                'task_id': task_id,
                'golden_trajectory': golden_trajectory_str
            }
            tasks.append(task)
    elif tasks_folder:
        # Fallback: load from individual JSON files
        tasks_files = [i for i in os.listdir(tasks_folder) if '.json' in i]
        for task_file in tasks_files:
            with open(os.path.join(tasks_folder, task_file), 'r') as f:
                task_data = json.load(f)
                # Convert to format expected by get_diversity_report
                task = {
                    'task_id': task_data.get('task_id', ''),
                    'golden_trajectory': json.dumps(task_data.get('golden_trajectory', []))
                }
                tasks.append(task)
    else:
        raise ValueError("Either csv_file or tasks_folder must be provided")
    
    all_diversity_report, task_specific_diversity_report, individual_tool_counts_df, task_data_df = get_diversity_report(tasks)
    
    # Calculate summary metrics
    total_tasks = len(tasks)
    # Count total calls: sum all individual tool call counts
    total_calls = int(individual_tool_counts_df['Count'].sum()) if not individual_tool_counts_df.empty else 0
    # Count distinct tools: number of unique tools
    distinct_tools = len(individual_tool_counts_df)
    # Calculate average: total calls divided by total tasks (tasks with 0 calls are included in denominator)
    average_calls_per_task = round(total_calls / total_tasks, 2) if total_tasks > 0 else 0.0
    
    # Create summary DataFrame
    summary_data = {
        'Metric': [
            'Total number of tasks',
            'Total number of calls',
            'Distinct number of tools used',
            'Average calls per task'
        ],
        'Value': [
            total_tasks,
            total_calls,
            distinct_tools,
            average_calls_per_task
        ]
    }
    summary_df = pd.DataFrame(summary_data)

    with pd.ExcelWriter(output_excel_file, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        all_diversity_report.to_excel(writer, sheet_name='Diversity Report', index=False)
        task_specific_diversity_report.to_excel(writer, sheet_name='Task Specific Diversity Report', index=False)
        individual_tool_counts_df.to_excel(writer, sheet_name='Individual Tool Counts', index=False)
        task_data_df.to_excel(writer, sheet_name='Task Data', index=False)


if __name__ == '__main__':
    csv_file = 'data/paypal_delivery_task_20260122.csv'  # CSV file path
    # tasks_folder = 'data/'  # Alternative: use tasks_folder if CSV not available
    output_excel_file = 'diversity_report.xlsx'
    generate_excel_report(csv_file=csv_file, output_excel_file=output_excel_file)
