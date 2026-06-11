"""
Graphite ReAct Agent System — Google ADK-based with PlanReActPlanner.

Uses function tools for note CRUD, search, project analysis, and research.
Logs every action to agent_action_log for trajectory evaluation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger('graphite.react_agent')

APP_NAME = 'graphite'
SESSION_ID_PREFIX = 'graphite-session'


class ActionLogger:
  """Records every agent action into the active note store for trajectory evaluation."""

  def __init__(self, note_store, run_id: str):
    self.note_store = note_store
    self.run_id = run_id
    self.step_counter = 0
    self.trajectory: list[dict[str, Any]] = []

  def log(
    self,
    action_type: str,
    tool_name: str | None = None,
    tool_args: dict | None = None,
    tool_result: Any = None,
    reasoning: str | None = None,
    duration_ms: int | None = None,
  ) -> None:
    self.step_counter += 1
    entry = {
      'id': f'act-{uuid4().hex[:12]}',
      'run_id': self.run_id,
      'step_index': self.step_counter,
      'action_type': action_type,
      'tool_name': tool_name,
      'tool_args': json.dumps(tool_args) if tool_args else None,
      'tool_result': json.dumps(tool_result)[:4000] if tool_result else None,
      'reasoning': reasoning,
      'timestamp': datetime.now(timezone.utc).isoformat(),
      'duration_ms': duration_ms,
    }
    self.trajectory.append(entry)
    try:
      self.note_store.insert_action_log(entry)
    except Exception as err:
      logger.warning('Failed to log action: %s', err)

  def get_trajectory_names(self) -> list[str]:
    return [
      e.get('tool_name') or e['action_type']
      for e in self.trajectory
    ]


def _build_notes_context(note_store, user_id: str | None = None) -> str:
  """Build a context string from all user notes for the agent."""
  notes = note_store.get_all_notes_content(user_id)
  if not notes:
    return 'No notes found in the workspace.'
  parts = []
  for n in notes[:50]:  # limit context window
    parts.append(f"## Note: {n['title']}\nID: {n['id']}\n{n['content'][:2000]}\n")
  return '\n---\n'.join(parts)


def _create_note_tools(services):
  """Create function tools that the ReAct agent can call."""

  def search_notes(query: str, user_id: str = 'web-local') -> dict[str, Any]:
    """Search through all notes by keyword. Returns matching notes with title and excerpt.

    Args:
        query: The search query string to find in note titles and content.
        user_id: The user ID to filter notes. Defaults to 'web-local'.
  
    Returns:
        dict with status and list of matching notes.
    """
    result = services.search_notes(query, user_id=user_id, top_k=10)
    return {
      'status': 'success',
      'count': result['count'],
      'backend': result['backend'],
      'matches': result['matches'],
    }

  def get_note_by_id(note_id: str) -> dict[str, Any]:
    """Retrieve the full content of a specific note by its ID.

    Args:
        note_id: The unique identifier of the note to retrieve.

    Returns:
        dict with status and the full note content.
    """
    note = services.note_store.get_note(note_id)
    if note:
      return {'status': 'success', 'note': note}
    return {'status': 'error', 'error_message': f'Note {note_id} not found.'}

  def create_note(title: str, content: str, user_id: str = 'web-local') -> dict[str, Any]:
    """Create a new note with the given title and content.

    Args:
        title: The title for the new note.
        content: The markdown content of the note.
        user_id: The user ID who owns this note. Defaults to 'web-local'.

    Returns:
        dict with status and the saved note details.
    """
    from src.schemas import NoteSaveRequest

    try:
      saved = services.save_note(NoteSaveRequest(
        user_id=user_id, title=title, content=content,
        source_path='ai://react-agent', is_ai_generated=True,
      ))
      return {'status': 'success', 'note_id': saved['id'], 'title': saved['title']}
    except Exception as err:
      return {'status': 'error', 'error_message': str(err)}

  def update_note(note_id: str, title: str, content: str) -> dict[str, Any]:
    """Update an existing note's title and content.

    Args:
        note_id: The ID of the note to update.
        title: The new title for the note.
        content: The new content for the note.

    Returns:
        dict with status and updated note details.
    """
    from src.schemas import NoteSaveRequest

    existing = services.note_store.get_note(note_id)
    if not existing:
      return {'status': 'error', 'error_message': f'Note {note_id} not found.'}
    try:
      saved = services.save_note(NoteSaveRequest(
        id=note_id, user_id=existing['user_id'],
        title=title, content=content,
        source_path=existing.get('source_path'),
        is_ai_generated=existing.get('is_ai_generated', False),
      ))
      return {'status': 'success', 'note_id': saved['id'], 'title': saved['title']}
    except Exception as err:
      return {'status': 'error', 'error_message': str(err)}

  def list_all_notes(user_id: str = 'web-local') -> dict[str, Any]:
    """List all notes for a user with their titles and excerpts.

    Args:
        user_id: The user ID to list notes for. Defaults to 'web-local'.

    Returns:
        dict with status and list of notes (id, title, excerpt).
    """
    notes = services.list_notes(user_id)
    return {
      'status': 'success',
      'count': len(notes),
      'notes': [{'id': n['id'], 'title': n['title'], 'excerpt': n.get('excerpt', '')} for n in notes],
    }

  def analyze_project(project_path: str, project_name: str) -> dict[str, Any]:
    """Analyze a project directory and return its structure and key files.
    Used to generate detailed notes about a project's codebase.

    Args:
        project_path: Path to the project directory to analyze.
        project_name: Human-readable name of the project.

    Returns:
        dict with status and project analysis including file tree and key content.
    """
    try:
      return services.analyze_project_directory(project_path, project_name)
    except Exception as err:
      return {'status': 'error', 'error_message': str(err)}

  def run_financial_research(ticker: str, algorithms: str = 'ma,rsi,macd,bollinger') -> dict[str, Any]:
    """Run financial analysis on a stock ticker using technical indicators.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL').
        algorithms: Comma-separated list of algorithms: ma, rsi, macd, bollinger.

    Returns:
        dict with analysis results including signals and metrics.
    """
    algo_list = [a.strip() for a in algorithms.split(',')]
    try:
      result = services.run_research(ticker, algo_list)
      return {'status': 'success', 'analysis': result}
    except Exception as err:
      return {'status': 'error', 'error_message': str(err)}

  return [
    search_notes,
    get_note_by_id,
    create_note,
    update_note,
    list_all_notes,
    analyze_project,
    run_financial_research,
  ]


def _create_react_agent(services, user_id: str = 'web-local') -> LlmAgent:
  """Create a ReAct agent with PlanReActPlanner and note context."""
  notes_context = _build_notes_context(services.note_store, user_id)
  tools = _create_note_tools(services)

  model = services.settings.gemini_model or 'gemini-3.5-flash'

  agent = LlmAgent(
    model=model,
    name='graphite_react_agent',
    description=(
      'A ReAct agent for the Graphite workspace. Can search, create, and update notes, '
      'analyze projects to generate documentation, and run financial research. '
      'Has full access to the user\'s notes context.'
    ),
    instruction=f"""You are the Graphite ReAct Agent, an intelligent assistant for a Supabase-backed workspace.

You have access to the user's notes and can perform these actions:
- Search notes by keyword
- Read specific notes by ID
- Create new notes with markdown content
- Update existing notes
- List all notes
- Analyze project directories and generate detailed notes about them
- Run financial research on stock tickers

IMPORTANT CONTEXT - User's current notes:
{notes_context}

When the user asks you to:
1. "Take a project" or "Analyze project at <path>": Use analyze_project tool, then create detailed notes.
2. "Search for X": Use search_notes tool.
3. "Create a note about X": Use create_note tool with well-structured markdown.
4. "Research <ticker>": Use run_financial_research tool and summarize findings.
5. General questions: Use your knowledge + notes context to answer.

Always be thorough. When generating notes from project analysis:
- Include architecture overview, tech stack, file structure, setup instructions
- Note key design patterns and dependencies
- Provide actionable developer notes

Respond with clear, structured answers. Use markdown formatting.""",
    tools=tools,
    planner=PlanReActPlanner(),
  )
  return agent


async def run_react_agent(
  services,
  task: str,
  user_id: str = 'web-local',
  agent_id: str = 'react',
) -> dict[str, Any]:
  """
  Execute a ReAct agent task with full action logging and trajectory tracking.

  Returns the agent result plus trajectory info for evaluation.
  """
  run_id = f'run-{uuid4().hex[:12]}'
  started_at = datetime.now(timezone.utc).isoformat()
  start_time = time.monotonic()

  # Log the run start
  services.note_store.insert_agent_run({
    'id': run_id,
    'agent_id': agent_id,
    'user_id': user_id,
    'task': task,
    'status': 'running',
    'started_at': started_at,
  })

  action_logger = ActionLogger(services.note_store, run_id)
  action_logger.log('reasoning', reasoning=f'Starting task: {task}')

  try:
    agent = _create_react_agent(services, user_id)
    session_service = InMemorySessionService()
    session = await session_service.create_session(
      app_name=APP_NAME,
      user_id=user_id,
      session_id=f'{SESSION_ID_PREFIX}-{run_id}',
    )
    runner = Runner(
      agent=agent,
      app_name=APP_NAME,
      session_service=session_service,
    )

    content = types.Content(
      role='user',
      parts=[types.Part(text=task)],
    )

    final_response = ''
    events_collected = []

    async for event in runner.run_async(
      user_id=user_id,
      session_id=session.id,
      new_message=content,
    ):
      events_collected.append(event)

      # Log tool calls
      if event.content and event.content.parts:
        for part in event.content.parts:
          if part.function_call:
            fc = part.function_call
            step_start = time.monotonic()
            action_logger.log(
              'tool_call',
              tool_name=fc.name,
              tool_args=dict(fc.args) if fc.args else {},
            )
          elif part.function_response:
            fr = part.function_response
            action_logger.log(
              'observation',
              tool_name=fr.name if hasattr(fr, 'name') else None,
              tool_result=fr.response if hasattr(fr, 'response') else str(fr),
            )
          elif part.text and part.text.strip():
            text = part.text.strip()
            # Check for planning/reasoning markers from PlanReActPlanner
            if '/*PLANNING*/' in text or '/*REASONING*/' in text:
              action_logger.log('reasoning', reasoning=text[:2000])
            elif event.is_final_response():
              final_response = text
              action_logger.log('llm_call', reasoning=f'Final response generated ({len(text)} chars)')

      if event.is_final_response() and event.content and event.content.parts:
        for part in event.content.parts:
          if part.text:
            final_response = part.text.strip()

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    # Update run as completed
    services.note_store.update_agent_run(run_id, {
      'status': 'completed',
      'result_json': json.dumps({'response': final_response[:5000]}),
      'completed_at': datetime.now(timezone.utc).isoformat(),
      'duration_ms': elapsed_ms,
    })

    action_logger.log('reasoning', reasoning='Task completed successfully')

    return {
      'run_id': run_id,
      'agent': agent_id,
      'agent_name': 'Graphite ReAct Agent',
      'status': 'completed',
      'result': {
        'summary': final_response,
        'action_plan': [f'Step {i+1}: {e.get("tool_name") or e["action_type"]}' for i, e in enumerate(action_logger.trajectory)],
        'next_actions': [],
      },
      'trajectory': action_logger.get_trajectory_names(),
      'duration_ms': elapsed_ms,
      'events_count': len(events_collected),
    }

  except Exception as err:
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    error_msg = str(err)
    logger.exception('ReAct agent run failed: %s', error_msg)

    action_logger.log('error', reasoning=f'Agent failed: {error_msg}')

    services.note_store.update_agent_run(run_id, {
      'status': 'failed',
      'error_message': error_msg[:1000],
      'completed_at': datetime.now(timezone.utc).isoformat(),
      'duration_ms': elapsed_ms,
    })

    return {
      'run_id': run_id,
      'agent': agent_id,
      'agent_name': 'Graphite ReAct Agent',
      'status': 'failed',
      'result': {
        'summary': f'Agent execution failed: {error_msg}',
        'action_plan': [],
        'next_actions': ['Review error and retry'],
      },
      'trajectory': action_logger.get_trajectory_names(),
      'duration_ms': elapsed_ms,
      'error': error_msg,
    }


def run_react_agent_sync(
  services,
  task: str,
  user_id: str = 'web-local',
  agent_id: str = 'react',
) -> dict[str, Any]:
  """Synchronous wrapper for run_react_agent."""
  try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
      import concurrent.futures
      with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(
          asyncio.run,
          run_react_agent(services, task, user_id, agent_id),
        )
        return future.result(timeout=120)
    else:
      return loop.run_until_complete(
        run_react_agent(services, task, user_id, agent_id)
      )
  except RuntimeError:
    return asyncio.run(
      run_react_agent(services, task, user_id, agent_id)
    )
