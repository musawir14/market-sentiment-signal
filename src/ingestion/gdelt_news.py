from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


@dataclass(frozen=True)
class NewsIngestResult:
    key: str
    docs: int
    cache_hit: bool
    path: Path


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _gdelt_dt(dt: datetime) -> str:
    # GDELT expects YYYYMMDDHHMMSS
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def build_gdelt_doc_url(
    query: str,
    start_dt: datetime,
    end_dt: datetime,
    max_records: int = 250,
) -> str:
    """
    GDELT DOC 2.0 endpoint.
    We request JSON and ask for a list of articles.
    """
    base = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(max_records),
        "startdatetime": _gdelt_dt(start_dt),
        "enddatetime": _gdelt_dt(end_dt),
        "sort": "HybridRel",
    }

    # Encode query params safely
    return base + "?" + "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())


def load_or_download_gdelt_articles(
    key: str,
    query: str,
    cache_dir: Path,
    lookback_days: int = 7,
    max_records: int = 250,
    timeout_sec: int = 30,
) -> Tuple[List[Dict[str, Any]], NewsIngestResult]:
    """
    Downloads recent articles from GDELT and caches the raw JSON response.

    Returns:
      - list of article dicts (payload["articles"])
      - NewsIngestResult (doc count, cache hit, path)
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Cache file name includes key + lookback window
    safe_key = key.strip().lower().replace("/", "_")
    cache_path = cache_dir / f"{safe_key}_{lookback_days}d_{max_records}r.json"

    # Cache hit: file exists + non-empty
    if cache_path.exists() and cache_path.stat().st_size > 0:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        return articles, NewsIngestResult(key=key, docs=len(articles), cache_hit=True, path=cache_path)

    end_dt = _utc_now()
    start_dt = end_dt - timedelta(days=lookback_days)

    url = build_gdelt_doc_url(query=query, start_dt=start_dt, end_dt=end_dt, max_records=max_records)

    resp = requests.get(url, timeout=timeout_sec)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "json" not in content_type.lower():
        snippet = (resp.text or "")[:300]
        raise ValueError(
            f"GDELT returned non-JSON (status={resp.status_code}, content_type='{content_type}'). "
            f"First 300 chars: {snippet!r}"
        )

    payload = resp.json()


    # Cache raw payload for reproducibility
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    return articles, NewsIngestResult(key=key, docs=len(articles), cache_hit=False, path=cache_path)
