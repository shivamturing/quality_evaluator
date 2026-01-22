"""
RLToolUseEval Quality Evaluator
Dual-provider (OpenAI + Gemini) evaluation engine for RL Tool Use Data Generation
"""
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime

from config import (
    QUALITY_DIMENSIONS, PROVIDER, 
    OPENAI_API_KEY, OPENAI_MODEL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
    REQUEST_TIMEOUT, FAILURE_CATEGORIES, FLAGS
)
from langsmith import traceable

# Conditional imports for providers
if PROVIDER == 'google':
    from google import genai
    from google.genai import types
elif PROVIDER == 'openai':
    import openai


class QualityEvaluator:
    """Evaluator for RL Tool Use Data Generation quality dimensions."""
    
    def __init__(self, provider: str = None):
        self.provider = provider or PROVIDER
        self.logger = logging.getLogger(__name__)
        self._init_client()
    
    def _init_client(self):
        """Initialize the LLM client based on provider."""
        if self.provider == 'google':
            self.client = genai.Client()
            self.model = GOOGLE_MODEL
        elif self.provider == 'openai':
            self.client = openai.OpenAI()
            self.model = OPENAI_MODEL
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    # ==========================================================================
    # Tool Definition Loading (Same pattern as HumanTraceEval)
    # ==========================================================================
    
    def _load_tool_info(self, domain: str = None) -> List[Dict[str, Any]]:
        """Load tool definitions from domain-specific JSON file.
        
        Args:
            domain: The domain name (e.g., 'paypal', 'slack') to load tools for.
        
        Returns:
            List of tool definitions with name, description, and parameters.
        """
        if not domain:
            self.logger.warning("No domain specified, cannot load tool info")
            return []
        
        tool_file = os.path.join(os.path.dirname(__file__), 'tools', f'{domain}.json')
        
        try:
            with open(tool_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Tool info file not found: {tool_file}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing tool info file: {e}")
            return []
    
    def _extract_tool_names(self, tool_info: List[Dict[str, Any]]) -> List[str]:
        """Extract tool names from tool_info, handling different formats.
        
        Supports:
        - Simple format: [{"name": "tool_name", ...}]
        - OpenAI format: [{"type": "function", "function": {"name": "tool_name", ...}}]
        """
        tool_names = []
        for tool in tool_info:
            # Try direct name
            if 'name' in tool:
                tool_names.append(tool['name'])
            # Try nested function.name (OpenAI format)
            elif 'function' in tool and isinstance(tool['function'], dict):
                tool_names.append(tool['function'].get('name', ''))
        return tool_names
    
    # ==========================================================================
    # LLM API Calls
    # ==========================================================================
    
    @traceable(run_type="llm", name="LLM Call")
    def _get_llm_response(self, system_prompt: str, user_prompt: str) -> str:
        """Get response from LLM based on configured provider."""
        try:
            if self.provider == 'google':
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.3,
                    ),
                )
                return response.candidates[0].content.parts[0].text
            
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    timeout=REQUEST_TIMEOUT
                )
                return response.choices[0].message.content.strip()
        
        except Exception as e:
            self.logger.error(f"LLM API error: {e}")
            raise
    
    # ==========================================================================
    # Prompt Loading
    # ==========================================================================
    
    def load_prompts(self, dimension_key: str) -> Tuple[str, str]:
        """Load system and agent prompts for a specific quality dimension."""
        try:
            base_dir = os.path.dirname(__file__)
            
            system_path = os.path.join(base_dir, QUALITY_DIMENSIONS[dimension_key]["system_prompt_file"])
            agent_path = os.path.join(base_dir, QUALITY_DIMENSIONS[dimension_key]["agent_prompt_file"])
            
            with open(system_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
            
            with open(agent_path, 'r', encoding='utf-8') as f:
                agent_prompt = f.read().strip()
            
            return system_prompt, agent_prompt
        
        except FileNotFoundError as e:
            self.logger.error(f"Prompt file not found for {dimension_key}: {e}")
            return "", ""
    
    # ==========================================================================
    # Data Transformation
    # ==========================================================================
    
    def load_task_data(self, config_path: str, results_path: str) -> Dict[str, Any]:
        """Load and merge config and results files into a unified task object.
        
        Also loads tool definitions from domain-specific file.
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        with open(results_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
        
        # Extract domain from config (e.g., 'paypal', 'slack', 'stripe')
        # Look in scenario_config.mcp_server_name or metadata.domain
        # Extract domain from config (e.g., 'paypal', 'slack', 'stripe')
        # Robust check: scenario_config, top-level, or metadata
        domain = None
        scenario_config = config_data.get("scenario_config", {})
        
        if "mcp_server_name" in scenario_config:
            domain = scenario_config["mcp_server_name"]
        elif "mcp_server_name" in config_data:
            domain = config_data["mcp_server_name"]
        elif "domain" in config_data.get("metadata", {}):
            domain = config_data["metadata"]["domain"]
            
        # UI Override (highest priority if provided)
        if task_data.get("domain_override"):
            domain = task_data["domain_override"]
        
        # Fallback: Try to guess from config filename
        if not domain and config_path != "uploaded":
            filename = os.path.basename(config_path).lower()
            if "paypal" in filename: domain = "paypal"
            elif "slack" in filename: domain = "slack"
            elif "stripe" in filename: domain = "stripe"
            elif "discord" in filename: domain = "discord"
        
        # Load tool definitions for this domain
        tool_definitions = self._load_tool_info(domain)
        allowed_tools = self._extract_tool_names(tool_definitions)
        
        return {
            "task_id": config_data.get("task_id"),
            "domain": domain,
            "config": config_data,
            "results": results_data,
            "config_path": config_path,
            "results_path": results_path,
            # Tool definitions loaded from tools/{domain}.json
            "tool_definitions": tool_definitions,
            "allowed_tools": allowed_tools
        }
    
    def extract_prompt_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for Prompt Quality evaluation."""
        config = task_data.get("config", {})
        scenario = config.get("scenario_config", {})
        
        return {
            "prompt_text": scenario.get("prompt", config.get("task_name", "")),
            "system_prompt": scenario.get("system_prompt", config.get("system_prompt", "")),
            "expected_tools": scenario.get("expected_tools", []),
            "task_description": config.get("description", "")
        }
    
    def extract_happy_path_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for Happy Path evaluation."""
        config = task_data.get("config", {})
        
        tools = config.get("tools", [])
        happy_path_steps = []
        
        for i, tool in enumerate(tools):
            step = {
                "step_number": i + 1,
                "tool_name": tool.get("name"),
                "arguments": tool.get("arguments", {}),
                "execution_result": tool.get("tool_execution_results", {})
            }
            happy_path_steps.append(step)
        
        return {
            "expected_tools": config.get("scenario_config", {}).get("expected_tools", []),
            "happy_path_steps": happy_path_steps
        }
    
    def extract_sql_verifier_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for SQL Verifier Quality evaluation."""
        config = task_data.get("config", {})
        
        verifiers = []
        for v in config.get("verifier_configs", []):
            verifiers.append({
                "name": v.get("name"),
                "description": v.get("description"),
                "sql_query": v.get("sql_query"),
                "expected_value": v.get("expected_value"),
                "comparison_type": v.get("comparison_type")
            })
        
        return {
            "verifiers": verifiers,
            "prompt_text": config.get("scenario_config", {}).get("prompt", "")
        }
    
    def extract_model_run_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for Model Benchmarking evaluation."""
        results = task_data.get("results", {})
        config = task_data.get("config", {})
        
        model_runs = []
        for run in results.get("results", []):
            model_runs.append({
                "run_number": run.get("run_number"),
                "status": run.get("status"),
                "mcp_tool_calls": run.get("mcp_tool_calls", []),
                "verification_result": run.get("verification_result", []),
                "overall_success": run.get("overall_success"),
                "agent_response": run.get("agent_response", ""),
                "error_message": run.get("error_message")
            })
        
        return {
            "expected_tools": config.get("scenario_config", {}).get("expected_tools", []),
            "happy_path": config.get("tools", []),
            "model_runs": model_runs,
            "models_tested": results.get("task_metadata", {}).get("models_to_test", [])
        }
    
    # ==========================================================================
    # Auto-Detection of Failure Categories
    # ==========================================================================
    
    def detect_failure_category(self, model_run: Dict[str, Any], expected_tools: List[str]) -> str:
        """Auto-detect the failure category based on model run data."""
        mcp_calls = model_run.get("mcp_tool_calls", [])
        agent_response = model_run.get("agent_response", "")
        overall_success = model_run.get("overall_success", False)
        
        # Check for Pass
        if overall_success:
            return "pass"
        
        # Check for Refusal
        refusal_patterns = [
            r"i cannot assist",
            r"i'm not able to",
            r"i can't help with",
            r"outside my capabilities",
            r"i don't have access"
        ]
        for pattern in refusal_patterns:
            if re.search(pattern, agent_response.lower()):
                return "refusal"
        
        # Check if model made any tool calls
        if not mcp_calls:
            # Model didn't call any tools but gave a response
            if agent_response:
                # Check if it claimed to complete the task (hallucination)
                completion_patterns = [r"i have completed", r"done", r"task is complete", r"successfully"]
                for pattern in completion_patterns:
                    if re.search(pattern, agent_response.lower()):
                        return "hallucination"
                
                # Check if asking for confirmation
                question_patterns = [r"\?", r"would you like", r"should i", r"can you confirm"]
                for pattern in question_patterns:
                    if re.search(pattern, agent_response.lower()):
                        return "asking_confirmation"
            
            return "incomplete"
        
        # Model made tool calls - check if correct tools
        called_tools = [call.get("tool_name") for call in mcp_calls]
        
        # Check for wrong tool
        for called in called_tools:
            if called and called not in expected_tools:
                return "wrong_tool"
        
        # If tools are correct but verification failed, likely wrong parameter
        return "wrong_parameter"
    
    # ==========================================================================
    # Flag Detection
    # ==========================================================================
    
    def detect_flags(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect flags in the task data."""
        flags_found = []
        config = task_data.get("config", {})
        # Try multiple paths to find the prompt
        prompt = config.get("scenario_config", {}).get("prompt", "")
        if not prompt:
            prompt = config.get("prompt", "")
        
        # Check for Magic IDs
        # Pass prompt to allow IDs that are explicitly mentioned
        magic_ids = self._detect_magic_ids(config.get("tools", []), prompt)
        if magic_ids:
            flags_found.append({
                "flag_type": "magic_id",
                "details": magic_ids
            })
        
        # Check for API params in prompt
        api_params = self._detect_api_params_in_prompt(prompt)
        if api_params:
            flags_found.append({
                "flag_type": "api_param_in_prompt",
                "details": api_params
            })
        
        # Check for redundant calls
        redundant = self._detect_redundant_calls(config.get("tools", []))
        if redundant:
            flags_found.append({
                "flag_type": "redundant_calls",
                "details": redundant
            })
        
        return flags_found
    
    def _detect_magic_ids(self, tools: List[Dict], prompt: str = "") -> List[str]:
        """Detect IDs used before they were retrieved.
        
        IDs found in the 'prompt' are whitelisted (considered 'known').
        """
        magic_ids = []
        known_ids = set()
        
        # Whitelist IDs from prompt
        if prompt:
            # Simple alphanumeric ID pattern
            prompt_ids = re.findall(r'[A-Z0-9]{10,}|[A-Z]+-[A-Z0-9]+', prompt)
            known_ids.update(prompt_ids)
        
        for tool in tools:
            # Get IDs from arguments
            args = tool.get("arguments", {})
            args_str = json.dumps(args)
            
            # Find ID patterns
            id_patterns = re.findall(r'[A-Z0-9]{10,}|[A-Z]+-[A-Z0-9]+', args_str)
            
            for id_val in id_patterns:
                if id_val not in known_ids:
                    magic_ids.append(f"ID '{id_val}' used in {tool.get('name')} before retrieval")
            
            # Add IDs from output to known set
            execution_results = tool.get("tool_execution_results") or {}
            result = execution_results.get("result", {})
            result_str = json.dumps(result)
            found_ids = re.findall(r'"id":\s*"([^"]+)"', result_str)
            known_ids.update(found_ids)
        
        return magic_ids
    
    def _detect_api_params_in_prompt(self, prompt: str) -> List[str]:
        """Detect API parameter names in the prompt."""
        api_param_patterns = [
            r'\b(is_private|is_public|user_id|channel_id|webhook_id)\s*=',
            r'set\s+(\w+_\w+)\s+to',
            r'parameter\s+(\w+)',
        ]
        
        found = []
        for pattern in api_param_patterns:
            matches = re.findall(pattern, prompt.lower())
            found.extend(matches)
        
        return found
    
    def _detect_redundant_calls(self, tools: List[Dict]) -> List[str]:
        """Detect redundant tool calls."""
        call_counts = {}
        for tool in tools:
            name = tool.get("name", "")
            call_counts[name] = call_counts.get(name, 0) + 1
        
        redundant = [f"{name} called {count} times" for name, count in call_counts.items() if count > 1]
        return redundant
    
    # ==========================================================================
    # Prompt Processing
    # ==========================================================================
    
    def process_agent_prompt(self, dimension_key: str, agent_prompt: str, task_data: Dict[str, Any]) -> str:
        """Replace placeholders in agent prompt with actual data."""
        processed = agent_prompt
        
        # Common: Add tool definitions and allowed tools to ALL prompts
        tool_definitions = task_data.get("tool_definitions", [])
        allowed_tools = task_data.get("allowed_tools", [])
        processed = processed.replace("{tool_definitions}", json.dumps(tool_definitions, indent=2))
        processed = processed.replace("{allowed_tools}", json.dumps(allowed_tools, indent=2))
        
        if dimension_key == "prompt_quality":
            data = self.extract_prompt_data(task_data)
            processed = processed.replace("{prompt_text}", data.get("prompt_text", ""))
            processed = processed.replace("{expected_tools}", json.dumps(data.get("expected_tools", []), indent=2))
            processed = processed.replace("{system_prompt}", data.get("system_prompt", ""))
        
        elif dimension_key == "happy_path_execution":
            data = self.extract_happy_path_data(task_data)
            processed = processed.replace("{expected_tools}", json.dumps(data.get("expected_tools", []), indent=2))
            processed = processed.replace("{happy_path_steps}", json.dumps(data.get("happy_path_steps", []), indent=2))
        
        elif dimension_key == "sql_verifier_quality":
            data = self.extract_sql_verifier_data(task_data)
            processed = processed.replace("{verifiers}", json.dumps(data.get("verifiers", []), indent=2))
            processed = processed.replace("{prompt_text}", data.get("prompt_text", ""))
        
        elif dimension_key == "model_benchmarking":
            data = self.extract_model_run_data(task_data)
            processed = processed.replace("{expected_tools}", json.dumps(data.get("expected_tools", []), indent=2))
            processed = processed.replace("{happy_path}", json.dumps(data.get("happy_path", []), indent=2))
            processed = processed.replace("{model_runs}", json.dumps(data.get("model_runs", []), indent=2))
        
        # Add detected flags
        flags = self.detect_flags(task_data)
        processed = processed.replace("{detected_flags}", json.dumps(flags, indent=2))
        
        return processed
    
    # ==========================================================================
    # Evaluation
    # ==========================================================================
    
    @traceable(run_type="chain", name="Evaluate Dimension")
    def evaluate_quality_dimension(self, dimension_key: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single quality dimension."""
        try:
            system_prompt, agent_prompt = self.load_prompts(dimension_key)
            
            if not system_prompt or not agent_prompt:
                return {
                    "dimension": dimension_key,
                    "response": "Prompts not configured",
                    "error": "Empty prompt files"
                }
            
            processed_prompt = self.process_agent_prompt(dimension_key, agent_prompt, task_data)
            response = self._get_llm_response(system_prompt, processed_prompt)
            
            return {
                "dimension": dimension_key,
                "response": response,
                "error": None
            }
        
        except Exception as e:
            self.logger.error(f"Error evaluating {dimension_key}: {e}")
            return {
                "dimension": dimension_key,
                "response": f"Evaluation error: {str(e)}",
                "error": str(e)
            }
    
    @traceable(run_type="chain", name="Evaluate Task")
    def evaluate_task(self, config_path: str, results_path: str) -> Dict[str, Any]:
        """Evaluate all quality dimensions for a task."""
        task_data = self.load_task_data(config_path, results_path)
        
        results = {
            "task_id": task_data.get("task_id"),
            "config_file": config_path,
            "results_file": results_path,
            "reviewed_at": datetime.now().isoformat(),
            "evaluation_results": {},
            "detected_flags": self.detect_flags(task_data)
        }
        
        for dimension_key in QUALITY_DIMENSIONS:
            self.logger.info(f"Evaluating {dimension_key} for {task_data.get('task_id')}")
            eval_result = self.evaluate_quality_dimension(dimension_key, task_data)
            
            dimension_name = QUALITY_DIMENSIONS[dimension_key]["name"]
            results["evaluation_results"][dimension_name] = eval_result
            results[dimension_name] = eval_result.get("response", "")
        
        return results
