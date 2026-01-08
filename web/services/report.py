from __future__ import annotations

from io import BytesIO
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from web.services.analysis import FullAnalysis, summarize_strengths
from web.services.marker import SubjectResult


PRIMARY = colors.HexColor("#3498DB")
TEXT = colors.HexColor("#2C3E50")


def _draw_section_title(pdf: canvas.Canvas, title: str, y: float) -> float:
    pdf.setFillColor(PRIMARY)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, title)
    return y - 0.6 * cm


def _draw_list(pdf: canvas.Canvas, items: List[str], y: float) -> float:
    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica", 11)
    for item in items:
        pdf.drawString(2.4 * cm, y, f"• {item}")
        y -= 0.5 * cm
    return y


def generate_student_report(
    student_name: str,
    writing_score: int,
    reading_result: SubjectResult,
    qrar_results: List[SubjectResult],
    analysis: FullAnalysis,
    logo_path: Optional[str] = None,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(2 * cm, height - 2 * cm, "Everest Tutoring")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(2 * cm, height - 2.7 * cm, "ASET Marking Report")

    if logo_path:
        try:
            pdf.drawImage(logo_path, width - 6 * cm, height - 3.5 * cm, 4 * cm, 2 * cm)
        except Exception:
            pass

    y = height - 4 * cm
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(TEXT)
    pdf.drawString(2 * cm, y, f"Student: {student_name}")
    y -= 0.6 * cm
    pdf.drawString(2 * cm, y, f"Writing score: {writing_score}")
    y -= 1 * cm

    y = _draw_section_title(pdf, "Scores", y)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2.4 * cm, y, f"Reading: {reading_result.correct}/{reading_result.total}")
    y -= 0.5 * cm
    for result in qrar_results:
        pdf.drawString(2.4 * cm, y, f"{result.subject}: {result.correct}/{result.total}")
        y -= 0.5 * cm

    y -= 0.5 * cm
    done_well, needs_improvement = summarize_strengths(analysis)

    y = _draw_section_title(pdf, "Done well", y)
    if done_well:
        y = _draw_list(pdf, done_well, y)
    else:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(2.4 * cm, y, "No areas above 51% yet.")
        y -= 0.5 * cm

    y -= 0.5 * cm
    y = _draw_section_title(pdf, "Needs improvement", y)
    if needs_improvement:
        y = _draw_list(pdf, needs_improvement, y)
    else:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(2.4 * cm, y, "No areas below 51%.")
        y -= 0.5 * cm

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
