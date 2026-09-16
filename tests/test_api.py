from fastapi.testclient import TestClient

from app import main


def test_health_reports_healthy_ollama(monkeypatch):
    monkeypatch.setattr(
        main,
        "ollama_status",
        lambda: {"reachable": True, "model_available": True},
    )
    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ollama_model_available"] is True


def test_search_returns_numbered_sources():
    with TestClient(main.app) as client:
        response = client.get("/api/search", params={"query": "activation"})

    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert source["number"] == 1
    assert source["id"] == "demo-activation-001"


def test_chat_returns_clear_error_when_nothing_matches():
    with TestClient(main.app) as client:
        response = client.post("/api/chat", json={"question": "restaurant menu"})

    assert response.status_code == 404
    assert "No matching demo transcript" in response.json()["detail"]


def test_chat_uses_generated_answer_and_sources(monkeypatch):
    monkeypatch.setattr(main, "generate_answer", lambda question, passages: "Try one onboarding improvement. [Source 1]")
    with TestClient(main.app) as client:
        response = client.post("/api/chat", json={"question": "How do I improve activation?"})

    assert response.status_code == 200
    body = response.json()
    assert "[Source 1]" in body["answer"]
    assert body["sources"][0]["number"] == 1


def test_model_template_tokens_are_removed():
    answer = main.clean_model_answer("<|assistant|> Keep the onboarding simple.\n\n\n<|end|>")

    assert answer == "Keep the onboarding simple."


def test_model_html_is_converted_to_readable_plain_text():
    answer = main.clean_model_answer(
        "<div class='product'>Improve <strong>activation</strong>.</div><p>Measure the result.</p>"
    )

    assert answer == "Improve activation.\n\nMeasure the result."
    assert "<div" not in answer
    assert "<strong" not in answer


def test_json_wrapped_model_answer_is_unwrapped():
    answer = main.clean_model_answer('{"extract": "Test the price with a new-user segment. [Source 1]"}')

    assert answer == "Test the price with a new-user segment. [Source 1]"


def test_normal_model_answer_is_preserved():
    answer = main.clean_model_answer("Keep the normal answer unchanged. [Source 1]")

    assert answer == "Keep the normal answer unchanged. [Source 1]"
