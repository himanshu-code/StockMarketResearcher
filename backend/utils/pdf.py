"""Convert a Markdown string to PDF bytes."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def markdown_to_pdf(markdown_text: str) -> bytes:
    """
    Convert Markdown to PDF bytes using md2pdf.
    Falls back to a plain-text PDF via fpdf if md2pdf is unavailable.
    """
    try:
        from md2pdf.core import md2pdf  # type: ignore

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "report.pdf"
            md2pdf(str(out_path), md_content=markdown_text)
            return out_path.read_bytes()
    except (ImportError, OSError) as e:
        logger.warning(
            f"[pdf] md2pdf/WeasyPrint library or dependency missing ({type(e).__name__}: {e}) "
            "— falling back to fpdf plain-text export"
        )
        return _plain_text_pdf(markdown_text)
    except Exception:
        logger.exception("[pdf] md2pdf conversion failed — falling back to fpdf plain-text export")
        try:
            return _plain_text_pdf(markdown_text)
        except Exception:
            logger.exception("[pdf] fpdf fallback also failed")
            raise


def _clean_text_for_fpdf(text: str) -> str:
    """Replace common Unicode characters with Latin-1 equivalents, and sanitize the rest."""
    replacements = {
        "\u2014": "--",  # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "*",   # bullet point
        "\u2026": "...", # ellipsis
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _plain_text_pdf(text: str) -> bytes:
    """Minimal plain-text PDF using fpdf as a last-resort fallback."""
    try:
        from fpdf import FPDF  # type: ignore

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        for line in text.splitlines():
            cleaned_line = _clean_text_for_fpdf(line)
            pdf.multi_cell(pdf.epw, 5, cleaned_line, new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
    except ImportError as exc:
        raise RuntimeError("Neither md2pdf nor fpdf is installed.") from exc
