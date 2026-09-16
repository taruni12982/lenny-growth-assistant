"""Small, transparent keyword retrieval for the demo transcript collection."""

import json
import re
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_transcripts.json"
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "our", "should", "the", "to",
    "we", "what", "with", "you", "your",
}


REQUIRED_FIELDS = {"id", "title", "speaker", "excerpt", "topics"}


def load_transcripts() -> list[dict[str, Any]]:
    """Load and validate the local, fictional sample dataset."""
    with DATASET_PATH.open("r", encoding="utf-8") as dataset_file:
        transcripts = json.load(dataset_file)

    if not isinstance(transcripts, list):
        raise ValueError("Demo transcript dataset must be a JSON list.")
    for index, transcript in enumerate(transcripts, start=1):
        if not isinstance(transcript, dict) or not REQUIRED_FIELDS <= transcript.keys():
            raise ValueError(
                f"Demo transcript {index} must include: {', '.join(sorted(REQUIRED_FIELDS))}."
            )
        if not all(isinstance(transcript[field], str) and transcript[field].strip()
                   for field in REQUIRED_FIELDS - {"topics"}):
            raise ValueError(f"Demo transcript {index} has an empty text field.")
        if not isinstance(transcript["topics"], list) or not all(
            isinstance(topic, str) and topic.strip() for topic in transcript["topics"]
        ):
            raise ValueError(f"Demo transcript {index} must have a non-empty topics list.")
    return transcripts


def _keywords(text: str) -> set[str]:
    return {
        word.lower()
        for word in re.findall(r"[a-zA-Z][a-zA-Z-]{1,}", text)
        if word.lower() not in STOP_WORDS
    }


def search_transcripts(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Rank passages by overlapping query keywords, without external services."""
    query_terms = _keywords(query)
    if not query_terms:
        return []

    matches = []
    for transcript in load_transcripts():
        searchable_text = " ".join(
            [transcript["title"], transcript["excerpt"], " ".join(transcript["topics"])]
        )
        passage_terms = _keywords(searchable_text)
        shared_terms = sorted(query_terms & passage_terms)
        if shared_terms:
            matches.append({
                **transcript,
                "score": len(shared_terms),
                "matched_terms": shared_terms,
            })

    return sorted(matches, key=lambda item: item["score"], reverse=True)[:limit]
