"""
RLToolUseEval Configuration
Quality Dimensions for RL Tool Use Data Generation Evaluation
"""
import os
from typing import Dict, List

# ==============================================================================
# LLM Provider Configuration (Dual-Provider Support)
# ==============================================================================
PROVIDER = os.getenv("LLM_PROVIDER", "google")  # 'google' or 'openai'

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Google Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

# ==============================================================================
# Quality Dimensions (Mapped from RL Tool Use Data Generation Rubric)
# ==============================================================================
QUALITY_DIMENSIONS = {
    "prompt_quality": {
        "name": "Prompt Quality",
        "description": "Evaluates if the Trainer created a realistic, solvable prompt grounded in the specific environment",
        "sub_checks": ["Naturalness", "Environment Grounding", "Complexity"],
        "system_prompt_file": "prompts/system/prompt_quality.txt",
        "agent_prompt_file": "prompts/agent/prompt_quality.txt"
    },
    "happy_path_execution": {
        "name": "Manual Tool Execution (Happy Path)",
        "description": "Evaluates the Gold Standard execution performed by the Trainer - the Imitation Learning target",
        "sub_checks": ["Tool Selection", "Parameter Accuracy", "Logical Dependency", "State Change"],
        "system_prompt_file": "prompts/system/happy_path_execution.txt",
        "agent_prompt_file": "prompts/agent/happy_path_execution.txt"
    },
    "sql_verifier_quality": {
        "name": "SQL Verifier Quality",
        "description": "Evaluates the SQL queries written to validate the model's performance",
        "sub_checks": ["Target Accuracy", "State Validation", "Robustness"],
        "system_prompt_file": "prompts/system/sql_verifier_quality.txt",
        "agent_prompt_file": "prompts/agent/sql_verifier_quality.txt"
    },
    "model_benchmarking": {
        "name": "Model Benchmarking Analysis",
        "description": "Evaluates the analysis of model runs (Pass@10) to ensure accurate labeling of model failures",
        "sub_checks": ["Categorization Accuracy", "Comment Quality"],
        "system_prompt_file": "prompts/system/model_benchmarking.txt",
        "agent_prompt_file": "prompts/agent/model_benchmarking.txt"
    }
}

# ==============================================================================
# Failure Categories (For Auto-Detection)
# ==============================================================================
FAILURE_CATEGORIES = {
    "pass": "Model successfully completed the task",
    "wrong_tool": "Model chose the wrong tool entirely",
    "wrong_parameter": "Model chose correct tool but failed on parameter syntax/values",
    "hallucination": "Model invented facts, confirmation, or IDs not from tool output",
    "asking_confirmation": "Model stopped to ask a question instead of completing the task",
    "refusal": "Model refused to complete the task (safety/policy)",
    "incomplete": "Model stopped prematurely without completing all required steps"
}

# ==============================================================================
# Flag Definitions (From Rubric)
# ==============================================================================
FLAGS = {
    "magic_id": {
        "name": "Magic ID",
        "description": "Trainer uses an ID that was never output by a previous tool in the trace"
    },
    "fake_pass": {
        "name": "Fake Pass (False Positive)",
        "description": "Model claimed success but never called the required tool"
    },
    "lazy_verification": {
        "name": "Lazy Verification",
        "description": "Wrong tool mislabeled as wrong parameter"
    },
    "safety_mislabel": {
        "name": "Safety Trigger Mislabel",
        "description": "Refusal mislabeled as asking for confirmation"
    },
    "redundant_calls": {
        "name": "Redundant Tool Calls",
        "description": "Trainer calls the same tool multiple times unnecessarily"
    },
    "api_param_in_prompt": {
        "name": "API Parameter in Prompt",
        "description": "Prompt includes API parameter names (e.g., 'Set is_private to true')"
    }
}

# ==============================================================================
# File Paths
# ==============================================================================
DATA_DIR = "data"
RESULTS_FILE = "results/results.csv"
DETAILED_RESULTS_FILE = "results/results.json"
ERROR_LOG_FILE = "logs/error_log.txt"

# ==============================================================================
# Processing Configuration
# ==============================================================================
TASKS_PER_PROCESS = 4
THREADS_PER_TASK = 4
REQUEST_TIMEOUT = 120

# ==============================================================================
# CSV Headers
# ==============================================================================
CSV_HEADERS = [
    "task_id", 
    "config_file", 
    "results_file",
    "reviewed_at"
] + [qd["name"] for qd in QUALITY_DIMENSIONS.values()]
