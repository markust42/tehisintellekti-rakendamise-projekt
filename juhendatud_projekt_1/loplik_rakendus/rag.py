import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def do_rag(query: str, filtered_df: pd.DataFrame, embedder, n: int = 3):
    """Semantic search. Returns (context_text, course_names, results_display_df)."""
    if filtered_df.empty:
        return None, [], pd.DataFrame()

    query_vec = embedder.encode([query])[0]
    emb_matrix = np.stack(filtered_df["embedding"].values)
    scored = filtered_df.copy()
    scored["score"] = cosine_similarity([query_vec], emb_matrix)[0]
    results = scored.sort_values("score", ascending=False).head(n)
    results_display = results.drop(columns=["embedding"], errors="ignore").copy()
    results = results.drop(columns=["score", "embedding", "unique_ID"], errors="ignore")

    lines, course_names = [], []
    for i, (_, row) in enumerate(results.iterrows(), 1):
        def get(field, default="?"):
            return row.get(field, default)

        def truncate(field, limit):
            val = get(field, "")
            return str(val)[:limit] if pd.notna(val) else ""

        name = get("nimi_et", get("nimi_en"))
        lines.append(
            f"{i}. {name} ({get('nimi_en', '')})\n"
            f"   Kood: {get('aine_kood')}\n"
            f"   EAP: {get('eap')} | Semester: {get('semester')} | "
            f"Keel: {get('keel')} | Õppeviis: {get('veebiope')}\n"
            f"   Õppeaste: {get('oppeaste')} | Linn: {get('linn')}\n"
            f"   Kirjeldus: {truncate('kirjeldus', 500)}\n"
            f"   Eesmärgid: {truncate('eesmargid', 300)}\n"
            f"   Õpiväljundid: {truncate('opivaljundid', 300)}"
        )
        course_names.append(name)

    return "\n\n".join(lines), course_names, results_display
