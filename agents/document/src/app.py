import os
import uuid
from typing import List, Optional, TypedDict, Dict

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from markdown import markdown
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer


load_dotenv()


class State(TypedDict):
    title: str
    markdown: str
    assets: Optional[List[str]]
    output_path: Optional[str]


def _markdown_to_text(md: str) -> str:
    html = markdown(md)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def document_node(state: State) -> Dict:
    artifact_dir = os.getenv("ARTIFACT_DIR", "/tmp/artifacts")
    os.makedirs(artifact_dir, exist_ok=True)
    filename = state.get("output_path") or os.path.join(
        artifact_dir, f"document-{uuid.uuid4().hex}.pdf"
    )

    doc = SimpleDocTemplate(filename, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    title = state.get("title") or "Document"
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    text = _markdown_to_text(state.get("markdown", ""))
    for line in text.splitlines():
        if line.strip():
            story.append(Paragraph(line, styles["BodyText"]))
            story.append(Spacer(1, 6))

    for asset in state.get("assets") or []:
        if os.path.exists(asset):
            story.append(Spacer(1, 12))
            story.append(Image(asset, width=400, height=300))

    doc.build(story)
    return {"output_path": filename}


builder = StateGraph(State)
builder.add_node("document", document_node)
builder.add_edge(START, "document")
builder.add_edge("document", END)

graph = builder.compile()
