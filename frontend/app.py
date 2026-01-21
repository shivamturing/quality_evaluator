"""
RLToolUseEval Frontend - Flask API Server
Web interface for evaluating RL Tool Use Data Generation tasks
"""
import sys
import os

# Add parent directory to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
import requests
import base64
from werkzeug.utils import secure_filename
import json
import csv
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from quality_evaluator import QualityEvaluator
from config import QUALITY_DIMENSIONS, PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY

# Paths
RESULTS_CSV = os.path.join(PROJECT_ROOT, 'results', 'results.csv')
RESULTS_JSON = os.path.join(PROJECT_ROOT, 'results', 'results.json')

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
            static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

app.secret_key = os.environ.get('FRONTEND_SECRET_KEY', 'rltooluseeval-dev-secret')

THREADS_PER_TASK = 4
ADMIN_USER = os.environ.get('ADMIN_USER', 'deep-chokshi')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Deep@256114')
FRONTEND_PORT = int(os.environ.get('FRONTEND_PORT', '5002'))
FRONTEND_DEBUG = os.environ.get('FRONTEND_DEBUG', '0') == '1'
RL_GYM_API_KEY = os.environ.get('RL_GYM_API_KEY')
RL_GYM_BASE_URL = os.environ.get('RL_GYM_BASE_URL', 'https://rl-gym-advance.turing.com')


def _check_admin_auth() -> bool:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        encoded = auth_header.split(' ', 1)[1].strip()
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username == ADMIN_USER and password == ADMIN_PASS
    except Exception:
        return False


def _require_admin_auth():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="RLToolUseEval Admin"'}
    )


def evaluate_task_pair(
    config_data: dict,
    results_data: dict,
    domain_override: str = None,
    reviewer_email: str = None
) -> dict:
    """Evaluate a config/results pair."""
    evaluator = QualityEvaluator()
    
    # Create temp files or pass data directly
    task_data = {
        "task_id": config_data.get("task_id", "uploaded_task"),
        "config": config_data,
        "results": results_data,
        "config_path": "uploaded",
        "results_path": "uploaded",
        "domain_override": domain_override
    }
    
    results = {
        "task_id": task_data["task_id"],
        "reviewed_at": datetime.now().isoformat(),
        "reviewer_email": reviewer_email,
        "evaluation_results": {},
        "detected_flags": evaluator.detect_flags(task_data)
    }
    
    logger.info(f"Evaluating dimensions...")
    
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
                logger.info(f"✓ Completed: {dim_name}")
            except Exception as e:
                logger.error(f"Error evaluating {dim_key}: {e}")
    
    return results


def _require_api_key():
    return jsonify({"error": "RL_GYM_API_KEY is not set on the server"}), 500


def _proxy_rl_gym(path: str) -> Response:
    if not RL_GYM_API_KEY:
        return _require_api_key()
    url = f"{RL_GYM_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {RL_GYM_API_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    except requests.RequestException as exc:
        return jsonify({"error": f"Upstream request failed: {exc}"}), 502


def save_result(result: dict):
    """Save result to JSON file."""
    os.makedirs(os.path.dirname(RESULTS_JSON), exist_ok=True)
    
    existing = []
    if os.path.exists(RESULTS_JSON) and os.path.getsize(RESULTS_JSON) > 0:
        try:
            with open(RESULTS_JSON, 'r') as f:
                existing = json.load(f)
        except:
            existing = []
    
    existing.append(result)
    
    with open(RESULTS_JSON, 'w') as f:
        json.dump(existing, f, indent=2)


@app.route('/')
def index():
    """Serve main page."""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.route('/admin')
def admin():
    """Serve admin page (basic auth protected)."""
    if not _check_admin_auth():
        return _require_admin_auth()
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'admin.html')


@app.route('/api/health')
def health():
    """Health check."""
    api_configured = bool(GOOGLE_API_KEY if PROVIDER == 'google' else OPENAI_API_KEY)
    return jsonify({
        "status": "healthy",
        "provider": PROVIDER,
        "api_configured": api_configured
    })


@app.route('/api/dimensions')
def get_dimensions():
    """Return quality dimensions."""
    dims = [
        {"key": k, "name": v["name"], "description": v["description"], "sub_checks": v.get("sub_checks", [])}
        for k, v in QUALITY_DIMENSIONS.items()
    ]
    return jsonify({"dimensions": dims})


@app.route('/api/environments')
def get_environments():
    """Return list of available tool environments."""
    tools_dir = os.path.join(PROJECT_ROOT, 'tools')
    envs = []
    
    if os.path.exists(tools_dir):
        for f in os.listdir(tools_dir):
            if f.endswith('.json'):
                envs.append(os.path.splitext(f)[0])
                
    return jsonify({"environments": sorted(envs)})


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Evaluate uploaded task files."""
    logger.info("Received evaluation request")
    
    try:
        # Check for file uploads
        if 'config_file' not in request.files:
            return jsonify({"error": "Config file is required"}), 400
        
        config_file = request.files['config_file']
        results_file = request.files.get('results_file')
        
        if not config_file.filename.endswith('.json'):
             return jsonify({"error": "Config file must be JSON"}), 400
             
        if results_file and not results_file.filename.endswith('.json'):
            return jsonify({"error": "Results file must be JSON"}), 400
        
        # Parse files
        config_data = json.loads(config_file.read().decode('utf-8'))
        results_data = {}
        if results_file:
            results_data = json.loads(results_file.read().decode('utf-8'))
        
        logger.info(f"Evaluating task: {config_data.get('task_id', 'unknown')}")
        
        reviewer_email = request.form.get('reviewer_email', '').strip()
        if not reviewer_email:
            return jsonify({"error": "Reviewer email is required"}), 400
        if not reviewer_email.lower().endswith('@turing.com'):
            return jsonify({"error": "Reviewer email must be a @turing.com address"}), 400

        domain = request.form.get('domain')
        if domain == "": domain = None  # Handle empty string from select
        
        # Evaluate
        result = evaluate_task_pair(
            config_data,
            results_data,
            domain_override=domain,
            reviewer_email=reviewer_email
        )
        
        # Save
        save_result(result)
        
        return jsonify(result)
    
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tasks/<task_id>/config')
def fetch_task_config(task_id: str):
    return _proxy_rl_gym(f"/api/tasks/{task_id}/config")


@app.route('/api/tasks/<task_id>/download')
def fetch_task_results(task_id: str):
    return _proxy_rl_gym(f"/api/tasks/{task_id}/download")


@app.route('/api/evaluate_task', methods=['POST'])
def evaluate_task_by_id():
    if not RL_GYM_API_KEY:
        return _require_api_key()
    data = request.get_json(silent=True) or {}
    task_id = data.get('task_id', '').strip()
    domain = data.get('domain')
    reviewer_email = data.get('reviewer_email', '').strip()

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400
    if not reviewer_email:
        return jsonify({"error": "Reviewer email is required"}), 400
    if not reviewer_email.lower().endswith('@turing.com'):
        return jsonify({"error": "Reviewer email must be a @turing.com address"}), 400

    try:
        config_resp = requests.get(
            f"{RL_GYM_BASE_URL}/api/tasks/{task_id}/config",
            headers={"Authorization": f"Bearer {RL_GYM_API_KEY}"},
            timeout=30
        )
        if config_resp.status_code != 200:
            return jsonify({"error": f"Config fetch failed: {config_resp.text}"}), config_resp.status_code

        results_resp = requests.get(
            f"{RL_GYM_BASE_URL}/api/tasks/{task_id}/download",
            headers={"Authorization": f"Bearer {RL_GYM_API_KEY}"},
            timeout=30
        )
        if results_resp.status_code != 200:
            return jsonify({"error": f"Results fetch failed: {results_resp.text}"}), results_resp.status_code

        config_data = config_resp.json()
        results_data = results_resp.json()

        result = evaluate_task_pair(
            config_data,
            results_data,
            domain_override=domain,
            reviewer_email=reviewer_email
        )

        save_result(result)
        return jsonify(result)
    except requests.RequestException as exc:
        return jsonify({"error": f"Upstream request failed: {exc}"}), 502


@app.route('/api/history')
def get_history():
    """Get evaluation history."""
    if not os.path.exists(RESULTS_JSON):
        return jsonify({"history": []})
    
    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        
        history = [
            {
                "index": i,
                "task_id": r.get("task_id"),
                "reviewed_at": r.get("reviewed_at"),
                "flags_count": len(r.get("detected_flags", []))
            }
            for i, r in enumerate(reversed(results))
        ]
        
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history/<int:index>')
def get_history_entry(index):
    """Get specific history entry."""
    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        
        if index < 0 or index >= len(results):
            return jsonify({"error": "Not found"}), 404
        
        return jsonify(results[index])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/results')
def admin_results():
    """Return evaluation results for admin view (basic auth protected)."""
    if not _check_admin_auth():
        return _require_admin_auth()
    if not os.path.exists(RESULTS_JSON):
        return jsonify({"results": []})
    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        results = list(reversed(results))
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/download/json')
def download_json():
    """Download results JSON."""
    if os.path.exists(RESULTS_JSON):
        return send_file(RESULTS_JSON, mimetype='application/json', as_attachment=True)
    return jsonify({"error": "No results"}), 404


if __name__ == '__main__':
    if PROVIDER == 'google' and not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set!")
    elif PROVIDER == 'openai' and not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set!")
    
    print("\n" + "=" * 60)
    print("RLToolUseEval Frontend")
    print(f"Provider: {PROVIDER}")
    print("=" * 60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=FRONTEND_PORT,
        debug=FRONTEND_DEBUG,
        use_reloader=FRONTEND_DEBUG
    )
