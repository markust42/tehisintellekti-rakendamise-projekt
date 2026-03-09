import pandas as pd
import streamlit as st

from config import EAP_DEFAULT, FILTER_NONE


def get_active_filters(filter_semester, filter_keel, filter_oppeaste,
                       filter_veebiope, filter_linn, filter_eap):
    """Returns (list_of_filter_strings, human-readable summary string)."""
    active = []
    if filter_semester != FILTER_NONE:
        active.append(f"semester: {filter_semester}")
    if filter_keel != FILTER_NONE:
        active.append(f"keel: {filter_keel}")
    if filter_oppeaste != FILTER_NONE:
        active.append(f"õppeaste: {filter_oppeaste}")
    if filter_veebiope != FILTER_NONE:
        active.append(f"õppeviis: {filter_veebiope}")
    if filter_linn != FILTER_NONE:
        active.append(f"linn: {filter_linn}")
    if filter_eap != EAP_DEFAULT:
        active.append(f"EAP: {filter_eap[0]}–{filter_eap[1]}")
    return active, (", ".join(active) if active else "filtrid puuduvad")


def build_filter_mask(merged: pd.DataFrame, filter_semester, filter_keel,
                      filter_oppeaste, filter_veebiope, filter_linn,
                      filter_eap) -> pd.Series:
    """Builds a boolean mask for *merged* based on the active sidebar filters."""
    mask = pd.Series(True, index=merged.index)

    def contains(col, val):
        return merged[col].apply(lambda x: val in str(x) if pd.notna(x) else False)

    if filter_semester != FILTER_NONE:
        mask &= merged["semester"] == filter_semester
    if filter_keel != FILTER_NONE:
        mask &= contains("keel", filter_keel)
    if filter_oppeaste != FILTER_NONE:
        mask &= contains("oppeaste", filter_oppeaste)
    if filter_veebiope != FILTER_NONE:
        mask &= contains("veebiope", filter_veebiope)
    if filter_linn != FILTER_NONE:
        mask &= contains("linn", filter_linn)
    if filter_eap != EAP_DEFAULT:
        mask &= (merged["eap"] >= filter_eap[0]) & (merged["eap"] <= filter_eap[1])
    return mask


def get_pending_filters_tuple() -> tuple:
    filters = st.session_state.pending_filter_values
    return (
        filters.get("semester", FILTER_NONE),
        filters.get("keel", FILTER_NONE),
        filters.get("oppeaste", FILTER_NONE),
        filters.get("veebiope", FILTER_NONE),
        filters.get("linn", FILTER_NONE),
        tuple(filters.get("eap", EAP_DEFAULT)),
    )
