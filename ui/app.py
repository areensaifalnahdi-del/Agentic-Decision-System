import asyncio
import json
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workflow_runner import MACHINE_DATA, run_allocation  # noqa: E402


st.set_page_config(
    page_title="Intelligent Manufacturing Decision System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def build_pdf_report(
    order: dict[str, Any],
    result: dict[str, Any],
    execution_time: float,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        alignment=TA_LEFT,
    )

    story: list[Any] = [
        Paragraph("Intelligent Manufacturing Decision Report", title_style),
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}",
            body_style,
        ),
        Spacer(1, 8),
        Paragraph("Order Information", heading_style),
    ]

    order_rows = [["Field", "Value"]] + [
        [key.replace("_", " ").title(), str(value)] for key, value in order.items()
    ]
    order_table = Table(order_rows, colWidths=[58 * mm, 105 * mm])
    order_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(order_table)

    story.extend(
        [
            Paragraph("Final Recommendation", heading_style),
            Paragraph(
                f"Selected machine: <b>{result.get('selected_machine', 'none')}</b>",
                body_style,
            ),
            Spacer(1, 5),
            Paragraph(result.get("justification", "No explanation returned."), body_style),
            Paragraph("Required Actions", heading_style),
        ]
    )

    actions = result.get("required_actions", {})
    action_rows = [
        ["Quality", str(actions.get("quality", "none"))],
        ["Maintenance", str(actions.get("maintenance", "none"))],
    ]
    action_table = Table(action_rows, colWidths=[58 * mm, 105 * mm])
    action_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(action_table)

    filtered = result.get("machines_filtered_out", [])
    story.append(Paragraph("Filtered Machines", heading_style))
    if filtered:
        filtered_rows = [["Machine", "Reason"]] + [
            [item.get("machine_id", "-"), item.get("reason", "-")] for item in filtered
        ]
        filtered_table = Table(filtered_rows, colWidths=[35 * mm, 128 * mm])
        filtered_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.7),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(filtered_table)
    else:
        story.append(Paragraph("No machines were filtered out.", body_style))

    story.extend(
        [
            Paragraph("Execution Summary", heading_style),
            Paragraph(f"Execution time: {execution_time:.2f} seconds", body_style),
            Paragraph(f"Machines evaluated: {len(MACHINE_DATA)}", body_style),
        ]
    )

    document.build(story)
    return buffer.getvalue()


def status_for_machine(
    machine_id: str,
    selected_machine: str,
    rejected_ids: set[str],
    warnings: list[str],
) -> tuple[str, str]:
    if machine_id == selected_machine:
        return "Selected", "green"
    if machine_id in rejected_ids:
        return "Rejected", "red"
    if warnings:
        return "Warning", "yellow"
    return "Available", "green"


def inject_css() -> None:
    st.markdown(
        """
        <style>
            html, body, [class*="css"], [data-testid="stAppViewContainer"],
            [data-testid="stSidebar"], button, input, textarea, select,
            label, p, span, div, h1, h2, h3, h4, h5, h6 {
                font-family: "Times New Roman", Times, serif !important;
                color: #000000 !important;
            }

            .stApp {
                background: #F7F7F7 !important;
                color: #000000 !important;
            }

            [data-testid="stHeader"] { background: transparent !important; }
            [data-testid="stSidebar"] {
                background: #FFFFFF !important;
                border-right: 1px solid #000000 !important;
            }

            .block-container {
                max-width: 1500px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            /* Remove the rounded AI look everywhere. */
            *, *::before, *::after {
                border-radius: 0 !important;
                box-shadow: none !important;
            }

            .hero {
                background: #FFFFFF;
                border: 1px solid #000000;
                padding: 28px 30px;
                margin-bottom: 22px;
            }
            .eyebrow {
                font-size: 12px;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 700;
                color: #000000 !important;
                margin-bottom: 10px;
            }
            .hero-title {
                font-size: 38px;
                line-height: 1.08;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: #000000 !important;
                margin: 0;
            }
            .hero-subtitle {
                font-size: 16px;
                line-height: 1.65;
                color: #000000 !important;
                margin-top: 12px;
                max-width: 850px;
            }

            .panel, .metric-card, .machine-card, .explanation, .legend {
                background: #FFFFFF !important;
                border: 1px solid #000000 !important;
                color: #000000 !important;
            }
            .panel { padding: 20px; margin-bottom: 16px; }
            .section-kicker {
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-weight: 700;
                color: #000000 !important;
                margin-bottom: 6px;
            }
            .section-title {
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 5px;
                color: #000000 !important;
            }
            .section-note, .metric-label, .metric-sub, .machine-meta,
            .timeline-time {
                color: #000000 !important;
            }
            .section-note { font-size: 13px; margin-bottom: 14px; }

            .metric-card { padding: 17px 18px; min-height: 108px; }
            .metric-label { font-size: 12px; margin-bottom: 9px; }
            .metric-value { font-size: 25px; font-weight: 700; color: #000000 !important; }
            .metric-sub { font-size: 12px; margin-top: 7px; }

            .machine-card { padding: 17px; min-height: 215px; }
            .machine-name { font-size: 19px; font-weight: 700; color: #000000 !important; }
            .machine-meta { font-size: 13px; line-height: 1.85; }

            .badge {
                display: inline-block;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: 700;
                margin-top: 8px;
                margin-bottom: 10px;
                color: #000000 !important;
                border: 1px solid #000000 !important;
            }
            .badge-green { background: #CDECCF !important; }
            .badge-yellow { background: #F6E7A6 !important; }
            .badge-red { background: #F2B8B5 !important; }

            .timeline { border-left: 1px solid #000000; margin-left: 8px; padding-left: 22px; }
            .timeline-item { position: relative; padding: 0 0 18px 0; }
            .timeline-item:before {
                content: "";
                position: absolute;
                left: -28px;
                top: 4px;
                width: 10px;
                height: 10px;
                background: #000000;
                border: 1px solid #000000;
            }
            .timeline-title { font-size: 14px; font-weight: 700; color: #000000 !important; }
            .timeline-time { font-size: 11px; margin-top: 2px; }
            .check { color: #000000 !important; font-weight: 700; margin-right: 7px; }

            .explanation {
                border-left: 5px solid #000000 !important;
                padding: 18px 20px;
                font-size: 15px;
                line-height: 1.72;
            }

            .legend {
                display: flex;
                flex-wrap: wrap;
                gap: 18px;
                align-items: center;
                padding: 14px 17px;
                font-size: 12px;
                margin-top: 20px;
            }
            .legend-dot {
                width: 10px;
                height: 10px;
                display: inline-block;
                margin-right: 7px;
                border: 1px solid #000000;
            }
            .dot-green { background: #55A868; }
            .dot-yellow { background: #E1C542; }
            .dot-red { background: #C94C4C; }
            .dot-blue { background: #6B8EAD; }

            /* Make every Streamlit form control a sharp rectangle. */
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-baseweb="select"] > div,
            div[data-baseweb="base-input"],
            div[data-baseweb="input"],
            div[data-baseweb="popover"],
            div[data-baseweb="menu"],
            div[data-baseweb="select"],
            textarea {
                background: #FFFFFF !important;
                border: 1px solid #000000 !important;
                color: #000000 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
            }

            /* Remove rounded corners from the number-input +/- controls. */
            [data-testid="stNumberInput"] button,
            [data-testid="stNumberInput"] div,
            [data-testid="stSelectbox"] div,
            [data-testid="stTextInput"] div {
                border-radius: 0 !important;
            }

            div.stButton > button,
            div[data-testid="stFormSubmitButton"] button,
            div[data-testid="stDownloadButton"] button {
                border: 1px solid #000000 !important;
                background: #FFFFFF !important;
                color: #000000 !important;
                font-weight: 700;
                min-height: 44px;
            }
            div.stButton > button:hover,
            div[data-testid="stFormSubmitButton"] button:hover,
            div[data-testid="stDownloadButton"] button:hover {
                background: #EAEAEA !important;
                color: #000000 !important;
                border-color: #000000 !important;
            }

            [data-testid="stProgress"] > div > div > div {
                background-color: #000000 !important;
            }
            [data-testid="stProgress"] > div > div {
                background-color: #D9D9D9 !important;
            }

            /* Tables and expanders */
            [data-testid="stDataFrame"],
            [data-testid="stExpander"],
            details, summary {
                border-radius: 0 !important;
                color: #000000 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("### Platform")
    st.write("Multi-agent order allocation")
    st.write("Rule-based machine selection")
    st.write("Gemini-generated explanation")

inject_css()

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Manufacturing Intelligence Platform</div>
        <div class="hero-title">Intelligent Manufacturing Decision System</div>
        <div class="hero-subtitle">
            A multi-agent platform that evaluates machine availability, capability,
            quality risk, maintenance condition, queue length and deadline feasibility
            before generating a transparent machine-allocation recommendation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

input_col, overview_col = st.columns([0.92, 1.38], gap="large")

with input_col:
    st.markdown(
        """
        <div class="section-kicker">Input</div>
        <div class="section-title">Order Information</div>
        <div class="section-note">Enter the manufacturing requirements used by the agents.</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("order_form"):
        order_id = st.text_input("Order ID", value="ORD-001")
        priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"], index=2)
        required_capability = st.selectbox("Required Capability", ["milling", "turning"])
        deadline_minutes = st.number_input(
            "Deadline in Minutes",
            min_value=1,
            max_value=10000,
            value=120,
            step=5,
        )
        quality_requirement = st.selectbox(
            "Quality Requirement",
            ["standard", "strict"],
            index=1,
        )
        submitted = st.form_submit_button("Run Allocation", use_container_width=True)

with overview_col:
    st.markdown(
        """
        <div class="section-kicker">System Overview</div>
        <div class="section-title">Current Machine Network</div>
        <div class="section-note">Live configuration loaded from the workflow runner.</div>
        """,
        unsafe_allow_html=True,
    )

    cards = st.columns(len(MACHINE_DATA))
    for column, (machine_id, machine) in zip(cards, MACHINE_DATA.items()):
        warnings = machine.get("active_warnings", [])
        if machine.get("status", "").lower() != "available":
            badge_text, badge_class = "Unavailable", "red"
        elif warnings:
            badge_text, badge_class = "Warning", "yellow"
        else:
            badge_text, badge_class = "Available", "green"

        warning_text = ", ".join(warnings) if warnings else "None"
        with column:
            st.markdown(
                f"""
                <div class="machine-card">
                    <div class="machine-name">{machine_id}</div>
                    <span class="badge badge-{badge_class}">{badge_text}</span>
                    <div class="machine-meta">
                        Capability: {machine['capability'].title()}<br>
                        Queue length: {machine['queue_length']}<br>
                        Processing time: {machine['estimated_processing_time_mins']} min<br>
                        Maintenance: {machine['maintenance_condition']:.0%}<br>
                        Warnings: {warning_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

if submitted:
    if not order_id.strip():
        st.error("Enter an Order ID before running the allocation.")
        st.stop()

    order_payload = {
        "order_id": order_id.strip(),
        "priority": priority,
        "required_capability": required_capability,
        "deadline_minutes": int(deadline_minutes),
        "quality_requirement": quality_requirement,
    }

    progress_placeholder = st.empty()
    timeline_steps = [
        "Order received",
        "Order validated",
        "Coordinator started",
        "Machine agents evaluated",
        "Quality assessment completed",
        "Maintenance assessment completed",
        "Decision rules applied",
        "Gemini explanation generated",
        "Final recommendation completed",
    ]

    with progress_placeholder.container():
        st.markdown("### Live Agent Activity")
        progress_bar = st.progress(0)
        status_text = st.empty()
        for index, step in enumerate(timeline_steps[:-1], start=1):
            status_text.markdown(f"<span class='check'>✔</span>{step}", unsafe_allow_html=True)
            progress_bar.progress(index / len(timeline_steps))
            time.sleep(0.11)

    start_time = time.perf_counter()
    try:
        recommendation = asyncio.run(run_allocation(**order_payload))
    except Exception as error:
        progress_placeholder.empty()
        st.error("The allocation workflow failed.")
        st.exception(error)
        st.stop()

    execution_time = time.perf_counter() - start_time
    result = recommendation.model_dump()

    progress_bar.progress(1.0)
    status_text.markdown(
        "<span class='check'>✔</span>Final recommendation completed",
        unsafe_allow_html=True,
    )
    time.sleep(0.2)
    progress_placeholder.empty()

    selected_machine = str(result.get("selected_machine", "none"))
    rejected = result.get("machines_filtered_out", [])
    rejected_ids = {item.get("machine_id", "") for item in rejected}
    suitable_count = max(len(MACHINE_DATA) - len(rejected_ids), 0)

    st.markdown("---")
    st.markdown(
        """
        <div class="section-kicker">Result</div>
        <div class="section-title">Final Recommendation</div>
        <div class="section-note">Decision generated by fixed Python rules and explained by Gemini.</div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)
    metric_values = [
        ("Selected Machine", selected_machine.upper(), "Best-ranked suitable machine"),
        ("Machines Evaluated", str(len(MACHINE_DATA)), "All registered machine agents"),
        ("Suitable Machines", str(suitable_count), "Passed the decision rules"),
        ("Execution Time", f"{execution_time:.2f} s", "End-to-end runtime"),
    ]
    for column, (label, value, note) in zip(metrics, metric_values):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sub">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Decision Explanation")
    st.markdown(
        f"<div class='explanation'>{result.get('justification', 'No explanation returned.')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Machine Decision Cards")
    result_cards = st.columns(len(MACHINE_DATA))
    for column, (machine_id, machine) in zip(result_cards, MACHINE_DATA.items()):
        status_text_value, badge_class = status_for_machine(
            machine_id,
            selected_machine,
            rejected_ids,
            machine.get("active_warnings", []),
        )
        reason = next(
            (item.get("reason", "") for item in rejected if item.get("machine_id") == machine_id),
            "Passed the filtering stage",
        )
        if machine_id == selected_machine:
            reason = "Selected by queue length, quality risk and processing-time ranking"

        with column:
            st.markdown(
                f"""
                <div class="machine-card">
                    <div class="machine-name">{machine_id}</div>
                    <span class="badge badge-{badge_class}">{status_text_value}</span>
                    <div class="machine-meta">
                        Capability: {machine['capability'].title()}<br>
                        Queue: {machine['queue_length']}<br>
                        Processing: {machine['estimated_processing_time_mins']} min<br>
                        Maintenance: {machine['maintenance_condition']:.0%}<br><br>
                        {reason}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    chart_left, chart_right = st.columns(2, gap="large")
    chart_data = pd.DataFrame(
        {
            "Machine": list(MACHINE_DATA.keys()),
            "Queue Length": [m["queue_length"] for m in MACHINE_DATA.values()],
            "Processing Time": [m["estimated_processing_time_mins"] for m in MACHINE_DATA.values()],
            "Maintenance Condition": [m["maintenance_condition"] * 100 for m in MACHINE_DATA.values()],
        }
    ).set_index("Machine")

    with chart_left:
        st.markdown("### Queue and Processing Comparison")
        st.bar_chart(chart_data[["Queue Length", "Processing Time"]], use_container_width=True)

    with chart_right:
        st.markdown("### Maintenance Condition")
        st.bar_chart(chart_data[["Maintenance Condition"]], use_container_width=True)

    timeline_col, actions_col = st.columns([1.2, 0.8], gap="large")

    with timeline_col:
        st.markdown("### Agent Decision Timeline")
        timeline_html = "<div class='timeline'>"
        base_time = datetime.now()
        for index, step in enumerate(timeline_steps):
            stamp = base_time.strftime("%H:%M:%S")
            timeline_html += (
                "<div class='timeline-item'>"
                f"<div class='timeline-title'><span class='check'>✔</span>{step}</div>"
                f"<div class='timeline-time'>{stamp}</div>"
                "</div>"
            )
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

    with actions_col:
        st.markdown("### Required Actions")
        actions = result.get("required_actions", {})
        st.markdown(
            f"""
            <div class="panel">
                <div class="section-kicker">Quality</div>
                <div class="section-title" style="font-size:17px;">{actions.get('quality', 'none')}</div>
            </div>
            <div class="panel">
                <div class="section-kicker">Maintenance</div>
                <div class="section-title" style="font-size:17px;">{actions.get('maintenance', 'none')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Detailed Machine Data")
    detail_rows: list[dict[str, Any]] = []
    for machine_id, machine in MACHINE_DATA.items():
        status_value, _ = status_for_machine(
            machine_id,
            selected_machine,
            rejected_ids,
            machine.get("active_warnings", []),
        )
        detail_rows.append(
            {
                "Machine": machine_id,
                "Decision Status": status_value,
                "Operational Status": machine["status"].title(),
                "Capability": machine["capability"].title(),
                "Queue": machine["queue_length"],
                "Processing Time (min)": machine["estimated_processing_time_mins"],
                "Maintenance": f"{machine['maintenance_condition']:.0%}",
                "Warnings": ", ".join(machine["active_warnings"]) or "None",
            }
        )
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

    with st.expander("View filtered-machine reasons"):
        if rejected:
            st.dataframe(pd.DataFrame(rejected), use_container_width=True, hide_index=True)
        else:
            st.write("No machines were filtered out.")

    with st.expander("View complete JSON result"):
        st.json(result)

    json_bytes = json.dumps(
        {
            "order": order_payload,
            "recommendation": result,
            "execution_time_seconds": execution_time,
            "generated_at": datetime.now().isoformat(),
        },
        indent=2,
    ).encode("utf-8")

    pdf_bytes = build_pdf_report(order_payload, result, execution_time)

    st.markdown("### Export")
    download_left, download_right = st.columns(2)
    with download_left:
        st.download_button(
            "Download JSON",
            data=json_bytes,
            file_name=f"{order_id.strip()}_allocation_result.json",
            mime="application/json",
            use_container_width=True,
        )
    with download_right:
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=f"{order_id.strip()}_allocation_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.markdown(
    """
    <div class="legend">
        <strong>Status legend</strong>
        <span><span class="legend-dot dot-green"></span>Available, passed or selected</span>
        <span><span class="legend-dot dot-yellow"></span>Warning or observation required</span>
        <span><span class="legend-dot dot-red"></span>Rejected, blocked or unavailable</span>
        <span><span class="legend-dot dot-blue"></span>Active workflow stage</span>
    </div>
    """,
    unsafe_allow_html=True,
)