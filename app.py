from __future__ import annotations

import html

import streamlit as st

from extractor.export import review_table_html, to_csv, to_xlsx
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
    .flag-card, .warn-card, .ok-card {
        padding: 0.75rem 0.9rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    .flag-card { background: #FDECEC; border-left: 4px solid #B42318; }
    .warn-card { background: #FFF4D6; border-left: 4px solid #B54708; }
    .ok-card { background: #EEF6F0; border-left: 4px solid #027A48; }
    table.review {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        background: #fff;
        border: 1px solid #E0D9CC;
        border-radius: 8px;
        overflow: hidden;
    }
    table.review th {
        text-align: left;
        background: #1F4E5F;
        color: #F7F5F0;
        padding: 0.55rem 0.65rem;
        font-weight: 600;
    }
    table.review td {
        padding: 0.55rem 0.65rem;
        vertical-align: top;
        border-top: 1px solid #E8E2D6;
    }
    table.review tr.row-flag { background: #FDECEC; }
    table.review tr.row-warn { background: #FFF4D6; }
    table.review tr.row-ok { background: #F6FAF7; }
    .badge {
        display: inline-block;
        padding: 0.1rem 0.5rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-flag { background: #F8D7D3; color: #7A271A; }
    .badge-warn { background: #F8E3B8; color: #7A2E0E; }
    .badge-ok { background: #C8E6D4; color: #054F31; }
    table.lines { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
    table.lines th, table.lines td { padding: 0.4rem 0.5rem; border-bottom: 1px solid #E8E2D6; text-align: left; }
    table.lines th { color: #5C656A; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
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
    st.markdown(review_table_html(reviewed), unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Why rows were flagged")
        notable = [row for row in reviewed if row.issues]
        if not notable:
            st.success("Every document in this batch passed the checks.")
        for row in notable:
            css = "flag-card" if row.status_label == "Flagged" else "warn-card"
            reasons = "".join(f"<div>• {html.escape(issue.message)}</div>" for issue in row.issues)
            st.markdown(
                f'<div class="{css}"><strong>{html.escape(row.document.document_number)}</strong> '
                f"— {html.escape(row.document.supplier)}<br/>{reasons}</div>",
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
        format_func=lambda i: (
            f"{reviewed[i].document.document_number} · "
            f"{reviewed[i].document.supplier} · {reviewed[i].status_label}"
        ),
    )
    chosen = reviewed[selected]
    doc = chosen.document
    meta_cols = st.columns(4)
    meta_cols[0].write(f"**PO:** {doc.po_number or '—'}")
    meta_cols[1].write(f"**Subtotal:** {fmt_money(doc.subtotal, doc.currency)}")
    meta_cols[2].write(f"**VAT:** {fmt_money(doc.vat_amount, doc.currency)}")
    meta_cols[3].write(f"**Total:** {fmt_money(doc.total, doc.currency)}")
    if doc.line_items:
        cells = "".join(
            "<tr>"
            f"<td>{html.escape(item.description)}</td>"
            f"<td>{html.escape(_fmt_qty(item.quantity))}</td>"
            f"<td>{html.escape(fmt_money(item.unit_price))}</td>"
            f"<td>{html.escape(f'{(item.vat_rate * 100):.0f}%')}</td>"
            f"<td>{html.escape(fmt_money(item.line_total))}</td>"
            "</tr>"
            for item in doc.line_items
        )
        st.markdown(
            "<table class='lines'><thead><tr>"
            "<th>Description</th><th>Qty</th><th>Unit price</th><th>VAT</th><th>Amount</th>"
            f"</tr></thead><tbody>{cells}</tbody></table>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("No line items were extracted from this file.")


def _fmt_qty(value) -> str:
    text = f"{value.normalize():f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


if __name__ == "__main__":
    main()
