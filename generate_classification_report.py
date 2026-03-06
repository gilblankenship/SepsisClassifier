"""Generate PDF classification report for Su et al. 2021 simulated patient data."""

import sys
sys.path.insert(0, "/Users/gilblankenship/Documents/Projects/SepsisClassifer")

import pandas as pd
import numpy as np
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from sepsis.model_export import SepsisPredictor

# ---------------------------------------------------------------------------
# Load data & run classifier
# ---------------------------------------------------------------------------
df = pd.read_csv("data/su2021_mapped_for_classifier.csv")
predictor = SepsisPredictor.from_exported("random_forest")
result = predictor.predict_batch(df)

# ---------------------------------------------------------------------------
# PDF setup
# ---------------------------------------------------------------------------
OUTPUT = "Su2021_Classification_Report.pdf"
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=landscape(letter),
    topMargin=0.5 * inch,
    bottomMargin=0.5 * inch,
    leftMargin=0.5 * inch,
    rightMargin=0.5 * inch,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "ReportTitle", parent=styles["Title"], fontSize=18, spaceAfter=4,
    textColor=colors.HexColor("#1a365d"),
)
subtitle_style = ParagraphStyle(
    "Subtitle", parent=styles["Normal"], fontSize=11, spaceAfter=2,
    textColor=colors.HexColor("#4a5568"),
)
section_style = ParagraphStyle(
    "SectionHead", parent=styles["Heading2"], fontSize=13, spaceBefore=14,
    spaceAfter=6, textColor=colors.HexColor("#1a365d"),
)
note_style = ParagraphStyle(
    "Note", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#718096"),
    spaceAfter=4,
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=9, spaceAfter=4,
    textColor=colors.HexColor("#2d3748"),
)
cell_style = ParagraphStyle("Cell", fontSize=7.5, leading=9)
cell_center = ParagraphStyle("CellC", fontSize=7.5, leading=9, alignment=TA_CENTER)
cell_right = ParagraphStyle("CellR", fontSize=7.5, leading=9, alignment=TA_RIGHT)
header_style = ParagraphStyle(
    "Header", fontSize=7.5, leading=9, alignment=TA_CENTER,
    textColor=colors.white, fontName="Helvetica-Bold",
)

elements = []

# ---------------------------------------------------------------------------
# Title page content
# ---------------------------------------------------------------------------
elements.append(Spacer(1, 0.3 * inch))
elements.append(Paragraph("SepsisDx Classification Report", title_style))
elements.append(Paragraph(
    "Su et al. 2021 — Simulated Patient Data from Urinary Biomarker Panel Study",
    subtitle_style,
))
elements.append(Paragraph(
    f"Generated {datetime.now().strftime('%B %d, %Y at %H:%M')} &nbsp;|&nbsp; "
    f"Model: Random Forest (threshold={predictor.threshold:.4f})",
    subtitle_style,
))
elements.append(Spacer(1, 0.15 * inch))
elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e0")))
elements.append(Spacer(1, 0.15 * inch))

# Source description
elements.append(Paragraph("Source Data", section_style))
elements.append(Paragraph(
    "Su L, Cao L, Zhou R, et al. <i>A panel of urine-derived biomarkers to identify "
    "sepsis and distinguish it from systemic inflammatory response syndrome.</i> "
    "Sci Rep. 2021;11:20794. doi:10.1038/s41598-021-99595-0 (PMC8531286)",
    body_style,
))
elements.append(Paragraph(
    "151 simulated patients generated from published summary statistics (Table 3): "
    "53 Sepsis, 48 SIRS, 50 Healthy controls. CRP/Cr values linearly mapped from "
    "&mu;g/mmol to pg/mg scale. IP-10/Cr values simulated from training distributions "
    "(not measured in original study).",
    body_style,
))
elements.append(Spacer(1, 0.1 * inch))

# Summary statistics table
elements.append(Paragraph("Classification Summary", section_style))

y_true = (result.clinical_status == "Septic").astype(int)
y_pred = (result.ml_prediction == "Septic").astype(int)
tp = int(((y_true == 1) & (y_pred == 1)).sum())
tn = int(((y_true == 0) & (y_pred == 0)).sum())
fp = int(((y_true == 0) & (y_pred == 1)).sum())
fn = int(((y_true == 1) & (y_pred == 0)).sum())
sens = tp / (tp + fn)
spec = tn / (tn + fp)
ppv = tp / (tp + fp)
npv = tn / (tn + fn)
acc = (tp + tn) / len(result)

summary_data = [
    [Paragraph("<b>Group</b>", header_style),
     Paragraph("<b>N</b>", header_style),
     Paragraph("<b>Correct</b>", header_style),
     Paragraph("<b>Accuracy</b>", header_style),
     Paragraph("<b>Avg P(sepsis)</b>", header_style),
     Paragraph("<b>Risk: LOW</b>", header_style),
     Paragraph("<b>Risk: MOD</b>", header_style),
     Paragraph("<b>Risk: HIGH</b>", header_style),
     Paragraph("<b>Risk: V.HIGH</b>", header_style)],
]

for grp, label in [("Septic", "Sepsis"), ("SIRS", "SIRS"), ("Healthy", "Healthy")]:
    sub = result[result.clinical_status == grp]
    expected = "Septic" if grp == "Septic" else "Not Septic"
    correct = int((sub.ml_prediction == expected).sum())
    n = len(sub)
    avg_p = sub.ml_probability.mean()
    risk_counts = sub.ml_risk_level.value_counts()
    summary_data.append([
        Paragraph(f"<b>{label}</b>", cell_style),
        Paragraph(str(n), cell_center),
        Paragraph(f"{correct}/{n}", cell_center),
        Paragraph(f"{correct/n*100:.1f}%", cell_center),
        Paragraph(f"{avg_p:.3f}", cell_center),
        Paragraph(str(risk_counts.get("LOW", 0)), cell_center),
        Paragraph(str(risk_counts.get("MODERATE", 0)), cell_center),
        Paragraph(str(risk_counts.get("HIGH", 0)), cell_center),
        Paragraph(str(risk_counts.get("VERY HIGH", 0)), cell_center),
    ])

# Overall row
summary_data.append([
    Paragraph("<b>Overall</b>", cell_style),
    Paragraph(str(len(result)), cell_center),
    Paragraph(f"{tp+tn}/{len(result)}", cell_center),
    Paragraph(f"{acc*100:.1f}%", cell_center),
    Paragraph("—", cell_center),
    Paragraph("—", cell_center),
    Paragraph("—", cell_center),
    Paragraph("—", cell_center),
    Paragraph("—", cell_center),
])

col_widths = [0.8*inch, 0.5*inch, 0.65*inch, 0.7*inch, 0.85*inch,
              0.7*inch, 0.7*inch, 0.7*inch, 0.75*inch]
summary_table = Table(summary_data, colWidths=col_widths)
summary_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#edf2f7")),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
elements.append(summary_table)
elements.append(Spacer(1, 0.1 * inch))

# Metrics row
metrics_text = (
    f"<b>Sensitivity:</b> {sens:.3f} &nbsp;&nbsp; "
    f"<b>Specificity:</b> {spec:.3f} &nbsp;&nbsp; "
    f"<b>PPV:</b> {ppv:.3f} &nbsp;&nbsp; "
    f"<b>NPV:</b> {npv:.3f} &nbsp;&nbsp; "
    f"<b>TP:</b> {tp} &nbsp; <b>TN:</b> {tn} &nbsp; "
    f"<b>FP:</b> {fp} &nbsp; <b>FN:</b> {fn}"
)
elements.append(Paragraph(metrics_text, body_style))

# ---------------------------------------------------------------------------
# Color-coding helpers
# ---------------------------------------------------------------------------
RISK_COLORS = {
    "LOW": colors.HexColor("#c6f6d5"),
    "MODERATE": colors.HexColor("#fefcbf"),
    "HIGH": colors.HexColor("#fed7aa"),
    "VERY HIGH": colors.HexColor("#fed7d7"),
}

PRED_COLORS = {
    "Septic": colors.HexColor("#fc8181"),
    "Not Septic": colors.HexColor("#9ae6b4"),
}

GROUP_LABELS = {
    "Septic": ("SEPSIS", colors.HexColor("#c53030")),
    "SIRS": ("SIRS", colors.HexColor("#d69e2e")),
    "Healthy": ("HEALTHY", colors.HexColor("#38a169")),
}


def build_patient_table(group_df, group_name):
    """Build a formatted patient table for one clinical group."""
    header = [
        Paragraph("<b>#</b>", header_style),
        Paragraph("<b>Patient ID</b>", header_style),
        Paragraph("<b>Age</b>", header_style),
        Paragraph("<b>SOFA</b>", header_style),
        Paragraph("<b>CRP/Cr<br/>(pg/mg)</b>", header_style),
        Paragraph("<b>IP-10/Cr<br/>(pg/mg)</b>", header_style),
        Paragraph("<b>ML Prediction</b>", header_style),
        Paragraph("<b>P(Sepsis)</b>", header_style),
        Paragraph("<b>Risk Level</b>", header_style),
        Paragraph("<b>SepsisDx</b>", header_style),
        Paragraph("<b>Agree?</b>", header_style),
    ]

    rows = [header]
    sub = group_df.sort_values("ml_probability", ascending=False).reset_index(drop=True)

    for i, (_, r) in enumerate(sub.iterrows()):
        correct_label = "Septic" if group_name == "Septic" else "Not Septic"
        is_correct = r["ml_prediction"] == correct_label

        pred_text = f'<font color="{"#c53030" if r["ml_prediction"]=="Septic" else "#276749"}">'
        pred_text += f'<b>{r["ml_prediction"]}</b></font>'
        if not is_correct:
            pred_text += ' <font color="#c53030">✗</font>'

        agree_text = "✓" if r["models_agree"] else "✗"
        agree_color = "#276749" if r["models_agree"] else "#c53030"

        rows.append([
            Paragraph(str(i + 1), cell_center),
            Paragraph(str(r["sample_id"]), cell_style),
            Paragraph(str(int(r["age"])) if pd.notna(r.get("age")) else "—", cell_center),
            Paragraph(str(int(r["sofa_score"])) if pd.notna(r.get("sofa_score")) else "—", cell_center),
            Paragraph(f"{r['crp_cr_pg_mg']:.1f}", cell_right),
            Paragraph(f"{r['ip10_cr_pg_mg']:.1f}", cell_right),
            Paragraph(pred_text, cell_center),
            Paragraph(f"{r['ml_probability']:.4f}", cell_center),
            Paragraph(f"<b>{r['ml_risk_level']}</b>", cell_center),
            Paragraph(str(r["sepsisdx_prediction"]), cell_center),
            Paragraph(f'<font color="{agree_color}"><b>{agree_text}</b></font>', cell_center),
        ])

    col_w = [0.35*inch, 0.85*inch, 0.4*inch, 0.45*inch, 0.75*inch, 0.75*inch,
             0.95*inch, 0.7*inch, 0.75*inch, 0.8*inch, 0.5*inch]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]

    # Color-code risk and prediction cells
    for row_idx in range(1, len(rows)):
        r = sub.iloc[row_idx - 1]
        risk = r["ml_risk_level"]
        if risk in RISK_COLORS:
            style_cmds.append(("BACKGROUND", (8, row_idx), (8, row_idx), RISK_COLORS[risk]))
        pred = r["ml_prediction"]
        if pred in PRED_COLORS:
            style_cmds.append(("BACKGROUND", (6, row_idx), (6, row_idx), PRED_COLORS[pred]))

        # Highlight misclassifications
        correct_label = "Septic" if group_name == "Septic" else "Not Septic"
        if pred != correct_label:
            style_cmds.append(("BACKGROUND", (0, row_idx), (0, row_idx), colors.HexColor("#fff5f5")))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


# ---------------------------------------------------------------------------
# Patient listing pages
# ---------------------------------------------------------------------------
for grp in ["Septic", "SIRS", "Healthy"]:
    elements.append(PageBreak())
    label, label_color = GROUP_LABELS[grp]
    sub = result[result.clinical_status == grp]
    n = len(sub)
    expected = "Septic" if grp == "Septic" else "Not Septic"
    correct = int((sub.ml_prediction == expected).sum())

    elements.append(Paragraph(
        f'<font color="{label_color.hexval()}">{label}</font> Group — '
        f'{correct}/{n} Correctly Classified ({correct/n*100:.1f}%)',
        section_style,
    ))

    if grp == "Septic":
        elements.append(Paragraph(
            "Expected classification: <b>Septic</b>. Patients sorted by descending P(sepsis).",
            note_style,
        ))
    elif grp == "SIRS":
        elements.append(Paragraph(
            "Expected classification: <b>Not Septic</b>. SIRS patients with elevated CRP/Cr "
            "are the most challenging group — overlapping inflammatory profiles with sepsis. "
            "Sorted by descending P(sepsis).",
            note_style,
        ))
    else:
        elements.append(Paragraph(
            "Expected classification: <b>Not Septic</b>. All healthy controls correctly "
            "identified with very low sepsis probability.",
            note_style,
        ))

    tbl = build_patient_table(sub, grp)
    elements.append(tbl)

# ---------------------------------------------------------------------------
# Footer / disclaimers
# ---------------------------------------------------------------------------
elements.append(Spacer(1, 0.3 * inch))
elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e0")))
elements.append(Paragraph(
    "<b>Disclaimer:</b> This report is generated from simulated patient data derived from "
    "published summary statistics. It is intended for research and algorithm validation "
    "purposes only — not for clinical decision-making. The IP-10/Cr values were simulated "
    "(not measured in the original study). CRP/Cr values were linearly rescaled from the "
    "original &mu;g/mmol units to match the algorithm's pg/mg input range.",
    note_style,
))
elements.append(Paragraph(
    "SepsisDx Classifier v1.0 &nbsp;|&nbsp; Random Forest model &nbsp;|&nbsp; "
    f"Report generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    note_style,
))

# ---------------------------------------------------------------------------
# Build PDF
# ---------------------------------------------------------------------------
doc.build(elements)
print(f"PDF report saved: {OUTPUT}")
