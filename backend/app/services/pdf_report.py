from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SimilarityReport, User
from app.services.reporting import build_report_response


class PDFReportBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, report: SimilarityReport, user: User) -> str:
        reports_dir = Path(settings.STORAGE_DIR) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / f"similarity_report_{report.id}.pdf"

        payload = build_report_response(self.db, report, user)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="SmallMuted",
                parent=styles["BodyText"],
                fontSize=8,
                textColor=colors.HexColor("#4b5563"),
                leading=10,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=styles["Heading2"],
                fontSize=14,
                spaceBefore=14,
                spaceAfter=8,
            )
        )

        story = []
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "genevidence-similarity-check.png"
        if logo_path.exists():
            story.append(RLImage(str(logo_path), width=16 * cm, height=3.01 * cm))
        else:
            story.append(Paragraph("GenEvidence Similarity Check", styles["Title"]))
        story.append(Paragraph("Reporte de similitud academica biomedica", styles["Heading2"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Documento analizado: {payload.document_title}", styles["BodyText"]))
        story.append(Paragraph(f"Reporte #{payload.id}", styles["SmallMuted"]))
        story.append(Paragraph(f"Fecha: {payload.created_at.strftime('%Y-%m-%d %H:%M')}", styles["SmallMuted"]))
        story.append(Spacer(1, 0.7 * cm))

        story.append(Paragraph("Resumen ejecutivo", styles["SectionTitle"]))
        summary_data = [
            ["Metrica", "Resultado"],
            ["Similitud global", f"{payload.global_similarity_score:.2f}%"],
            ["Similitud excluyendo referencias", f"{payload.similarity_excluding_references_score:.2f}%"],
            ["Coincidencias detectadas", str(len(payload.matches))],
            ["Fuentes principales", str(len(payload.source_summary))],
        ]
        story.append(self._table(summary_data, [7 * cm, 7 * cm]))
        story.append(Spacer(1, 0.4 * cm))
        for warning in payload.warnings:
            story.append(Paragraph(warning, styles["SmallMuted"]))

        story.append(Paragraph("Tabla de fuentes", styles["SectionTitle"]))
        source_data = [["Fuente", "Coincidencias", "Score maximo", "Secciones"]]
        for source in payload.source_summary:
            source_data.append(
                [
                    source.source_document_label,
                    str(source.match_count),
                    f"{source.max_score:.2f}",
                    ", ".join(source.matched_sections),
                ]
            )
        story.append(self._table(source_data, [6 * cm, 2.5 * cm, 2.5 * cm, 5 * cm]))

        story.append(Paragraph("Similitud por seccion", styles["SectionTitle"]))
        section_data = [["Seccion", "Similitud"]]
        for section_name, score in sorted(payload.section_similarity.items()):
            section_data.append([section_name, f"{score:.2f}%"])
        story.append(self._table(section_data, [8 * cm, 4 * cm]))

        story.append(PageBreak())
        story.append(Paragraph("Detalle de coincidencias", styles["SectionTitle"]))
        for match in payload.matches[:80]:
            story.append(
                Paragraph(
                    f"{match.match_type} | {match.target_section} | {match.source_document_label} | "
                    f"score {match.similarity_score:.2f}",
                    styles["Heading4"],
                )
            )
            if match.is_common_method_phrase:
                story.append(
                    Paragraph(
                        "Marcada como frase metodologica comun: "
                        + ", ".join(match.common_phrase_labels),
                        styles["SmallMuted"],
                    )
                )
            story.append(Paragraph("<b>Fragmento analizado:</b> " + self._safe(match.target_text), styles["BodyText"]))
            story.append(Paragraph("<b>Fuente coincidente:</b> " + self._safe(match.source_text), styles["BodyText"]))
            story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("Nota metodologica", styles["SectionTitle"]))
        story.append(
            Paragraph(
                "El sistema combina fingerprints winnowing, similitud Jaccard y RapidFuzz para detectar "
                "coincidencias literales o casi literales contra documentos internos y fuentes academicas abiertas. "
                "La capa semantica experimental, cuando esta activa, usa embeddings multilingues para senalar "
                "posibles parafrasis revisables.",
                styles["BodyText"],
            )
        )
        story.append(Paragraph("Limitaciones", styles["SectionTitle"]))
        story.append(
            Paragraph(
                "El reporte compara contra la base interna disponible y contra metadatos/abstracts publicos de "
                "fuentes academicas abiertas. No equivale a una cobertura completa de internet, no reemplaza la "
                "revision academica humana, no declara plagio y sus porcentajes deben interpretarse como "
                "aproximaciones.",
                styles["BodyText"],
            )
        )

        doc.build(story)
        return str(output_path)

    @staticmethod
    def _table(data: list[list[str]], col_widths: list[float]) -> Table:
        table = Table(data, colWidths=col_widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    @staticmethod
    def _safe(text_value: str) -> str:
        return (
            " ".join(text_value.split())
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
