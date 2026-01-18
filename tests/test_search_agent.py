from agents.search.src import app as search_app


def test_search_node(monkeypatch):
    class FakeClient:
        def __init__(self, api_key=None):
            self.api_key = api_key

        def search(self, query, max_results=5):
            return {"results": [{"title": "Result 1", "url": "https://example.com"}]}

    monkeypatch.setattr(search_app, "TavilyClient", FakeClient)
    result = search_app.search_node({"query": "test", "max_results": 1, "results": []})
    assert result["results"][0]["title"] == "Result 1"
