"""Web search with Brave Search as the primary provider.

Falls back to DuckDuckGo Lite when the Brave API is not configured or fails.
Results are returned in a provider-aware payload:
    { provider, fallback_used, results }
"""
from __future__ import annotations

import logging
import re
from typing import Any

import httpx

_LOG = logging.getLogger(__name__)
_BRAVE_URL = 'https://api.search.brave.com/res/v1/web/search'
_DDG_URL = 'https://html.duckduckgo.com/html/'
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; GraphiteBot/1.0)',
    'Accept': 'text/html',
}
_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
    re.DOTALL,
)
_TAG_RE = re.compile(r'<[^>]+>')


def _strip_tags(html: str) -> str:
    return _TAG_RE.sub('', html).strip()


def _search_brave(
    query: str,
    *,
    api_key: str,
    max_results: int,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    http_client = client or httpx.Client(timeout=8.0)
    try:
        resp = http_client.get(
            _BRAVE_URL,
            params={
                'q': query,
                'count': max_results,
                'text_decorations': 0,
                'search_lang': 'en',
                'result_filter': 'web',
            },
            headers={
                'X-Subscription-Token': api_key,
                'Accept': 'application/json',
                'User-Agent': _HEADERS['User-Agent'],
            },
        )
        resp.raise_for_status()
        payload = resp.json()
        results: list[dict[str, Any]] = []
        for item in payload.get('web', {}).get('results', [])[:max_results]:
            url = str(item.get('url', '')).strip()
            title = str(item.get('title', '')).strip()
            snippet = str(item.get('description', '')).strip()
            if url.startswith('http') and title:
                results.append({'title': title, 'url': url, 'snippet': snippet, 'provider': 'brave'})
        return results
    finally:
        if client is None:
            http_client.close()


def _search_duckduckgo(
    query: str,
    *,
    max_results: int,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    http_client = client or httpx.Client(timeout=8.0)
    try:
        resp = http_client.post(
            _DDG_URL,
            data={'q': query, 'b': '', 'kl': 'wt-wt'},
            headers=_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text
        results: list[dict[str, Any]] = []
        for m in _RESULT_RE.finditer(html):
            url = _strip_tags(m.group(1))
            title = _strip_tags(m.group(2))
            snippet = _strip_tags(m.group(3))
            if url.startswith('http') and title:
                results.append({'title': title, 'url': url, 'snippet': snippet, 'provider': 'duckduckgo'})
            if len(results) >= max_results:
                break
        return results
    finally:
        if client is None:
            http_client.close()


def search_web(
    query: str,
    max_results: int = 5,
    *,
    api_key: str = '',
    provider: str = 'auto',
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Return provider-aware web results for *query*."""
    normalized_provider = provider.strip().lower() or 'auto'
    fallback_used = False

    if normalized_provider in {'auto', 'brave'} and api_key.strip():
        try:
            results = _search_brave(query, api_key=api_key.strip(), max_results=max_results, client=client)
            _LOG.info('web_search(brave): %d results for %r', len(results), query)
            return {'provider': 'brave', 'fallback_used': False, 'results': results}
        except Exception as exc:
            fallback_used = True
            _LOG.warning('brave web_search failed, falling back: %s', exc)

    try:
        results = _search_duckduckgo(query, max_results=max_results, client=client)
        _LOG.info('web_search(duckduckgo): %d results for %r', len(results), query)
        return {
            'provider': 'duckduckgo' if results else ('brave' if normalized_provider == 'brave' else 'none'),
            'fallback_used': fallback_used,
            'results': results,
        }
    except Exception as exc:
        _LOG.warning('web_search failed: %s', exc)
        return {
            'provider': 'none',
            'fallback_used': fallback_used,
            'results': [],
        }


def format_results_for_prompt(results: list[dict[str, Any]]) -> str:
    if not results:
        return '(No live web results found.)'
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f'[W{i}] {r["title"]}\nURL: {r["url"]}\n{r["snippet"]}\n')
    return '\n'.join(lines)
