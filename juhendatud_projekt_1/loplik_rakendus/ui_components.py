import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import ASSISTANT_AVATAR, EAP_DEFAULT, FILTER_NONE, USER_AVATAR
from feedback import log_feedback
from filters import get_active_filters, get_pending_filters_tuple
from query_handlers import handle_first_query


def apply_custom_css():
    css_path = Path(__file__).parent / "styles.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_debug_expander(debug: dict, idx: int):
    with st.expander("🔍 Vaata kapoti alla (RAG ja filtrid)"):
        st.caption(f"**Aktiivsed filtrid:** {debug.get('filters', 'Info puudub')}")
        st.write(f"Filtrid jätsid andmestikku alles **{debug.get('filtered_count', 0)}** kursust.")

        st.write("**RAG otsingu tulemus (Top leitud kursust):**")
        ctx_df = debug.get("context_df")
        if ctx_df is not None and not ctx_df.empty:
            display_cols = ["unique_ID", "nimi_et", "eap", "semester", "oppeaste", "score"]
            cols_to_show = [c for c in display_cols if c in ctx_df.columns]
            st.dataframe(ctx_df[cols_to_show], hide_index=True)
        else:
            st.warning("Ühtegi kursust ei leitud (kas filtrid olid liiga karmid või andmestik tühi).")

        st.text_area(
            "LLM-ile saadetud täpne prompt:",
            debug.get("system_prompt", ""),
            height=150,
            disabled=True,
            key=f"prompt_area_{idx}",
        )


def render_feedback_form(debug: dict, message_content: str, idx: int):
    with st.expander("📝 Hinda vastust (Salvestab logisse)"):
        with st.form(key=f"feedback_form_{idx}"):
            rating = st.radio(
                "Hinnang vastusele:", ["👍 Hea", "👎 Halb"],
                horizontal=True, key=f"rating_{idx}",
            )
            kato = st.selectbox(
                "Kui vastus oli halb, siis mis läks valesti?",
                ["", "Filtrid olid liiga karmid/valed",
                 "Otsing leidis valed ained (RAG viga)",
                 "LLM hallutsineeris/vastas valesti"],
                key=f"kato_{idx}",
            )
            if st.form_submit_button("Salvesta hinnang"):
                ctx_df = debug.get("context_df")
                ctx_ids = ctx_df["unique_ID"].tolist() if (ctx_df is not None and not ctx_df.empty) else []
                ctx_names = (
                    ctx_df["nimi_et"].tolist()
                    if (ctx_df is not None and not ctx_df.empty and "nimi_et" in ctx_df.columns)
                    else []
                )
                log_feedback(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    debug.get("user_prompt", ""),
                    debug.get("filters", ""),
                    ctx_ids, ctx_names,
                    message_content, rating, kato,
                )
                st.success("Tagasiside salvestatud tagasiside_log.csv faili!")


def render_chat_history():
    for i, message in enumerate(st.session_state.messages):
        avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            if message["role"] == "assistant" and "filter_msg" in message:
                st.caption(message["filter_msg"])
            st.markdown(message["content"])
            if message["role"] == "assistant" and "usage" in message and message["usage"]:
                usage = message["usage"]
                st.markdown(
                    (
                        '<p class="usage-caption">'
                        f"LLM kasutus · sisend: {usage.get('prompt', 0):,} · "
                        f"väljund: {usage.get('completion', 0):,} · "
                        f"kokku: {usage.get('total', 0):,}"
                        "</p>"
                    ),
                    unsafe_allow_html=True,
                )
            if message["role"] == "assistant" and "debug_info" in message:
                render_debug_expander(message["debug_info"], i)
                render_feedback_form(message["debug_info"], message["content"], i)


def render_top_panel(test_cases_df):
    max_tests = len(test_cases_df) if test_cases_df is not None and not test_cases_df.empty else 0

    c_title, c_key, c_n, c_run, c_clr = st.columns([1.4, 2.8, 0.55, 0.85, 0.85])

    with c_title:
        st.markdown('<p class="header-title">AI Kursuste Nõustaja</p>', unsafe_allow_html=True)

    with c_key:
        api_key = st.text_input(
            "api",
            value=st.session_state.api_key_input,
            type="password",
            placeholder="OpenRouter API võti…",
            key="api_key_top_input",
            label_visibility="collapsed",
        )
        st.session_state.api_key_input = api_key

    with c_n:
        if max_tests > 0:
            test_count = st.number_input(
                "n", min_value=1, max_value=max_tests,
                value=min(5, max_tests), step=1,
                label_visibility="collapsed",
            )
        else:
            st.number_input("n", value=0, disabled=True, label_visibility="collapsed")
            test_count = 0

    with c_run:
        run_tests = st.button(
            "▶ Testid",
            disabled=(max_tests == 0 or not api_key),
            use_container_width=True,
        )

    with c_clr:
        clear_chat = st.button("✕ Tühjenda", use_container_width=True)

    if clear_chat:
        for key in [
            "messages", "total_tokens", "rag_context",
            "course_names", "results_display", "filter_counts",
            "last_test_results", "last_test_summary",
            "pending_query", "awaiting_filter_decision",
            "collecting_filter_values", "pending_filter_values",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    return api_key, test_count, run_tests


def render_chat_filter_gate(api_key, client, embedder, df, embeddings_df):
    pending_query = st.session_state.get("pending_query")
    if not pending_query:
        return

    with st.container(border=True):
        st.markdown('<p class="panel-section">Otsingu täpsustamine</p>', unsafe_allow_html=True)
        st.markdown(f"**Päring:** {pending_query}")

        if st.session_state.get("awaiting_filter_decision", False):
            st.markdown("Kas soovid enne otsingut rakendada filtreid?")
            col1, col2 = st.columns(2)
            if col1.button("Jah, vali filtrid", key="chat_filter_yes", use_container_width=True):
                st.session_state.awaiting_filter_decision = False
                st.session_state.collecting_filter_values = True
                st.rerun()
            if col2.button("Ei, otsi kohe", key="chat_filter_no", use_container_width=True):
                if not api_key:
                    error_msg = "Palun sisesta OpenRouter API võti üleval paneelis!"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.pending_query = None
                    st.session_state.awaiting_filter_decision = False
                    st.session_state.collecting_filter_values = False
                else:
                    st.session_state.awaiting_filter_decision = False
                    st.session_state.collecting_filter_values = False
                    query_to_run = st.session_state.pending_query
                    st.session_state.pending_query = None
                    handle_first_query(query_to_run, client, embedder, df, embeddings_df, (
                        FILTER_NONE, FILTER_NONE, FILTER_NONE,
                        FILTER_NONE, FILTER_NONE, EAP_DEFAULT,
                    ))

        elif st.session_state.get("collecting_filter_values", False):
            st.markdown("Vali soovi korral filtrid ja käivita otsing:")
            with st.form("chat_filter_form"):
                sem = st.selectbox(
                    "Semester",
                    [FILTER_NONE, "kevad", "sügis"],
                    index=[FILTER_NONE, "kevad", "sügis"].index(
                        st.session_state.pending_filter_values["semester"]
                    ),
                )
                keel = st.selectbox(
                    "Keel",
                    [FILTER_NONE, "eesti keel", "inglise keel"],
                    index=[FILTER_NONE, "eesti keel", "inglise keel"].index(
                        st.session_state.pending_filter_values["keel"]
                    ),
                )
                oppe = st.selectbox(
                    "Õppeaste",
                    [
                        FILTER_NONE, "bakalaureuseõpe", "magistriõpe", "doktoriõpe",
                        "integreeritud bakalaureuse- ja magistriõpe", "rakenduskõrgharidusõpe",
                    ],
                    index=[
                        FILTER_NONE, "bakalaureuseõpe", "magistriõpe", "doktoriõpe",
                        "integreeritud bakalaureuse- ja magistriõpe", "rakenduskõrgharidusõpe",
                    ].index(st.session_state.pending_filter_values["oppeaste"]),
                )
                veeb = st.selectbox(
                    "Õppeviis",
                    [FILTER_NONE, "põimõpe", "lähiõpe", "veebiõpe"],
                    index=[FILTER_NONE, "põimõpe", "lähiõpe", "veebiõpe"].index(
                        st.session_state.pending_filter_values["veebiope"]
                    ),
                )
                linn = st.selectbox(
                    "Linn",
                    [FILTER_NONE, "Tartu linn", "Narva linn", "Viljandi linn", "Pärnu linn"],
                    index=[FILTER_NONE, "Tartu linn", "Narva linn", "Viljandi linn", "Pärnu linn"].index(
                        st.session_state.pending_filter_values["linn"]
                    ),
                )
                eap = st.slider(
                    "EAP vahemik",
                    min_value=1,
                    max_value=36,
                    value=tuple(st.session_state.pending_filter_values["eap"]),
                )

                submit_apply = st.form_submit_button("Rakenda filtrid ja otsi")

            if st.button("Jäta filtrid vahele", key="chat_filter_skip", use_container_width=True):
                st.session_state.pending_filter_values = {
                    "semester": FILTER_NONE,
                    "keel": FILTER_NONE,
                    "oppeaste": FILTER_NONE,
                    "veebiope": FILTER_NONE,
                    "linn": FILTER_NONE,
                    "eap": EAP_DEFAULT,
                }
                submit_apply = True

            if submit_apply:
                if not api_key:
                    error_msg = "Palun sisesta OpenRouter API võti üleval paneelis!"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.pending_query = None
                    st.session_state.collecting_filter_values = False
                else:
                    st.session_state.pending_filter_values = {
                        "semester": sem,
                        "keel": keel,
                        "oppeaste": oppe,
                        "veebiope": veeb,
                        "linn": linn,
                        "eap": tuple(eap),
                    }
                    filters = get_pending_filters_tuple()
                    query_to_run = st.session_state.pending_query
                    st.session_state.pending_query = None
                    st.session_state.collecting_filter_values = False
                    handle_first_query(query_to_run, client, embedder, df, embeddings_df, filters)
