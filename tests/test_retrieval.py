from app.retrieval import search_transcripts


def test_activation_query_returns_activation_passage():
    results = search_transcripts("How can we improve new user activation?")

    assert results
    assert results[0]["id"] == "demo-activation-001"
    assert "activation" in results[0]["matched_terms"]


def test_unrelated_query_returns_no_results():
    assert search_transcripts("restaurant menu reservation") == []

