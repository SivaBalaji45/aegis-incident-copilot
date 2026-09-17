"""Multimodal knowledge-base ingestion: PDF postmortems/runbooks where tables,
architecture diagrams, and dashboard screenshots carry information the plain
text extraction in `chunking.py` would flatten or drop.

Two HF task types back this:
  - Document Question Answering: query a PDF page directly (e.g. LayoutLM /
    Donut-style models) so a table's row/column structure survives, instead
    of collapsing it to whitespace-joined text.
  - Visual Document Retrieval: embed each *page image* (e.g. ColPali/ColQwen)
    so retrieval can return "page 4 has the relevant architecture diagram"
    even when the diagram has little to no extractable text.

Not implemented yet — `chunking.py` + `embeddings.py` (plain text, dense
vector) cover the text-only path end-to-end today. This module defines the
real interfaces the Retrieval agent will call once a document-QA/visual
retrieval model is wired in, so the pipeline's call sites don't need to
change shape later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PageImage:
    source_name: str
    page_number: int
    image_bytes: bytes


def ingest_pdf_pages(pdf_path: str) -> list[PageImage]:
    """Render each page of a PDF to an image for visual-document-retrieval
    embedding. TODO: implement with pypdfium2 or pdf2image; LlamaIndex's
    PDF connectors can supply both this and layout-aware text extraction."""
    raise NotImplementedError(
        "Wire in a PDF-to-image renderer (pypdfium2/pdf2image) here before "
        "using the visual-document-retrieval path."
    )


def embed_page_images(pages: list[PageImage]) -> list[list[float]]:
    """TODO: embed with a visual-document-retrieval model (e.g. ColPali/ColQwen
    via its HF checkpoint) rather than a text embedding model — these models
    embed the rendered page directly, preserving layout."""
    raise NotImplementedError("Wire in a visual-document-retrieval model (e.g. ColPali).")


def answer_from_page(question: str, page: PageImage) -> str:
    """TODO: run a document-QA model (e.g. a LayoutLM/Donut checkpoint) over
    `page` to answer `question` directly against the page image, preserving
    table structure that plain-text extraction would lose."""
    raise NotImplementedError("Wire in a document-QA model here.")
