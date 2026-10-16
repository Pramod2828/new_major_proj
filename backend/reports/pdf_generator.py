import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    """Generates professional executive anomaly detection reports with three-level risk classifications."""

    @classmethod
    def generate_report(
        cls,
        model_meta: Optional[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> bytes:
        """Generate PDF report in memory as bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0B1120")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B")
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=10,
            spaceAfter=5
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155")
        )
        badge_anomalous = ParagraphStyle(
            "BadgeAnomalous",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#DC2626")
        )
        badge_medium = ParagraphStyle(
            "BadgeMedium",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#D97706")
        )
        badge_normal = ParagraphStyle(
            "BadgeNormal",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#16A34A")
        )
        badge_unclassified = ParagraphStyle(
            "BadgeUnclassified",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#64748B")
        )

        story = []

        # Header Title
        story.append(Paragraph("SMART-LOG: SERVER SECURITY REPORT", title_style))
        gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        story.append(Paragraph(f"Automated Anomaly Detection Audit | Generated: {gen_time}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#06B6D4"), spaceAfter=12))

        # Executive Summary Section
        story.append(Paragraph("1. Executive Summary & Three-Level Classification Breakdown", h2_style))
        
        total = stats.get("total_logs", len(predictions))
        normal_cnt = stats.get("normal_count", sum(1 for p in predictions if (p.get("category") or "Normal").capitalize() == "Normal"))
        medium_cnt = stats.get("medium_count", sum(1 for p in predictions if (p.get("category") or "").capitalize() == "Medium"))
        anomalous_cnt = stats.get("anomalous_count", sum(1 for p in predictions if (p.get("category") or "").capitalize() in ("Anomalous", "Anomaly") or p.get("is_anomaly")))
        unclassified_cnt = stats.get("unclassified_count", sum(1 for p in predictions if (p.get("category") or "").capitalize() == "Unclassified"))

        classified_total = normal_cnt + medium_cnt + anomalous_cnt
        norm_pct = f"{round((normal_cnt / classified_total) * 100, 1)}%" if classified_total > 0 else "0.0%"
        med_pct = f"{round((medium_cnt / classified_total) * 100, 1)}%" if classified_total > 0 else "0.0%"
        anom_pct = f"{round((anomalous_cnt / classified_total) * 100, 1)}%" if classified_total > 0 else "0.0%"
        unclass_pct = f"{round((unclassified_cnt / total) * 100, 1)}%" if total > 0 else "0.0%"

        summary_data = [
            ["Risk Category", "Event Count", "Percentage of Classified", "Action Guidance"],
            ["Normal Baseline", str(normal_cnt), norm_pct, "Standard operational logs; no action required"],
            ["Medium Risk", str(medium_cnt), med_pct, "Borderline risk; correlate with host sessions"],
            ["Anomalous High Risk", str(anomalous_cnt), anom_pct, "Significant deviation; investigate processes/IPs"],
            ["Unclassified Events", str(unclassified_cnt), f"{unclass_pct} of total", "Model uncertainty; manual review needed"],
            ["Total Logs Audited", str(total), "100%", f"Active Model: {model_meta.get('name', 'N/A') if model_meta else 'None'}"]
        ]
        t_summary = Table(summary_data, colWidths=[110, 80, 120, 230])
        t_summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 12))

        # Model Performance & Metrics Section
        if model_meta and model_meta.get("metrics"):
            story.append(Paragraph("2. Active Model Validation & Decision Thresholds", h2_style))
            m = model_meta["metrics"]
            policy_info = m.get("classification_policy", {})
            t_norm = policy_info.get("threshold_normal", 0.30)
            t_anom = policy_info.get("threshold_anomaly", 0.70)

            metrics_table_data = [
                ["Evaluation Metric", "Measured Value on Test Split", "Policy Configuration", "Value"],
                ["Accuracy", f"{m.get('accuracy', 'N/A')}", "Normal Risk Upper Bound", f"P(Anomaly) < {t_norm}"],
                ["Precision (Anomaly)", f"{m.get('precision', 'N/A')}", "Medium Risk Range", f"{t_norm} <= P < {t_anom}"],
                ["Recall (Anomaly)", f"{m.get('recall', 'N/A')}", "Anomalous Threshold", f"P(Anomaly) >= {t_anom}"],
                ["F1-Score", f"{m.get('f1_score', 'N/A')}", "Algorithm", f"{model_meta.get('algorithm', 'N/A').upper()}"],
                ["ROC-AUC", f"{m.get('roc_auc', 'N/A')}", "Model Version", f"{model_meta.get('version', '1.0')}"]
            ]
            t_metrics = Table(metrics_table_data, colWidths=[120, 140, 140, 140])
            t_metrics.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_metrics)
            story.append(Spacer(1, 12))

        # Recent Flagged Records Section
        story.append(Paragraph("3. Audited Server Security Event Sample", h2_style))
        if not predictions:
            story.append(Paragraph("No log records processed in this report scope.", body_style))
        else:
            table_records = [["Timestamp", "Classification", "Risk / Conf", "Log Message Snippet", "Explanation"]]
            # Show up to 20 records prioritizing Anomalous and Medium
            priority_map = {"Anomalous": 3, "Medium": 2, "Unclassified": 1, "Normal": 0}
            sorted_preds = sorted(
                predictions,
                key=lambda x: (
                    priority_map.get(str(x.get("category", "")).capitalize(), 0),
                    float(x.get("risk_score") or x.get("probability") or 0.0)
                ),
                reverse=True
            )[:20]

            for p in sorted_preds:
                cat = str(p.get("category") or ("Anomalous" if p.get("is_anomaly") else "Normal")).capitalize()
                if cat in ("Anomalous", "Anomaly"):
                    p_style = badge_anomalous
                    cat_label = "ANOMALOUS"
                elif cat == "Medium":
                    p_style = badge_medium
                    cat_label = "MEDIUM"
                elif cat == "Normal":
                    p_style = badge_normal
                    cat_label = "NORMAL"
                else:
                    p_style = badge_unclassified
                    cat_label = "UNCLASSIFIED"

                status_cell = Paragraph(f"<b>{cat_label}</b>", p_style)

                prob = p.get("risk_score") if p.get("risk_score") is not None else p.get("probability")
                prob_cell = f"{round(float(prob) * 100, 1)}%" if prob is not None else "-"

                ts_cell = str(p.get("timestamp", ""))[:19]
                msg_snippet = str(p.get("raw_log", ""))[:70]
                msg_cell = Paragraph(msg_snippet, body_style)

                expl = str(p.get("explanation_summary") or "")[:85]
                expl_cell = Paragraph(expl, body_style)

                table_records.append([ts_cell, status_cell, prob_cell, msg_cell, expl_cell])

            t_logs = Table(table_records, colWidths=[90, 75, 55, 170, 150])
            t_logs.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1120")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_logs)

        # Build document
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
