"""
RLToolUseEval Main Entry Point
Batch processor for evaluating RL Tool Use Data Generation tasks
"""
import os
import sys
import json
import csv
import logging
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any

from dotenv import load_dotenv
load_dotenv()

from config import (
    DATA_DIR, RESULTS_FILE, DETAILED_RESULTS_FILE, ERROR_LOG_FILE,
    CSV_HEADERS, QUALITY_DIMENSIONS, TASKS_PER_PROCESS, THREADS_PER_TASK,
    PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY
)
from quality_evaluator import QualityEvaluator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ERROR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def find_task_pairs(data_dir: str) -> List[Dict[str, str]]:
    """Find matching config and results file pairs in the data directory."""
    config_files = glob.glob(os.path.join(data_dir, "*_config.json"))
    task_pairs = []
    
    for config_path in config_files:
        # Derive results path from config path
        results_path = config_path.replace("_config.json", "_results.json")
        
        if os.path.exists(results_path):
            task_pairs.append({
                "config_path": config_path,
                "results_path": results_path
            })
        else:
            logger.warning(f"No matching results file for: {config_path}")
    
    logger.info(f"Found {len(task_pairs)} task pairs in {data_dir}")
    return task_pairs


def process_single_task(task_pair: Dict[str, str]) -> Dict[str, Any]:
    """Process a single task with all quality dimensions."""
    try:
        config_path = task_pair["config_path"]
        results_path = task_pair["results_path"]
        
        logger.info(f"Processing: {os.path.basename(config_path)}")
        
        evaluator = QualityEvaluator()
        results = evaluator.evaluate_task(config_path, results_path)
        
        logger.info(f"Completed: {results.get('task_id')}")
        return results
    
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        return {
            "task_id": "error",
            "config_file": task_pair.get("config_path"),
            "results_file": task_pair.get("results_path"),
            "error": str(e)
        }


def process_task_batch(task_pairs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Process a batch of tasks using threading for quality dimensions."""
    batch_results = []
    
    for task_pair in task_pairs:
        result = process_single_task(task_pair)
        batch_results.append(result)
    
    return batch_results


class QualityEvaluationProcessor:
    """Main processor for batch evaluation of RL Tool Use tasks."""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or DATA_DIR
        self.results = []
        self.errors = []
    
    def initialize_results_file(self):
        """Initialize JSON results file."""
        os.makedirs(os.path.dirname(DETAILED_RESULTS_FILE), exist_ok=True)
        if not os.path.exists(DETAILED_RESULTS_FILE):
            with open(DETAILED_RESULTS_FILE, 'w') as f:
                json.dump([], f)
    
    def append_result_to_json(self, result: Dict[str, Any]):
        """Append a result to the JSON file."""
        try:
            with open(DETAILED_RESULTS_FILE, 'r') as f:
                existing = json.load(f)
            
            existing.append(result)
            
            with open(DETAILED_RESULTS_FILE, 'w') as f:
                json.dump(existing, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving result to JSON: {e}")
    
    def save_results_to_csv(self):
        """Save evaluation results to CSV file."""
        try:
            os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
            
            with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                writer.writeheader()
                
                for result in self.results:
                    row = {
                        "task_id": result.get("task_id", "unknown"),
                        "config_file": result.get("config_file", ""),
                        "results_file": result.get("results_file", ""),
                        "reviewed_at": result.get("reviewed_at", "")
                    }
                    
                    for dim_name in [qd["name"] for qd in QUALITY_DIMENSIONS.values()]:
                        row[dim_name] = result.get(dim_name, "N/A")
                    
                    writer.writerow(row)
            
            logger.info(f"Results saved to {RESULTS_FILE}")
        
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    def run_evaluation(self):
        """Run the complete quality evaluation process."""
        logger.info("=" * 60)
        logger.info("Starting RLToolUseEval Quality Evaluation")
        logger.info(f"Provider: {PROVIDER}")
        logger.info("=" * 60)
        
        # Initialize
        self.initialize_results_file()
        
        # Find task pairs
        task_pairs = find_task_pairs(self.data_dir)
        
        if not task_pairs:
            logger.error(f"No task pairs found in {self.data_dir}")
            return
        
        # Process tasks
        logger.info(f"Processing {len(task_pairs)} tasks...")
        
        for task_pair in task_pairs:
            result = process_single_task(task_pair)
            self.results.append(result)
            self.append_result_to_json(result)
            
            if "error" in result:
                self.errors.append(result)
        
        # Save final results
        self.save_results_to_csv()
        
        logger.info("=" * 60)
        logger.info(f"Evaluation complete. Processed {len(self.results)} tasks.")
        if self.errors:
            logger.warning(f"Errors encountered: {len(self.errors)}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    # Check API keys
    if PROVIDER == 'google' and not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not set. Please set it in .env file.")
        return
    elif PROVIDER == 'openai' and not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Please set it in .env file.")
        return
    
    # Check prompt files
    missing_prompts = []
    for dim_key, dim_config in QUALITY_DIMENSIONS.items():
        for prompt_type in ["system_prompt_file", "agent_prompt_file"]:
            path = dim_config[prompt_type]
            if not os.path.exists(path):
                missing_prompts.append(path)
    
    if missing_prompts:
        logger.warning("Missing prompt files:")
        for p in missing_prompts:
            logger.warning(f"  - {p}")
        logger.warning("Please create these files before running evaluation.")
        return
    
    # Get data directory from args or use default
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR
    
    # Run evaluation
    processor = QualityEvaluationProcessor(data_dir)
    processor.run_evaluation()


if __name__ == "__main__":
    main()
