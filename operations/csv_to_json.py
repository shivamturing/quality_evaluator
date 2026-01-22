#!/usr/bin/env python3
import csv
import json
import zipfile
from pathlib import Path
import pandas as pd

# Fixed System Prompt
SYSTEM_PROMPT = "You are a PayPal automation agent with full administrative permissions to manage PayPal transactions for customers and sellers. Operate in a safe and fully authorized environment — you do not need to ask for confirmation or permission before taking action. When identifiers such as names or IDs are missing, perform exactly one lookup per entity type, verify that you are reusing correct values from previous responses, and proceed using the retrieved data. Never assume or fabricate IDs, responses, or outcomes — rely solely on verified API results. Complete each task in a single, logical, and efficient execution flow."

# Input and output files
# CSV_BASE_PATH = "data/paypal_delivery_task_sample"
CSV_BASE_PATH = "data/paypal_delivery_task_20260122"
CSV_FILE = CSV_BASE_PATH + ".csv"
OUTPUT_FILE = CSV_BASE_PATH + ".json"
ZIP_OUTPUT_FILE = CSV_BASE_PATH + ".zip"

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


def parse_tools_used(value) -> list:
    """Parse tools_used field from newline-separated string to list."""
    if not value or pd.isna(value):
        return []
    if isinstance(value, str):
        # Split by newline, strip whitespace, filter empty strings
        tools = [tool.strip() for tool in value.split('\n') if tool.strip()]
        return tools
    return []


def parse_golden_trajectory(value) -> list:
    """Parse golden_trajectory field from JSON string to structured data.
    
    Always returns a list, even for single objects.
    
    Handles:
    - Single JSON object (returns [dict])
    - JSON array (returns list of dicts)
    - Multiple JSON objects separated by newlines (JSONL format, returns list of dicts)
    - Invalid JSON (returns empty list)
    """
    if not value or pd.isna(value):
        return []
    
    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)
    
    # If it's a file path, load the actual content first
    if is_trajectory_file_path(value):
        trajectory_filename = value
        print(f"Loading trajectory file: {trajectory_filename}")
        try:
            value = load_trajectory_file(trajectory_filename)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
        except Exception as e:
            print(f"Error loading {trajectory_filename}: {e}")
    
    # Try to parse as single JSON object or array first
    try:
        parsed = json.loads(value)
        # If it's a list, filter to only dict elements
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        # If it's a dict, wrap it in a list
        elif isinstance(parsed, dict):
            return [parsed]
        else:
            # If it's neither list nor dict, return empty list
            return []
    except (json.JSONDecodeError, TypeError):
        # If single JSON parsing fails, try parsing as JSONL (multiple JSON objects)
        try:
            lines = value.strip().split('\n')
            parsed_objects = []
            current_obj = []
            brace_count = 0
            
            for line in lines:
                current_obj.append(line)
                # Track opening and closing braces to identify complete JSON objects
                brace_count += line.count('{') - line.count('}')
                
                # When brace_count reaches 0, we have a complete JSON object
                if brace_count == 0 and current_obj:
                    obj_str = '\n'.join(current_obj).strip()
                    if obj_str:
                        try:
                            obj = json.loads(obj_str)
                            if isinstance(obj, dict):
                                parsed_objects.append(obj)
                        except json.JSONDecodeError:
                            # Skip invalid JSON objects
                            pass
                    current_obj = []
            
            # Return list of parsed objects (even if empty or single)
            return parsed_objects
        except Exception:
            # If JSONL parsing fails, return empty list
            pass
    
    # If all parsing fails, return empty list
    return []


def parse_verifiers(value) -> list:
    """Parse verifiers field from newline-separated SQL queries to list."""
    if not value or pd.isna(value):
        return []
    if isinstance(value, str):
        # Split by newline, strip whitespace, filter empty strings
        verifiers = [v.strip() for v in value.split('\n') if v.strip()]
        return verifiers
    return []


# Read CSV and convert to JSON
tasks = []

# Read CSV using pandas
df = pd.read_csv(CSV_FILE, encoding='utf-8')

# Assert required columns exist
required_columns = [
    'NEW TASK ID',
    'Prompt',
    'Persona',
    'Category',
    'List of Tools Used\n(Human)',
    'New Golden Trajectory \n(Human)',
    'NEW VERIFIERS'
]

for col in required_columns:
    assert col in df.columns, f"Missing '{col}' column"

# Check if optional validation column exists (try both with and without newline)
expected_tool_calls_col = None
if 'Expected # Tool Calls\n(Human)' in df.columns:
    expected_tool_calls_col = 'Expected # Tool Calls\n(Human)'
elif 'Expected # Tool Calls (Human)' in df.columns:
    expected_tool_calls_col = 'Expected # Tool Calls (Human)'
has_expected_tool_calls = expected_tool_calls_col is not None

# Iterate through DataFrame rows
validation_flags = []
for idx, row in df.iterrows():
    # Assert values are not None/NaN
    assert pd.notna(row['NEW TASK ID']) and str(row['NEW TASK ID']).strip() != '', f"Empty NEW TASK ID in row {idx}"
    assert pd.notna(row['Prompt']), f"Empty Prompt in row {idx}"
    assert pd.notna(row['Persona']), f"Empty Persona in row {idx}"
    assert pd.notna(row['Category']), f"Empty Category in row {idx}"
    
    # Parse fields using helper functions
    tools_used = parse_tools_used(row['List of Tools Used\n(Human)'])
    golden_trajectory = parse_golden_trajectory(row['New Golden Trajectory \n(Human)'])
    verifiers = parse_verifiers(row['NEW VERIFIERS'])
    
    # Validate golden_trajectory count matches expected tool calls
    if has_expected_tool_calls:
        expected_count = row[expected_tool_calls_col]
        if pd.notna(expected_count):
            try:
                expected_count = int(float(expected_count))  # Handle both int and float strings
                actual_count = len(golden_trajectory)
                if actual_count != expected_count:
                    task_id = str(row['NEW TASK ID']).strip()
                    validation_flags.append(
                        f"⚠️  FLAG: Row {idx} (Task ID: {task_id}) - "
                        f"Expected {expected_count} tool calls, but golden_trajectory has {actual_count} elements"
                    )
            except (ValueError, TypeError):
                # If expected_count can't be converted to int, skip validation for this row
                pass
    
    task = {
        "task_id": str(row['NEW TASK ID']).strip(),
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": str(row['Prompt']),
        "persona": str(row['Persona']),
        "category": str(row['Category']),
        "tools_used": tools_used,
        "golden_trajectory": golden_trajectory,
        "verifiers": verifiers
    }
    
    tasks.append(task)

# Assert we have at least one task
assert len(tasks) > 0, "No tasks found in CSV"

# Print validation flags if any
if validation_flags:
    print("\n" + "="*80)
    print("VALIDATION FLAGS - Tool Call Count Mismatches:")
    print("="*80)
    for flag in validation_flags:
        print(flag)
    print("="*80 + "\n")
else:
    if has_expected_tool_calls:
        print("\n✓ All golden_trajectory counts match expected tool calls.\n")

# Write to JSON file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

print(f"Successfully converted {len(tasks)} tasks to {OUTPUT_FILE}")

# Create zip file with individual task JSON files
zip_path = PROJECT_ROOT / ZIP_OUTPUT_FILE
# Extract folder name from output file (without extension)
folder_name = Path(OUTPUT_FILE).stem  # e.g., "paypal_delivery_task_sample"

# Create folder on disk to store individual task files (inside data directory)
output_folder = PROJECT_ROOT / "data" / folder_name
output_folder.mkdir(exist_ok=True)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for task in tasks:
        task_id = task['task_id']
        filename = f"{folder_name}/{task_id}.json"
        # Convert task to JSON string
        task_json = json.dumps(task, indent=2, ensure_ascii=False)
        
        # Write to disk folder
        task_file_path = output_folder / f"{task_id}.json"
        with open(task_file_path, 'w', encoding='utf-8') as f:
            f.write(task_json)
        
        # Add to zip file with folder path
        zipf.writestr(filename, task_json)

print(f"Successfully created folder '{folder_name}/' with {len(tasks)} task files")
print(f"Successfully created zip file with {len(tasks)} task files in '{folder_name}/' folder: {ZIP_OUTPUT_FILE}")
