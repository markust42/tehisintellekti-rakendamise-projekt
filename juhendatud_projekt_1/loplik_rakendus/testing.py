import streamlit as st

import pandas as pd

from config import MODEL_NAME
from llm import build_system_prompt
from rag import do_rag


def run_test_cases(client, embedder, df, embeddings_df, test_cases_df, test_count):
    st.subheader(f"Testitulemused ({test_count} testi)")

    test_cases_to_run = test_cases_df.head(test_count)
    results_list = []
    progress_bar = st.progress(0)
    progress_text = st.empty()

    for i, (_, row) in enumerate(test_cases_to_run.iterrows()):
        query = row.iloc[0]
        expected_ids_str = str(row.iloc[1]).strip()

        progress_text.caption(f"Töötlus: test {i + 1}/{test_count} · päring: {query[:60]}")

        expected_ids = set()
        should_be_empty = False

        if expected_ids_str == "-":
            should_be_empty = True
        else:
            expected_ids = {x.strip() for x in expected_ids_str.split(",") if x.strip()}

        merged = pd.merge(df, embeddings_df, on="unique_ID")
        context_text, course_names, results_display = do_rag(query, merged, embedder, n=5)

        rag_found_ids = set()
        if not results_display.empty and "unique_ID" in results_display.columns:
            rag_found_ids = set(results_display["unique_ID"].tolist()[:5])

        system_prompt = build_system_prompt(
            context_text if context_text else "",
            course_names,
            "filtrid puuduvad", len(merged), len(merged)
        )

        messages_to_send = [system_prompt, {"role": "user", "content": query}]

        print(f"Test case {i}: {query}")

        llm_response = ""
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_to_send,
                stream=False
            )
            llm_response = stream.choices[0].message.content
        except Exception as e:
            llm_response = f"VIGA: {e}"

        missing_from_rag = [eid for eid in expected_ids if eid not in rag_found_ids]

        passed = False
        reason = ""

        if should_be_empty:
            if (
                len(rag_found_ids) == 0
                or "ei leidu" in llm_response.lower()
                or "ei leidnud" in llm_response.lower()
                or "pole" in llm_response.lower()
                or not any(x in llm_response for x in df["aine_kood"].tolist())
            ):
                passed = True
                reason = "Vastus tühi vastavalt ootusele (-)"
            else:
                passed = False
                reason = "LLM/RAG tagastas aineid, kuigi ootus oli -"
        else:
            if len(missing_from_rag) > 0:
                passed = False
                reason = f"RAG ei leidnud ID-sid: {', '.join(missing_from_rag)}"
            else:
                missing_ids = [eid for eid in expected_ids if eid not in llm_response]
                if len(missing_ids) == 0:
                    passed = True
                    reason = "RAG ja LLM leidsid kõik oodatud ained"
                else:
                    passed = False
                    reason = f"RAG leidis, aga LLM vastuses puuduvad: {', '.join(missing_ids)}"

        results_list.append({
            "Päring": query,
            "Oodatud ID-d": expected_ids_str,
            "Tulemus": "Pass" if passed else "Fail",
            "Põhjus": reason
        })

        progress_bar.progress((i + 1) / test_count)

    progress_text.caption("Testide käivitamine lõpetatud.")

    results_df = pd.DataFrame(results_list)
    passed_count = int((results_df["Tulemus"] == "Pass").sum()) if not results_df.empty else 0
    failed_count = int((results_df["Tulemus"] == "Fail").sum()) if not results_df.empty else 0

    st.session_state.last_test_results = results_df
    st.session_state.last_test_summary = {
        "total": int(test_count),
        "passed": passed_count,
        "failed": failed_count,
    }

    c1, c2, c3 = st.columns(3)
    c1.metric("Teste kokku", test_count)
    c2.metric("Läbitud", passed_count)
    c3.metric("Ebaõnnestunud", failed_count)

    st.dataframe(results_df, hide_index=True, use_container_width=True)
