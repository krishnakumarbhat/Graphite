import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Callable


_TOKEN_RE = re.compile(r'[a-z0-9]{2,}')


@dataclass(slots=True)
class ResearchChunk:
  id: str
  title: str
  source_label: str
  source_path: str
  content: str
  order: int


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
  normalized = text.strip()
  if not normalized:
    return []

  safe_overlap = max(min(overlap, chunk_size // 2), 0)
  step = max(chunk_size - safe_overlap, 1)
  chunks: list[str] = []
  for start in range(0, len(normalized), step):
    chunk = normalized[start:start + chunk_size].strip()
    if not chunk:
      continue
    chunks.append(chunk)
    if start + chunk_size >= len(normalized):
      break
  return chunks


def build_chunks(
  documents: list[dict[str, str]],
  *,
  chunk_size: int,
  overlap: int,
) -> list[ResearchChunk]:
  chunks: list[ResearchChunk] = []
  for document_index, document in enumerate(documents):
    title = document['title'].strip() or f'Document {document_index + 1}'
    source_label = document['source_label'].strip() or title
    source_path = document.get('source_path', '').strip()
    for chunk_index, piece in enumerate(chunk_text(document['content'], chunk_size, overlap)):
      digest = hashlib.md5(f'{source_label}:{chunk_index}:{piece[:120]}'.encode()).hexdigest()[:12]
      chunks.append(
        ResearchChunk(
          id=f'chunk-{digest}',
          title=title,
          source_label=source_label,
          source_path=source_path,
          content=piece,
          order=document_index * 1000 + chunk_index,
        )
      )
  return chunks


def rank_chunks(
  query: str,
  chunks: list[ResearchChunk],
  *,
  max_chunks: int,
  embedding_provider: Callable[[str], list[float]] | None = None,
) -> list[dict[str, Any]]:
  if not chunks:
    return []

  lexical_ranked = sorted(
    ((lexical_score(query, chunk), chunk) for chunk in chunks),
    key=lambda item: item[0],
    reverse=True,
  )

  shortlist_size = max(max_chunks * 2, min(10, len(lexical_ranked)))
  shortlist = lexical_ranked[:shortlist_size]

  if embedding_provider is None:
    candidates = [
      _serialize_ranked_chunk(
        score,
        chunk,
        lexical_rank=score,
        semantic_rank=0.0,
      )
      for score, chunk in shortlist
    ]
    return cross_encoder_rerank(query, candidates, max_items=max_chunks)

  query_embedding = embedding_provider(query)
  candidates: list[dict[str, Any]] = []
  for lexical_rank, chunk in shortlist:
    chunk_embedding = embedding_provider(f'{chunk.title}\n\n{chunk.content[:1800]}')
    semantic_rank = cosine_similarity(query_embedding, chunk_embedding)
    candidates.append(
      _serialize_ranked_chunk(
        (semantic_rank * 0.7) + (lexical_rank * 0.3),
        chunk,
        lexical_rank=lexical_rank,
        semantic_rank=semantic_rank,
      )
    )

  return cross_encoder_rerank(query, candidates, max_items=max_chunks)


def render_chunks_for_prompt(chunks: list[dict[str, Any]]) -> str:
  rendered: list[str] = []
  for index, chunk in enumerate(chunks, start=1):
    rendered.extend([
      f'[S{index}] {chunk["source_label"]}',
      f'Title: {chunk["title"]}',
      f'Source path: {chunk["source_path"] or "inline://source"}',
      chunk['content'][:1800],
      '',
    ])
  return '\n'.join(rendered).strip()


def document_lexical_score(query: str, title: str, content: str) -> float:
  return lexical_score(
    query,
    ResearchChunk(
      id='rank-doc',
      title=title,
      source_label=title or 'Document',
      source_path='',
      content=content,
      order=0,
    ),
  )


def lexical_score(query: str, chunk: ResearchChunk) -> float:
  query_tokens = tokenize(query)
  if not query_tokens:
    return 0.0

  title_tokens = tokenize(chunk.title)
  content_tokens = tokenize(chunk.content)
  overlap = len(query_tokens & content_tokens)
  title_overlap = len(query_tokens & title_tokens)
  phrase_bonus = 0.4 if query.lower().strip() in chunk.content.lower() else 0.0
  density = overlap / max(len(query_tokens), 1)
  title_density = title_overlap / max(len(query_tokens), 1)
  length_bonus = min(len(chunk.content) / 2000.0, 0.2)
  return density + (title_density * 0.6) + phrase_bonus + length_bonus


def cosine_similarity(left: list[float], right: list[float]) -> float:
  if not left or not right:
    return 0.0

  size = min(len(left), len(right))
  numerator = sum(left[index] * right[index] for index in range(size))
  left_norm = math.sqrt(sum(value * value for value in left[:size]))
  right_norm = math.sqrt(sum(value * value for value in right[:size]))
  if left_norm == 0 or right_norm == 0:
    return 0.0
  return numerator / (left_norm * right_norm)


def tokenize(text: str) -> set[str]:
  return set(_TOKEN_RE.findall(text.lower()))


def cross_encoder_score(query: str, title: str, content: str) -> float:
  normalized_query = query.lower().strip()
  query_tokens = _TOKEN_RE.findall(normalized_query)
  if not query_tokens:
    return 0.0

  title_tokens = _TOKEN_RE.findall(title.lower())
  doc_tokens = _TOKEN_RE.findall(f'{title}\n{content}'.lower())
  if not doc_tokens:
    return 0.0

  query_set = set(query_tokens)
  doc_set = set(doc_tokens)
  title_set = set(title_tokens)
  unigram_coverage = len(query_set & doc_set) / max(len(query_set), 1)
  title_coverage = len(query_set & title_set) / max(len(query_set), 1)

  query_bigrams = set(zip(query_tokens, query_tokens[1:]))
  doc_bigrams = set(zip(doc_tokens, doc_tokens[1:]))
  if query_bigrams:
    bigram_coverage = len(query_bigrams & doc_bigrams) / len(query_bigrams)
  else:
    bigram_coverage = unigram_coverage

  ordered_score = _ordered_match_score(query_tokens, doc_tokens)
  phrase_bonus = 1.0 if normalized_query and normalized_query in f'{title}\n{content}'.lower() else 0.0

  return round(
    (unigram_coverage * 0.34)
    + (bigram_coverage * 0.2)
    + (ordered_score * 0.24)
    + (title_coverage * 0.17)
    + (phrase_bonus * 0.05),
    6,
  )


def cross_encoder_rerank(
  query: str,
  items: list[dict[str, Any]],
  *,
  max_items: int,
  title_key: str = 'title',
  text_key: str = 'content',
  base_score_key: str = 'score',
) -> list[dict[str, Any]]:
  reranked: list[dict[str, Any]] = []
  for item in items:
    title = str(item.get(title_key, ''))
    content = str(item.get(text_key) or item.get('excerpt') or '')
    lexical_rank = float(item.get('lexical_score', document_lexical_score(query, title, content)))
    semantic_rank = float(item.get('semantic_score', 0.0))
    base_score = float(item.get(base_score_key, 0.0))
    cross_rank = cross_encoder_score(query, title, content)
    final_score = (cross_rank * 0.45) + (semantic_rank * 0.3) + (lexical_rank * 0.15) + (base_score * 0.1)

    reranked.append(
      {
        **item,
        'score': round(final_score, 6),
        'lexical_score': round(lexical_rank, 6),
        'semantic_score': round(semantic_rank, 6),
        'cross_encoder_score': round(cross_rank, 6),
      }
    )

  reranked.sort(
    key=lambda item: (
      float(item.get('score', 0.0)),
      float(item.get('cross_encoder_score', 0.0)),
      float(item.get('semantic_score', 0.0)),
      float(item.get('lexical_score', 0.0)),
    ),
    reverse=True,
  )
  return reranked[:max_items]


def _ordered_match_score(query_tokens: list[str], doc_tokens: list[str]) -> float:
  if not query_tokens or not doc_tokens:
    return 0.0

  positions: list[int] = []
  cursor = 0
  for token in query_tokens:
    try:
      index = doc_tokens.index(token, cursor)
    except ValueError:
      break
    positions.append(index)
    cursor = index + 1

  if not positions:
    return 0.0

  match_ratio = len(positions) / len(query_tokens)
  span = max(positions[-1] - positions[0] + 1, 1)
  compactness = len(positions) / span
  return min((match_ratio * 0.65) + (compactness * 0.35), 1.0)


def _serialize_ranked_chunk(
  score: float,
  chunk: ResearchChunk,
  *,
  lexical_rank: float | None = None,
  semantic_rank: float | None = None,
) -> dict[str, Any]:
  return {
    'id': chunk.id,
    'title': chunk.title,
    'source_label': chunk.source_label,
    'source_path': chunk.source_path,
    'content': chunk.content,
    'score': round(score, 6),
    'lexical_score': round(lexical_rank if lexical_rank is not None else score, 6),
    'semantic_score': round(semantic_rank if semantic_rank is not None else 0.0, 6),
  }