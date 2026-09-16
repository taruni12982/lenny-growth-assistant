# The Lenny Growth Assistant

A local product-growth question-and-answer demo. It searches a small transcript-style dataset with keywords, gives the most relevant passages to a local Ollama model, and shows the passages used beneath each answer.

> **Important data disclaimer:** The current dataset is original, fictional demo content created for this project. It is not real Lenny Podcast transcript material.

## Features currently implemented

- FastAPI backend serving a browser-based HTML, CSS, and JavaScript interface
- Local Ollama generation using `myModel:latest` by default
- Keyword-based search across six fictional sample passages
- Chat answers grounded in retrieved passages
- Clear, numbered source cards with title, fictional speaker, excerpt, and matched keywords
- Loading state and friendly error messages in the UI
- Special chat-template token cleanup, so artifacts such as `<|assistant|>` are not shown
- `GET /health` reports API health, Ollama reachability, and configured-model availability
- `GET /api/search?query=activation` demonstrates retrieval without calling the model
- `POST /api/chat` retrieves passages and generates an answer
- Automated tests for retrieval, API responses, error handling, sources, and token cleanup

## Run the project (Windows PowerShell)

Open PowerShell in the project folder:

```powershell
cd C:\Users\narra\Downloads\lenny-growth-assistant
```

For a first-time setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run this once for the current window, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Make sure Ollama is running. If it is not already running in the background, open a separate PowerShell window and run:

```powershell
ollama serve
```

In the project PowerShell window, start the application:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser. Do not start a second `ollama serve` if one is already running.

## How to test it

### Browser demo

1. Open http://127.0.0.1:8000.
2. Point out the visible fictional-data disclaimer.
3. Click **Improve activation** or ask: `How can I improve activation for new users?`
4. Show the temporary loading message, then the answer and numbered source cards.
5. Ask `What restaurant should I visit?` to demonstrate the friendly no-match error.

### API checks

- Health: http://127.0.0.1:8000/health
- Keyword retrieval: http://127.0.0.1:8000/api/search?query=activation
- Interactive API docs: http://127.0.0.1:8000/docs

### Automated tests

Install the test-only packages once, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

## Current limitations

- The six sample passages are fictional and intentionally small; they only cover a few growth topics.
- Search is keyword-based, so it may miss a relevant passage expressed with different wording.
- There is no chat history, authentication, persistent storage, streaming output, or production monitoring.
- Responses depend on the quality and speed of the local Ollama model.
- The model is asked to add `[Source n]` references, but the numbered source cards are the reliable, visible citation record.

## Adding real, properly sourced transcripts later

Only add content you are permitted to use. Keep a record of each episode's official URL, title, publication date, licensing/permission status, and the method used to obtain its transcript. Store each passage in a separate data file or database record with its source metadata, and make the UI link to the original official episode or transcript page. Do not describe third-party material as licensed or official unless you have verified that permission.

When the dataset grows, replace or supplement keyword matching with semantic retrieval, but continue showing the exact passages and source metadata used for every answer.

## Project layout

```
app/main.py          FastAPI routes, Ollama calls, and answer cleanup
app/retrieval.py     Local keyword retrieval and dataset validation
data/                Fictional demo dataset
static/              Browser interface files
tests/               Automated backend and retrieval tests
.env.example         Configuration template
requirements.txt     Runtime packages
requirements-dev.txt Test-only packages
```
