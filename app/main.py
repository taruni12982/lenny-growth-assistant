import json
import os
import re
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.retrieval import load_transcripts, search_transcripts

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "myModel:latest")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class Source(BaseModel):
    number: int
    id: str
    title: str
    speaker: str
    excerpt: str
    matched_terms: list[str]


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class SearchResponse(BaseModel):
    sources: list[Source]


class AnswerTextExtractor(HTMLParser):
    """Convert accidental model HTML into safe, readable plain text."""

    BLOCK_TAGS = {"div", "p", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4"}
    IGNORED_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.IGNORED_TAGS:
            self.ignored_depth += 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.IGNORED_TAGS and self.ignored_depth:
            self.ignored_depth -= 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def make_sources(passages: list[dict]) -> list[Source]:
    """Number sources once so API citations and visible source cards agree."""
    return [
        Source(
            number=index,
            id=passage["id"],
            title=passage["title"],
            speaker=passage["speaker"],
            excerpt=passage["excerpt"],
            matched_terms=passage["matched_terms"],
        )
        for index, passage in enumerate(passages, start=1)
    ]


def ollama_status() -> dict[str, bool]:
    """Report both server reachability and whether the selected model is installed."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()
        installed_models = {
            model.get("name") for model in response.json().get("models", [])
            if isinstance(model, dict)
        }
        return {"reachable": True, "model_available": OLLAMA_MODEL in installed_models}
    except requests.RequestException:
        return {"reachable": False, "model_available": False}


def clean_model_answer(answer: str) -> str:
    """Return safe, readable plain text from a local model response."""
    candidate = answer
    stripped_answer = answer.strip()
    if stripped_answer.startswith("{") and stripped_answer.endswith("}"):
        try:
            wrapped_answer = json.loads(stripped_answer)
        except json.JSONDecodeError:
            wrapped_answer = None
        if isinstance(wrapped_answer, dict):
            for field in ("extract", "answer", "response", "text", "content"):
                value = wrapped_answer.get(field)
                if isinstance(value, str) and value.strip():
                    candidate = value
                    break

    without_template_tokens = re.sub(r"<\|[^|>]+\|>", "", candidate)
    parser = AnswerTextExtractor()
    parser.feed(without_template_tokens)
    parser.close()
    plain_text = "".join(parser.parts)
    return re.sub(r"\n{3,}", "\n\n", plain_text).strip()


def generate_answer(question: str, passages: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source {index}] {passage['title']}\n{passage['excerpt']}"
        for index, passage in enumerate(passages, start=1)
    )
    prompt = f"""You are The Lenny Growth Assistant, a concise and practical product-growth helper.
Use only the fictional demo transcript passages below to answer the user's question.
Do not say or imply they are real Lenny Podcast content. If the passages do not fully answer the question, say what is unknown.
Give a helpful, actionable answer in plain language and do not use HTML. Cite supporting sources inline as [Source 1], [Source 2], etc.

User question: {question}

Fictional demo passages:
{context}
"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        answer = clean_model_answer(response.json().get("response", ""))
        if not answer:
            raise ValueError("Ollama returned an empty answer.")
        return answer
    except requests.ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Start Ollama, then confirm the configured model is installed.",
        ) from error
    except (requests.RequestException, ValueError) as error:
        raise HTTPException(status_code=502, detail=f"Ollama could not generate an answer: {error}") from error


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fail early with a useful message if the local demo data was accidentally edited incorrectly.
    load_transcripts()
    yield


app = FastAPI(title="The Lenny Growth Assistant", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check():
    status = ollama_status()
    return {
        "status": "ok" if status["reachable"] and status["model_available"] else "degraded",
        "ollama_reachable": status["reachable"],
        "ollama_model_available": status["model_available"],
        "ollama_model": OLLAMA_MODEL,
    }


@app.get("/api/search", response_model=SearchResponse)
def search(query: str = Query(min_length=2, max_length=1000)):
    """Expose keyword retrieval for demonstration and debugging without calling Ollama."""
    passages = search_transcripts(query, TOP_K_RESULTS)
    if not passages:
        raise HTTPException(
            status_code=404,
            detail="No matching demo transcript passages were found. Try activation, retention, pricing, growth loops, experiments, or user research.",
        )
    return SearchResponse(sources=make_sources(passages))


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    passages = search_transcripts(request.question, TOP_K_RESULTS)
    if not passages:
        raise HTTPException(
            status_code=404,
            detail="No matching demo transcript passages were found. Try words such as activation, retention, pricing, growth loop, experiment, or user research.",
        )

    answer = generate_answer(request.question, passages)
    sources = make_sources(passages)
    return ChatResponse(answer=answer, sources=sources)
