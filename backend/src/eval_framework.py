"""
Graphite Agent Evaluation Framework — ADK-eval compatible.

Implements trajectory evaluation and response matching based on Google ADK
evaluation patterns. Incorporates 10 key insights from ADK codelabs:

1. Define clear success criteria before evaluation
2. Evaluate trajectory (tool use sequence) not just final output
3. Use both exact-match and semantic similarity for responses
4. Track tool_trajectory_avg_score and response_match_score
5. Create test files with expected tool use and expected responses
6. Support multi-turn conversation evaluation
7. Include session_input for reproducible state
8. Use rubric-based evaluation when no reference response exists
9. Log all intermediate steps for debugging
10. Automate evaluations in CI/CD pipelines via pytest
"""

import json
import logging
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any
from uuid import uuid4

logger = logging.getLogger('graphite.eval')


def _resolve_threshold(criterion: Any, default: float) -> float:
  if isinstance(criterion, dict):
    return float(criterion.get('threshold', default))
  if isinstance(criterion, (int, float)):
    return float(criterion)
  return default


def _resolve_match_type(criterion: Any) -> str:
  if isinstance(criterion, dict):
    return str(criterion.get('match_type', 'EXACT')).upper()
  return 'EXACT'


def compute_trajectory_score(
  actual: list[str],
  expected: list[str],
  match_type: str = 'EXACT',
) -> float:
  """
  Compute tool trajectory average score.
  Uses ADK-style match semantics for EXACT, IN_ORDER, and ANY_ORDER.

  Insight #2, #4: Evaluate the sequence of actions, not just the final output.
  """
  normalized_match_type = match_type.upper()

  if normalized_match_type == 'EXACT':
    return 1.0 if actual == expected else 0.0

  if normalized_match_type == 'IN_ORDER':
    if not expected:
      return 1.0
    cursor = 0
    for step in actual:
      if cursor < len(expected) and step == expected[cursor]:
        cursor += 1
    return 1.0 if cursor == len(expected) else 0.0

  if normalized_match_type == 'ANY_ORDER':
    if not expected:
      return 1.0
    remaining = list(actual)
    for step in expected:
      if step not in remaining:
        return 0.0
      remaining.remove(step)
    return 1.0

  raise ValueError(f'Unsupported match type: {match_type}')


def compute_response_match_score(
  actual_response: str,
  expected_response: str,
) -> float:
  """
  Compute response match score using ROUGE-1-like similarity.
  ADK default threshold: 0.8.

  Insight #3: Use both exact-match and semantic similarity.
  """
  if not expected_response:
    return 1.0
  if not actual_response:
    return 0.0

  # Token-level overlap (ROUGE-1 approximation)
  actual_tokens = set(actual_response.lower().split())
  expected_tokens = set(expected_response.lower().split())

  if not expected_tokens:
    return 1.0

  intersection = actual_tokens & expected_tokens
  precision = len(intersection) / len(actual_tokens) if actual_tokens else 0.0
  recall = len(intersection) / len(expected_tokens) if expected_tokens else 0.0

  if precision + recall == 0:
    return 0.0

  f1 = 2 * precision * recall / (precision + recall)

  # Also use sequence matcher for substring similarity
  seq_score = SequenceMatcher(None, actual_response.lower(), expected_response.lower()).ratio()

  return max(f1, seq_score)


def evaluate_single_case(
  eval_case: dict[str, Any],
  agent_result: dict[str, Any] | list[dict[str, Any]],
  criteria: dict[str, Any] | None = None,
) -> dict[str, Any]:
  """
  Evaluate a single test case against agent results.

  Insight #1, #5: Define success criteria and test with expected trajectories.

  Args:
    eval_case: ADK-format eval case with conversation, expected tool_uses, final_response.
    agent_result: Result from run_react_agent with trajectory and result.
    criteria: Dict of ADK-style criterion config objects. Defaults to ADK defaults.

  Returns:
    Evaluation result with scores and pass/fail.
  """
  if criteria is None:
    criteria = {
      'tool_trajectory_avg_score': {'threshold': 1.0, 'match_type': 'EXACT'},
      'response_match_score': 0.8,
    }

  actual_results = agent_result if isinstance(agent_result, list) else [agent_result]
  expected_turns = []

  conversation = eval_case.get('conversation', [])
  for turn in conversation:
    intermediate = turn.get('intermediate_data', {})
    tool_uses = intermediate.get('tool_uses', [])
    final = turn.get('final_response', {})
    parts = final.get('parts', [])
    expected_response = ''
    for part in parts:
      if part.get('text'):
        expected_response = part['text']
    expected_turns.append({
      'trajectory': [tool_use.get('name', '') for tool_use in tool_uses],
      'response': expected_response,
    })

  trajectory_config = criteria.get('tool_trajectory_avg_score', {'threshold': 1.0})
  response_config = criteria.get('response_match_score', 0.8)
  match_type = _resolve_match_type(trajectory_config)

  trajectory_scores: list[float] = []
  response_scores: list[float] = []
  actual_trajectories: list[list[str]] = []
  expected_trajectories: list[list[str]] = []
  actual_responses: list[str] = []
  expected_responses: list[str] = []

  total_turns = max(len(expected_turns), len(actual_results))
  for index in range(total_turns):
    expected_turn = expected_turns[index] if index < len(expected_turns) else {'trajectory': [], 'response': ''}
    actual_turn = actual_results[index] if index < len(actual_results) else {}
    actual_trajectory = actual_turn.get('trajectory', [])
    actual_response = actual_turn.get('result', {}).get('summary', '')

    actual_trajectories.append(actual_trajectory)
    expected_trajectories.append(expected_turn['trajectory'])
    actual_responses.append(actual_response)
    expected_responses.append(expected_turn['response'])

    trajectory_scores.append(
      compute_trajectory_score(actual_trajectory, expected_turn['trajectory'], match_type)
    )
    response_scores.append(
      compute_response_match_score(actual_response, expected_turn['response'])
    )

  traj_score = sum(trajectory_scores) / len(trajectory_scores) if trajectory_scores else 0.0
  resp_score = sum(response_scores) / len(response_scores) if response_scores else 0.0

  # Determine pass/fail
  traj_pass = traj_score >= _resolve_threshold(trajectory_config, 1.0)
  resp_pass = resp_score >= _resolve_threshold(response_config, 0.8)
  overall_pass = traj_pass and resp_pass

  result = {
    'id': f'eval-{uuid4().hex[:12]}',
    'eval_case_id': eval_case.get('eval_id', 'unknown'),
    'agent_id': actual_results[0].get('agent', 'react') if actual_results else 'react',
    'tool_trajectory_score': round(traj_score, 4),
    'response_match_score': round(resp_score, 4),
    'overall_pass': overall_pass,
    'actual_trajectory': json.dumps(actual_trajectories),
    'expected_trajectory': json.dumps(expected_trajectories),
    'actual_response': '\n\n'.join(actual_responses)[:2000],
    'expected_response': '\n\n'.join(expected_responses)[:2000],
    'metadata': json.dumps({
      'criteria': criteria,
      'trajectory_pass': traj_pass,
      'response_pass': resp_pass,
      'match_type': match_type,
      'per_turn': [
        {
          'turn_index': index,
          'trajectory_score': trajectory_scores[index],
          'response_score': response_scores[index],
        }
        for index in range(len(trajectory_scores))
      ],
      'duration_ms': sum(result.get('duration_ms', 0) or 0 for result in actual_results),
    }),
    'evaluated_at': datetime.now(timezone.utc).isoformat(),
  }

  return result


def evaluate_eval_set(
  eval_set: dict[str, Any],
  run_agent_fn,
  services,
  criteria: dict[str, Any] | None = None,
) -> dict[str, Any]:
  """
  Run evaluation for an entire eval set.

  Insight #6, #7: Support multi-turn and reproducible session state.

  Args:
    eval_set: ADK-format eval set with eval_cases array.
    run_agent_fn: Callable that runs the agent and returns result.
    services: ServiceRegistry for database access.
    criteria: Evaluation criteria thresholds.

  Returns:
    Summary with per-case results.
  """
  eval_set_id = eval_set.get('eval_set_id', 'unknown')
  eval_cases = eval_set.get('eval_cases', [])
  results = []
  passed = 0
  failed = 0

  logger.info('Starting evaluation of set %s with %d cases', eval_set_id, len(eval_cases))

  for case in eval_cases:
    eval_id = case.get('eval_id', 'unknown')
    conversation = case.get('conversation', [])

    # Get session input
    session_input = case.get('session_input', {})
    user_id = session_input.get('user_id', 'web-local')

    actual_results = []
    for turn in conversation:
      task = ''
      user_content = turn.get('user_content', {})
      parts = user_content.get('parts', [])
      for part in parts:
        if part.get('text'):
          task = part['text']
          break

      if not task:
        continue

      logger.info('Running eval case %s: %s', eval_id, task[:80])
      start = time.monotonic()
      try:
        actual_results.append(run_agent_fn(services, task, user_id=user_id))
      except Exception as err:
        logger.error('Eval case %s failed to run turn: %s', eval_id, err)
        actual_results.append({
          'agent': 'react',
          'status': 'failed',
          'result': {'summary': f'Error: {err}'},
          'trajectory': [],
          'duration_ms': int((time.monotonic() - start) * 1000),
        })

    if not actual_results:
      logger.warning('Skipping eval case %s: no runnable turns found', eval_id)
      continue

    # Evaluate
    eval_result = evaluate_single_case(case, actual_results, criteria)
    results.append(eval_result)

    if eval_result['overall_pass']:
      passed += 1
    else:
      failed += 1

    # Store result in SQLite
    try:
      services.note_store.insert_eval_result(eval_result)
    except Exception as err:
      logger.warning('Failed to store eval result: %s', err)

    logger.info(
      'Eval case %s: trajectory=%.2f response=%.2f pass=%s',
      eval_id, eval_result['tool_trajectory_score'],
      eval_result['response_match_score'], eval_result['overall_pass'],
    )

  return {
    'eval_set_id': eval_set_id,
    'total': len(results),
    'passed': passed,
    'failed': failed,
    'pass_rate': round(passed / len(results), 4) if results else 0.0,
    'results': results,
  }


def load_eval_set_from_file(filepath: str) -> dict[str, Any]:
  """Load an eval set from a .test.json or .evalset.json file."""
  with open(filepath, 'r') as f:
    return json.load(f)
