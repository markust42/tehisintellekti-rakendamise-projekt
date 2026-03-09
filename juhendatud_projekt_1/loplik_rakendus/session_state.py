import os

import pandas as pd
import streamlit as st

from config import EAP_DEFAULT, FILTER_NONE


def init_session_state():
    defaults = {
        "messages": [],
        "total_tokens": {"prompt": 0, "completion": 0},
        "rag_context": None,
        "course_names": [],
        "results_display": pd.DataFrame(),
        "last_test_results": pd.DataFrame(),
        "last_test_summary": {"total": 0, "passed": 0, "failed": 0},
        "pending_query": None,
        "awaiting_filter_decision": False,
        "collecting_filter_values": False,
        "pending_filter_values": {
            "semester": FILTER_NONE,
            "keel": FILTER_NONE,
            "oppeaste": FILTER_NONE,
            "veebiope": FILTER_NONE,
            "linn": FILTER_NONE,
            "eap": EAP_DEFAULT,
        },
        "api_key_input": os.getenv("OPENROUTER_API_KEY", ""),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def update_tokens(usage):
    if usage:
        st.session_state.total_tokens["prompt"] += usage.prompt_tokens or 0
        st.session_state.total_tokens["completion"] += usage.completion_tokens or 0


def usage_to_dict(usage):
    if not usage:
        return None
    prompt_tokens = usage.prompt_tokens or 0
    completion_tokens = usage.completion_tokens or 0
    total_tokens = getattr(usage, "total_tokens", None)
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens
    return {
        "prompt": int(prompt_tokens),
        "completion": int(completion_tokens),
        "total": int(total_tokens),
    }
