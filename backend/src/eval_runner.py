import json
from pathlib import Path
from typing import Any

from src.eval_framework import evaluate_eval_set, load_eval_set_from_file


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_SET_PATH = REPO_ROOT / 'tests' / 'eval' / 'graphite_react_agent.evalset.json'
DEFAULT_CONFIG_PATH = REPO_ROOT / 'tests' / 'eval' / 'test_config.json'

LOCAL_SUPPORTED_CRITERIA = {
  'tool_trajectory_avg_score',
  'response_match_score',
}


def load_eval_config(config_path: str | None = None) -> dict[str, Any]:
  path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
  if not path.exists():
    return {'criteria': {}}
  with path.open('r', encoding='utf-8') as handle:
    return json.load(handle)


def split_supported_criteria(criteria: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
  supported: dict[str, Any] = {}
  unsupported: list[str] = []
  for name, config in criteria.items():
    if name in LOCAL_SUPPORTED_CRITERIA:
      supported[name] = config
    else:
      unsupported.append(name)
  return supported, unsupported


def run_saved_eval_set(
  services,
  *,
  eval_set_path: str | None = None,
  config_path: str | None = None,
  run_agent_fn=None,
) -> dict[str, Any]:
  resolved_eval_set_path = Path(eval_set_path) if eval_set_path else DEFAULT_EVAL_SET_PATH
  eval_set = load_eval_set_from_file(str(resolved_eval_set_path))
  config = load_eval_config(config_path)
  declared_criteria = config.get('criteria', {})
  supported_criteria, unsupported_criteria = split_supported_criteria(declared_criteria)

  if run_agent_fn is None:
    from src.react_agent import run_react_agent_sync

    def run_agent_fn(services, task: str, user_id: str = 'web-local'):
      return run_react_agent_sync(services, task, user_id=user_id, agent_id='react')

  summary = evaluate_eval_set(eval_set, run_agent_fn, services, supported_criteria)
  summary.update({
    'eval_set_path': str(resolved_eval_set_path),
    'config_path': str(Path(config_path) if config_path else DEFAULT_CONFIG_PATH),
    'declared_criteria': sorted(declared_criteria.keys()),
    'supported_criteria': sorted(supported_criteria.keys()),
    'unsupported_criteria': sorted(unsupported_criteria),
  })
  return summary