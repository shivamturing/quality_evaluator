#!/usr/bin/env python3
"""
Batch Evaluation Script for RL Tool Use Data Generation Tasks
Processes tasks from a JSON file and runs quality evaluations on all tasks.
"""
import sys
import os
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from quality_evaluator import QualityEvaluator
from config import QUALITY_DIMENSIONS, THREADS_PER_TASK

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_tools_list(tools_str: str) -> List[str]:
    """Parse comma or newline-separated tools list into a list."""
    if not tools_str:
        return []
    
    # Split by comma or newline, strip whitespace, filter empty strings
    tools = []
    for tool in tools_str.replace('\n', ',').split(','):
        tool = tool.strip()
        if tool:
            tools.append(tool)
    return tools


def parse_golden_trajectory(trajectory_str: str) -> List[Dict[str, Any]]:
    """Parse the new_golden_trajectory_human JSON string into a list of tool objects.
    
    The trajectory can be:
    1. A single JSON object (one tool call)
    2. Multiple JSON objects separated by newlines (multiple tool calls)
    3. A JSON string that needs to be parsed
    """
    if not trajectory_str:
        return []
    
    tools = []
    try:
        # Try parsing as a single JSON object first
        try:
            tool_obj = json.loads(trajectory_str)
            # Check if it's a tool object (has 'name' field) or a result object (has 'tool_name')
            if 'name' in tool_obj or 'tool_name' in tool_obj:
                tools.append(tool_obj)
                return tools
        except json.JSONDecodeError:
            pass
        
        # Try splitting by newlines and parsing each as JSON
        lines = trajectory_str.strip().split('\n')
        current_obj = []
        brace_count = 0
        
        for line in lines:
            current_obj.append(line)
            brace_count += line.count('{') - line.count('}')
            
            if brace_count == 0 and current_obj:
                # Complete JSON object found
                obj_str = '\n'.join(current_obj).strip()
                if obj_str:
                    try:
                        tool_obj = json.loads(obj_str)
                        if 'name' in tool_obj or 'tool_name' in tool_obj:
                            tools.append(tool_obj)
                    except json.JSONDecodeError:
                        pass
                current_obj = []
        
        # If we still have unclosed braces, try parsing the whole thing
        if not tools and trajectory_str.strip():
            try:
                tool_obj = json.loads(trajectory_str.strip())
                if isinstance(tool_obj, list):
                    tools = tool_obj
                elif isinstance(tool_obj, dict) and ('name' in tool_obj or 'tool_name' in tool_obj):
                    tools = [tool_obj]
            except json.JSONDecodeError:
                logger.warning(f"Could not parse golden trajectory: {trajectory_str[:100]}...")
    
    except Exception as e:
        logger.error(f"Error parsing golden trajectory: {e}")
    
    return tools


def parse_verifiers(verifiers_str: str) -> List[Dict[str, Any]]:
    """Parse newline-separated SQL queries into verifier configs."""
    if not verifiers_str:
        return []
    
    verifiers = []
    queries = [q.strip() for q in verifiers_str.split('\n') if q.strip()]
    
    for i, query in enumerate(queries):
        if query:
            verifiers.append({
                "name": f"Verifier {i + 1}",
                "description": f"SQL verifier query {i + 1}",
                "type": "database_state",
                "timeout_seconds": 30,
                "target_gym_server": None,
                "sql_query": query,
                "expected_value": 1,
                "comparison_type": "equals",
                "expected_response": None,
                "original_value": ""
            })
    
    return verifiers


def infer_domain_from_filename(filename: str) -> str:
    """Infer domain from filename."""
    filename_lower = filename.lower()
    if "paypal" in filename_lower:
        return "paypal"
    elif "slack" in filename_lower:
        return "slack"
    elif "stripe" in filename_lower:
        return "stripe"
    elif "discord" in filename_lower:
        return "discord"
    else:
        return "paypal"  # Default


def transform_task_to_config(task: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Transform a task from JSON format to config format expected by QualityEvaluator."""
    # Parse tools list
    expected_tools = parse_tools_list(task.get("list_of_tools_used_human", ""))
    
    # Parse golden trajectory
    tools = parse_golden_trajectory(task.get("new_golden_trajectory_human", ""))
    
    # Parse verifiers
    verifier_configs = parse_verifiers(task.get("new_verifiers", ""))
    
    # Build config structure
    config = {
        "task_id": task.get("task_id", "unknown"),
        "task_name": task.get("user_prompt", ""),
        "description": task.get("user_prompt", ""),
        "system_prompt": task.get("system_prompt", ""),
        "scenario_config": {
            "prompt": task.get("user_prompt", ""),
            "system_prompt": task.get("system_prompt", ""),
            "expected_tools": expected_tools,
            "selected_tools": [],
            "restricted_tools": []
        },
        "tools": tools,
        "verifier_configs": verifier_configs
    }
    
    return config


def evaluate_task_pair(
    config_data: dict,
    results_data: dict,
    domain_override: str = None
) -> dict:
    """Evaluate a config/results pair - same logic as web interface."""
    evaluator = QualityEvaluator()
    
    # Create task_data dictionary
    task_data = {
        "task_id": config_data.get("task_id", "unknown_task"),
        "config": config_data,
        "results": results_data,
        "config_path": "batch_eval",
        "results_path": "batch_eval",
        "domain_override": domain_override
    }
    
    results = {
        "task_id": task_data["task_id"],
        "reviewed_at": datetime.now().isoformat(),
        "evaluation_results": {},
        "detected_flags": evaluator.detect_flags(task_data)
    }
    
    logger.info(f"Evaluating dimensions for task: {task_data['task_id']}")
    
    dimensions_to_run = list(QUALITY_DIMENSIONS.keys())
    
    # Skip Model Benchmarking if no results provided
    if not results_data or not results_data.get("results"):
        if "model_benchmarking" in dimensions_to_run:
            dimensions_to_run.remove("model_benchmarking")
            results["evaluation_results"]["Model Benchmarking Analysis"] = {
                "response": "Skipped (No Results Provided)",
                "error": None
            }
            results["Model Benchmarking Analysis"] = "Skipped"
    
    # Evaluate dimensions in parallel (same as web interface)
    with ThreadPoolExecutor(max_workers=THREADS_PER_TASK) as executor:
        future_to_dim = {
            executor.submit(evaluator.evaluate_quality_dimension, dim_key, task_data): dim_key
            for dim_key in dimensions_to_run
        }
        
        for future in as_completed(future_to_dim):
            dim_key = future_to_dim[future]
            try:
                eval_result = future.result()
                dim_name = QUALITY_DIMENSIONS[dim_key]["name"]
                results["evaluation_results"][dim_name] = {
                    "response": eval_result.get("response", ""),
                    "error": eval_result.get("error")
                }
                results[dim_name] = eval_result.get("response", "")
                logger.info(f"✓ Completed: {dim_name} for {task_data['task_id']}")
            except Exception as e:
                logger.error(f"Error evaluating {dim_key} for {task_data['task_id']}: {e}")
                dim_name = QUALITY_DIMENSIONS[dim_key]["name"]
                results["evaluation_results"][dim_name] = {
                    "response": f"Error: {str(e)}",
                    "error": str(e)
                }
    
    return results


def process_batch(json_file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Process a batch of tasks from a JSON file."""
    logger.info(f"Loading tasks from: {json_file_path}")
    
    # Load JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        return []
    
    if not isinstance(tasks, list):
        logger.error("JSON file must contain an array of tasks")
        return []
    
    # Apply limit if specified
    if limit is not None:
        tasks = tasks[:limit]
        logger.info(f"Limited to first {limit} tasks")
    
    logger.info(f"Processing {len(tasks)} tasks...")
    
    # Infer domain from filename
    domain = infer_domain_from_filename(os.path.basename(json_file_path))
    logger.info(f"Inferred domain: {domain}")
    
    # Process each task
    results = []
    errors = []
    
    for i, task in enumerate(tasks, 1):
        task_id = task.get("task_id", f"task_{i}")
        logger.info(f"[{i}/{len(tasks)}] Processing task: {task_id}")
        
        try:
            # Transform task to config format
            config_data = transform_task_to_config(task, domain)
            
            # Create empty results (no model runs available)
            results_data = {
                "results": [],
                "task_metadata": {}
            }
            
            # Evaluate task
            eval_result = evaluate_task_pair(config_data, results_data, domain_override=domain)
            results.append(eval_result)
            
            logger.info(f"✓ Completed task: {task_id}")
        
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            errors.append({
                "task_id": task_id,
                "error": str(e)
            })
    
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during processing")
        for error in errors:
            logger.warning(f"  - {error['task_id']}: {error['error']}")
    
    return results


def save_results(results: List[Dict[str, Any]], input_file_path: str):
    """Save results to a timestamped JSON file in the same directory as input file."""
    # Generate output filename with timestamp
    input_dir = os.path.dirname(os.path.abspath(input_file_path))
    input_basename = os.path.basename(input_file_path)
    input_name, input_ext = os.path.splitext(input_basename)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_name}_results_{timestamp}.json"
    output_path = os.path.join(input_dir, output_filename)
    
    # Save results
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Total tasks evaluated: {len(results)}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch evaluation script for RL Tool Use Data Generation tasks"
    )
    parser.add_argument(
        "json_file",
        help="Path to JSON file containing tasks to evaluate"
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        help="Limit the number of tasks to evaluate (e.g., -n 10 for first 10 tasks)"
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not os.path.exists(args.json_file):
        logger.error(f"File not found: {args.json_file}")
        sys.exit(1)
    
    # Process batch
    results = process_batch(args.json_file, limit=args.limit)
    
    if not results:
        logger.error("No results to save")
        sys.exit(1)
    
    # Save results
    output_path = save_results(results, args.json_file)
    
    if output_path:
        logger.info("=" * 60)
        logger.info("Batch evaluation complete!")
        logger.info(f"Results saved to: {output_path}")
        logger.info("=" * 60)
    else:
        logger.error("Failed to save results")
        sys.exit(1)


if __name__ == "__main__":
    main()
