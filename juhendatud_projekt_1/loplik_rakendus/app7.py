import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from config import ASSISTANT_AVATAR, EAP_DEFAULT, FILTER_NONE, USER_AVATAR
from data_loader import get_models
from filters import get_pending_filters_tuple
from query_handlers import handle_followup_query
from session_state import init_session_state
from testing import run_test_cases
from ui_components import (
    apply_custom_css,
    render_chat_filter_gate,
    render_chat_history,
    render_top_panel,
)

load_dotenv()


def main():
    st.set_page_config(
        page_title="AI Kursuste Nõustaja · TÜ",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_custom_css()

    init_session_state()
    embedder, df, embeddings_df, test_cases_df = get_models()
    api_key, test_count, run_tests = render_top_panel(test_cases_df)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key) if api_key else None

    render_chat_filter_gate(api_key, client, embedder, df, embeddings_df)
    render_chat_history()

    prompt = st.chat_input("Kirjelda, mida soovid õppida...")

    if run_tests:
        if not api_key:
            st.error("Palun sisesta OpenRouter API võti ülapaneelis, et teste jooksutada!")
        else:
            run_test_cases(client, embedder, df, embeddings_df, test_cases_df, test_count)

    last_results = st.session_state.get("last_test_results", pd.DataFrame())
    last_summary = st.session_state.get("last_test_summary", {"total": 0, "passed": 0, "failed": 0})
    show_last_test_results = (
        not run_tests
        and isinstance(last_results, pd.DataFrame)
        and not last_results.empty
        and len(st.session_state.get("messages", [])) == 0
    )
    if show_last_test_results:
        st.subheader(f"Viimased testitulemused ({last_summary.get('total', len(last_results))} testi)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Teste kokku", int(last_summary.get("total", len(last_results))))
        c2.metric("Läbitud", int(last_summary.get("passed", 0)))
        c3.metric("Ebaõnnestunud", int(last_summary.get("failed", 0)))
        st.dataframe(last_results, hide_index=True, use_container_width=True)

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        if st.session_state.rag_context is None:
            st.session_state.pending_query = prompt
            st.session_state.awaiting_filter_decision = True
            st.session_state.collecting_filter_values = False
            st.rerun()

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            if not api_key:
                error_msg = "Palun sisesta OpenRouter API võti ülapaneelis!"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                filters = get_pending_filters_tuple()
                handle_followup_query(prompt, client, filters)


if __name__ == "__main__":
    main()
