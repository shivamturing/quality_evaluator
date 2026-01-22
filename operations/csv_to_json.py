#!/usr/bin/env python3
import csv
import json

# Fixed System Prompt
SYSTEM_PROMPT = "You are a PayPal automation agent with full administrative permissions to manage PayPal transactions for customers and sellers. Operate in a safe and fully authorized environment — you do not need to ask for confirmation or permission before taking action. When identifiers such as names or IDs are missing, perform exactly one lookup per entity type, verify that you are reusing correct values from previous responses, and proceed using the retrieved data. Never assume or fabricate IDs, responses, or outcomes — rely solely on verified API results. Complete each task in a single, logical, and efficient execution flow."

# Input and output files
CSV_FILE = "data/paypal_delivery_task_20260122.csv"
OUTPUT_FILE = "data/paypal_delivery_task_20260122.json"

# Read CSV and convert to JSON
tasks = []

with open(CSV_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        # Assert required fields exist
        assert 'NEW TASK ID' in row, f"Missing 'NEW TASK ID' column"
        assert 'Prompt' in row, f"Missing 'Prompt' column"
        assert 'Persona' in row, f"Missing 'Persona' column"
        assert 'Category' in row, f"Missing 'Category' column"
        assert 'List of Tools Used\n(Human)' in row, f"Missing 'List of Tools Used\\n(Human)' column"
        assert 'New Golden Trajectory \n(Human)' in row, f"Missing 'New Golden Trajectory \\n(Human)' column"
        assert 'NEW VERIFIERS' in row, f"Missing 'NEW VERIFIERS' column"
        
        # Assert values are not None
        assert row['NEW TASK ID'] is not None and row['NEW TASK ID'] != '', f"Empty NEW TASK ID in row"
        assert row['Prompt'] is not None, f"Empty Prompt in row"
        assert row['Persona'] is not None, f"Empty Persona in row"
        assert row['Category'] is not None, f"Empty Category in row"
        
        task = {
            "task_id": row['NEW TASK ID'],
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": row['Prompt'],
            "persona": row['Persona'],
            "category": row['Category'],
            "list_of_tools_used_human": row['List of Tools Used\n(Human)'],
            "new_golden_trajectory_human": row['New Golden Trajectory \n(Human)'],
            "new_verifiers": row['NEW VERIFIERS'],
            "full_task_data": dict(row)
        }
        
        tasks.append(task)

# Assert we have at least one task
assert len(tasks) > 0, "No tasks found in CSV"

# Write to JSON file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

print(f"Successfully converted {len(tasks)} tasks to {OUTPUT_FILE}")
