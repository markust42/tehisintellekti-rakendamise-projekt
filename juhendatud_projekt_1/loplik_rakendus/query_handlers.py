import pandas as pd
import streamlit as st

from config import EAP_DEFAULT, FILTER_NONE
from filters import build_filter_mask, get_active_filters
from llm import build_system_prompt, call_llm_stream
from rag import do_rag
from session_state import update_tokens, usage_to_dict


def handle_first_query(prompt: str, client, embedder, df, embeddings_df, filters: tuple):
    """Filters data, runs RAG, calls LLM, and persists context for follow-ups."""
    active, active_str = get_active_filters(*filters)

    with st.spinner("Otsin sobivaid kursusi..."):
        merged = pd.merge(df, embeddings_df, on="unique_ID")
        mask = build_filter_mask(merged, *filters)
        filtered_df = merged[mask].copy()
        total_count, filtered_count = len(merged), len(filtered_df)

    filter_msg = (
        f"Rakendatud filtrid jätsid andmestikku **{filtered_count}** kursust {total_count}-st."
        if active
        else f"Otsitakse kõikide andmebaasi **{total_count}** kursuse hulgast."
    )

    if filtered_count == 0:
        msg = "Antud filtritega ei leidu ühtegi kursust. Proovi muuta filtreid külgribal või alusta otsast."
        st.warning(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg, "filter_msg": filter_msg})
        return

    st.caption(filter_msg)
    context_text, course_names, results_display = do_rag(prompt, filtered_df, embedder, n=5)

    if context_text is None:
        msg = "Sobivaid kursuseid ei leitud. Proovi muuta otsingupäringut või filtreid."
        st.warning(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        return

    st.session_state.rag_context = context_text
    st.session_state.course_names = course_names
    st.session_state.results_display = results_display
    st.session_state.filter_counts = (total_count, filtered_count)

    system_prompt = build_system_prompt(context_text, course_names, active_str, total_count, filtered_count)
    messages_to_send = [system_prompt] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    try:
        full_text, usage = call_llm_stream(client, messages_to_send)
        update_tokens(usage)
        usage_dict = usage_to_dict(usage)
        st.session_state.messages.append({
            "role": "assistant",
            "filter_msg": filter_msg,
            "content": full_text,
            "usage": usage_dict,
            "debug_info": {
                "user_prompt": prompt,
                "filters": active_str,
                "filtered_count": filtered_count,
                "context_df": results_display,
                "system_prompt": system_prompt["content"],
            },
        })
        st.rerun()
    except Exception as e:
        st.error(f"Viga: {e}")


def handle_followup_query(prompt: str, client, filters: tuple):
    """Handles follow-up turns by reusing the cached RAG context."""
    _, active_str = get_active_filters(*filters)
    tc, fc = st.session_state.get("filter_counts", (0, 0))
    system_prompt = build_system_prompt(
        st.session_state.rag_context,
        st.session_state.course_names,
        active_str, tc, fc,
    )
    messages_to_send = [system_prompt] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    try:
        full_text, usage = call_llm_stream(client, messages_to_send)
        update_tokens(usage)
        usage_dict = usage_to_dict(usage)
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_text,
            "usage": usage_dict,
            "debug_info": {
                "user_prompt": prompt,
                "filters": active_str,
                "filtered_count": len(st.session_state.results_display),
                "context_df": st.session_state.results_display,
                "system_prompt": system_prompt["content"],
            },
        })
        st.rerun()
    except Exception as e:
        st.error(f"Viga: {e}")
