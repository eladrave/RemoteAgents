import types
from agents.code_interpreter.src import app as code_app


def test_local_exec():
    result = code_app._local_exec("print('ok')", timeout=5)
    assert result["stdout"].strip() == "ok"
    assert result["exit_code"] == 0


def test_openai_code_interpreter(monkeypatch):
    class FakeResponse:
        output_text = "done"

        def model_dump(self):
            return {"output_text": "done"}

    class FakeClient:
        class responses:
            @staticmethod
            def create(model, input, tools):
                return FakeResponse()

    monkeypatch.setattr(code_app, "OpenAI", lambda: FakeClient())
    result = code_app._openai_code_interpreter("task", "gpt-5.2")
    assert result["provider"] == "openai"
    assert result["text"] == "done"


def test_gemini_code_execution(monkeypatch):
    class FakeResponse:
        text = "gemini ok"

        def model_dump(self):
            return {"text": "gemini ok"}

    class FakeModels:
        @staticmethod
        def generate_content(model, contents, config):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(code_app.genai, "Client", lambda: FakeClient())
    result = code_app._gemini_code_execution("task", "gemini-3-pro-preview")
    assert result["provider"] == "gemini"
    assert "gemini ok" in result["text"]
