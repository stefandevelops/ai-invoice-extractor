from __future__ import annotations

import pandas as pd
import streamlit as st

from extractor.export import review_table_records, to_csv, to_xlsx
from extractor.money import fmt_money
from extractor.pipeline import has_llm_credentials, load_bundled_samples, run_pipeline

st.set_page_config(
    page_title="Document Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    .block-container { padding-top: 1.6rem; max-width: 1200px; }
    h1 { font-weight: 650; letter-spacing: -0.02em; }
    .eyebrow {
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #5C656A;
        margin-bottom: 0.2rem;
    }
    .pitch { font-size: 1.05rem; color: #3A4449; margin-bottom: 0.8rem; }
    .mode-pill {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: #D7E3E6;
        color: #1F4E5F;
    }
    .mode-pill.llm { background: #1F4E5F; color: #F7F5F0; }
    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #E0D9CC;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
    }
    .flag-card {
        background: #FDECEC;
        border-left: 4px solid #B42318;
        padding: 0.75rem 0.9rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    .warn-card {
        background: #FFF4D6;
        border-left: 4px solid #B54708;
        padding: 0.75rem 0.9rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    .ok-card {
        background: #EEF6F0;
        border-left: 4px solid #027A48;
        padding: 0.75rem 0.9rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
</style>
"""


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    llm_ready = has_llm_credentials()
    mode_label = "LLM mode" if llm_ready else "Demo mode"
    mode_class = "mode-pill llm" if llm_ready else "mode-pill"

    st.markdown('<div class="eyebrow">AP document review</div>', unsafe_allow_html=True)
    st.title("Document Extractor")
    st.markdown(
        '<p class="pitch">Turns invoices and delivery notes into a reviewable table, '
        "then flags the rows that do not add up.</p>",
        unsafe_allow_html=True,
    )
    if llm_ready:
        hint = "An API key is set, so uploaded PDFs go through an LLM. Bundled samples still work the same way."
    else:
        hint = "No API key — bundled samples use a deterministic parser. Set OPENAI_API_KEY or GEMINI_API_KEY to extract arbitrary PDFs."
    st.markdown(f'<span class="{mode_class}">{mode_label}</span>  {hint}', unsafe_allow_html=True)

    source = st.radio(
        "Documents",
        ("Bundled sample pack (8 fictional PDFs)", "Upload your own PDFs"),
        horizontal=True,
    )

    uploaded = []
    if source.startswith("Upload"):
        uploaded = st.file_uploader(
            "PDF invoices or delivery notes",
            type=["pdf"],
            accept_multiple_files=True,
        )
        if not llm_ready:
            st.info(
                "Without an API key the app will still try a simple label parser. "
                "For a reliable demo, run the bundled sample pack."
            )

    extract = st.button("Extract and validate", type="primary", use_container_width=False)

    if extract:
        files = _collect_files(source, uploaded)
        if not files:
            st.warning("Add at least one PDF, or switch back to the bundled sample pack.")
        else:
            with st.spinner("Reading documents…"):
                st.session_state["reviewed"] = run_pipeline(files)

    reviewed = st.session_state.get("reviewed")
    if not reviewed:
        st.caption("Tip: start with the sample pack. Three documents are clean; the others are built to fail a check.")
        return

    _render_results(reviewed)


def _collect_files(source: str, uploaded) -> list[tuple[str, bytes]]:
    if source.startswith("Bundled"):
        return load_bundled_samples()
    files = []
    for item in uploaded or []:
        files.append((item.name, item.getvalue()))
    return files


def _render_results(reviewed) -> None:
    flagged = [row for row in reviewed if row.status_label == "Flagged"]
    warnings = [row for row in reviewed if row.status_label == "Warning"]
    clean = [row for row in reviewed if row.status_label == "Clean"]

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Documents", len(reviewed))
    col_b.metric("Clean", len(clean))
    col_c.metric("Flagged", len(flagged))
    col_d.metric("Warnings", len(warnings))

    st.subheader("Review table")
    frame = pd.DataFrame(review_table_records(reviewed))

    def _style_status(column: pd.Series):
        styles = []
        for value in column:
            if value == "Flagged":
                styles.append("background-color: #FDECEC; color: #7A271A; font-weight: 600")
            elif value == "Warning":
                styles.append("background-color: #FFF4D6; color: #7A2E0E; font-weight: 600")
            else:
                styles.append("background-color: #EEF6F0; color: #054F31; font-weight: 600")
        return styles

    styler = frame.style.apply(_style_status, subset=["Status"]).apply(_row_tint, axis=1)
    st.dataframe(styler, use_container_width=True, hide_index=True, height=360)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Why rows were flagged")
        notable = [row for row in reviewed if row.issues]
        if not notable:
            st.success("Every document in this batch passed the checks.")
        for row in notable:
            css = "flag-card" if row.status_label == "Flagged" else "warn-card"
            reasons = "".join(f"<div>• {issue.message}</div>" for issue in row.issues)
            st.markdown(
                f'<div class="{css}"><strong>{row.document.document_number}</strong> '
                f"— {row.document.supplier}<br/>{reasons}</div>",
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Export")
        st.download_button(
            "Download CSV",
            data=to_csv(reviewed),
            file_name="extracted_documents.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download Excel",
            data=to_xlsx(reviewed),
            file_name="extracted_documents.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption("Excel has two sheets: document headers and line items. Flagged rows are highlighted.")

    st.subheader("Line items")
    selected = st.selectbox(
        "Open a document",
        options=list(range(len(reviewed))),
        format_func=lambda i: f"{reviewed[i].document.document_number} · {reviewed[i].document.supplier} · {reviewed[i].status_label}",
    )
    chosen = reviewed[selected]
    doc = chosen.document
    meta_cols = st.columns(4)
    meta_cols[0].write(f"**PO:** {doc.po_number or '—'}")
    meta_cols[1].write(f"**Subtotal:** {fmt_money(doc.subtotal, doc.currency)}")
    meta_cols[2].write(f"**VAT:** {fmt_money(doc.vat_amount, doc.currency)}")
    meta_cols[3].write(f"**Total:** {fmt_money(doc.total, doc.currency)}")
    if doc.line_items:
        st.table(
            [
                {
                    "Description": item.description,
                    "Qty": f"{item.quantity:g}",
                    "Unit price": fmt_money(item.unit_price),
                    "VAT": f"{(item.vat_rate * 100):.0f}%",
                    "Amount": fmt_money(item.line_total),
                }
                for item in doc.line_items
            ]
        )
    else:
        st.caption("No line items were extracted from this file.")


def _row_tint(row: pd.Series):
    if row["Status"] == "Flagged":
        color = "background-color: #FDF2F0"
    elif row["Status"] == "Warning":
        color = "background-color: #FFF8E8"
    else:
        color = "background-color: #F6FAF7"
    return [color] * len(row)


if __name__ == "__main__":
    main()
