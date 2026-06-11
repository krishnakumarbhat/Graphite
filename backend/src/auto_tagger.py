"""Auto-tagging: classify notes into faceted topic tags.

Tags are derived from keyword rules first (fast, zero-cost), then
Gemini for ambiguous notes.  Tags stored in note metadata field.
"""
from __future__ import annotations

import re
from typing import Any


# ── Rule-based tag definitions ─────────────────────────────────────────────
_RULES: list[tuple[str, list[str]]] = [
    ('stocks', ['aapl', 'nvda', 'msft', 'googl', 'amzn', 'tsla', 'stock', 'ticker',
                'dividend', 'portfolio', 'bull', 'bear', 'earnings', 'market cap',
                'options', 'puts', 'calls', 'csp', 'buy shares', 'price target']),
    ('crypto', ['bitcoin', 'btc', 'eth', 'ethereum', 'crypto', 'defi', 'nft', 'blockchain',
                'solana', 'binance', 'coinbase']),
    ('machine-learning', ['neural network', 'lstm', 'gru', 'transformer', 'attention',
                           'fine-tune', 'gradient', 'backpropagation', 'loss function',
                           'epoch', 'batch size', 'overfitting', 'regularization', 'cnn',
                           'rnn', 'bert', 'gpt', 'llm', 'embedding', 'vector']),
    ('deep-learning', ['pytorch', 'tensorflow', 'keras', 'cuda', 'gpu training',
                        'convolutional', 'residual', 'batch norm', 'dropout']),
    ('reinforcement-learning', ['q-learning', 'policy gradient', 'reward', 'agent',
                                  'environment', 'mdp', 'ppo', 'dqn', 'actor-critic',
                                  'gymnasium', 'openai gym']),
    ('data-engineering', ['pipeline', 'etl', 'spark', 'dbt', 'airflow', 'kafka',
                           'data warehouse', 'snowflake', 'bigquery', 'redshift',
                           'schema', 'lineage', 'data quality', 'ingestion', 'batch']),
    ('altimate', ['altimate', 'altimate.ai', 'sql lint', 'dbt review', 'schema tool',
                   'lineage tool', 'finops', 'memory tool']),
    ('career', ['job', 'resume', 'interview', 'salary', 'offer', 'linkedin',
                 'hiring', 'recruiter', 'role fit', 'tech stack', 'google', 'amazon',
                 'stripe', 'startup', 'promotion', 'skills']),
    ('personal', ['workout', 'sleep', 'travel', 'bucket list', 'book', 'reading',
                   'habit', 'goal', 'productivity', 'remote work', 'health']),
    ('research', ['paper', 'arxiv', 'experiment', 'ablation', 'baseline', 'benchmark',
                   'dataset', 'huggingface', 'state of the art', 'sota']),
]

_TOKEN_RE = re.compile(r'[a-z0-9]+')


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def tag_note(title: str, content: str) -> list[str]:
    """Return list of tags for a note using keyword rules."""
    combined = f'{title} {content}'.lower()
    assigned: list[str] = []
    for tag, keywords in _RULES:
        for kw in keywords:
            if kw in combined:
                assigned.append(tag)
                break
    return assigned or ['general']


def enrich_note(note: dict[str, Any]) -> dict[str, Any]:
    """Attach `tags` key to a note dict in-place and return it."""
    tags = tag_note(note.get('title', ''), note.get('content', ''))
    note['tags'] = tags
    return note


def bulk_tag_notes(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [enrich_note(dict(n)) for n in notes]
