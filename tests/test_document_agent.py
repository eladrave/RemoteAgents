import os
from agents.document.src import app as doc_app


def test_document_generation(tmp_path):
    out_path = tmp_path / "doc.pdf"
    result = doc_app.document_node(
        {"title": "Test", "markdown": "# Hello\nWorld", "assets": [], "output_path": str(out_path)}
    )
    assert os.path.exists(result["output_path"])
    assert result["output_path"].endswith(".pdf")
