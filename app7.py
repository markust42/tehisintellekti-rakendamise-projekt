import os
import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

st.title("🎓 AI Kursuse Nõustaja")
st.caption("Semantiline otsing koos metaandmete filtreerimisega.")

# ---------------------------------------------------------------------------
# Külgriba: API võti + filtrid + tokenite kulu
# ---------------------------------------------------------------------------
env_key = os.getenv("OPENROUTER_API_KEY", "")

with st.sidebar:
    api_key = st.text_input("OpenRouter API võti:", value=env_key, type="password")
    st.divider()

    # ---- Filtrid ----
    st.subheader("🔍 Filtrid")
    st.caption("Jäta 'Pole oluline', kui filter ei ole vajalik.")

    filter_semester = st.selectbox(
        "Semester",
        ["Pole oluline", "kevad", "sügis"],
    )
    filter_keel = st.selectbox(
        "Keel",
        ["Pole oluline", "eesti keel", "inglise keel"],
    )
    filter_oppeaste = st.selectbox(
        "Õppeaste",
        [
            "Pole oluline",
            "bakalaureuseõpe",
            "magistriõpe",
            "doktoriõpe",
            "integreeritud bakalaureuse- ja magistriõpe",
            "rakenduskõrgharidusõpe",
        ],
    )
    filter_veebiope = st.selectbox(
        "Õppeviis",
        ["Pole oluline", "põimõpe", "lähiõpe", "veebiõpe"],
    )
    filter_linn = st.selectbox(
        "Linn",
        ["Pole oluline", "Tartu linn", "Narva linn", "Viljandi linn", "Pärnu linn"],
    )
    filter_eap = st.slider("EAP vahemik", min_value=1, max_value=36, value=(1, 36))

    st.divider()

    # ---- Tokenid ja kulu ----
    st.subheader("💰 Tokenid ja kulu")
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = {"prompt": 0, "completion": 0}
    ptok = st.session_state.total_tokens["prompt"]
    ctok = st.session_state.total_tokens["completion"]
    st.metric("Sisend-tokenid", ptok)
    st.metric("Väljund-tokenid", ctok)
    cost = (ptok * 0.10 + ctok * 0.10) / 1_000_000
    st.metric("Ligikaudne kulu (USD)", f"${cost:.6f}")

    st.divider()
    if st.button("🔄 Alusta otsast", use_container_width=True):
        for key in ["messages", "total_tokens", "rag_context", "course_names"]:
            st.session_state.pop(key, None)
        st.rerun()

# ---------------------------------------------------------------------------
# Mudeli ja andmete laadimine (cache)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_models():
    embedder = SentenceTransformer("BAAI/bge-m3")
    df = pd.read_csv("puhtad_andmed.csv")
    embeddings_df = pd.read_pickle("puhtad_andmed_embeddings.pkl")
    return embedder, df, embeddings_df

embedder, df, embeddings_df = get_models()

# ---------------------------------------------------------------------------
# Oleku initsialiseerimine
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_context" not in st.session_state:
    st.session_state.rag_context = None
if "course_names" not in st.session_state:
    st.session_state.course_names = []

# ---------------------------------------------------------------------------
# Abifunktsioonid
# ---------------------------------------------------------------------------

def build_filter_mask(merged: pd.DataFrame) -> pd.Series:
    """Koostab boolean-maski vastavalt külgriba filtritele."""
    mask = pd.Series([True] * len(merged), index=merged.index)
    if filter_semester != "Pole oluline":
        mask &= merged["semester"] == filter_semester
    if filter_keel != "Pole oluline":
        mask &= merged["keel"].apply(
            lambda x: filter_keel in str(x) if pd.notna(x) else False
        )
    if filter_oppeaste != "Pole oluline":
        mask &= merged["oppeaste"].apply(
            lambda x: filter_oppeaste in str(x) if pd.notna(x) else False
        )
    if filter_veebiope != "Pole oluline":
        mask &= merged["veebiope"].apply(
            lambda x: filter_veebiope in str(x) if pd.notna(x) else False
        )
    if filter_linn != "Pole oluline":
        mask &= merged["linn"].apply(
            lambda x: filter_linn in str(x) if pd.notna(x) else False
        )
    if filter_eap != (1, 36):
        mask &= merged["eap"] >= filter_eap[0]
        mask &= merged["eap"] <= filter_eap[1]
    return mask


def do_rag(query: str, filtered_df: pd.DataFrame, n: int = 3):
    """Semantiline otsing. Tagastab konteksti teksti ja kursuste nimed."""
    if filtered_df.empty:
        return None, []
    query_vec = embedder.encode([query])[0]
    emb_matrix = np.stack(filtered_df["embedding"].values)
    scored = filtered_df.copy()
    scored["score"] = cosine_similarity([query_vec], emb_matrix)[0]
    results = scored.sort_values("score", ascending=False).head(n)
    results = results.drop(columns=["score", "embedding", "unique_ID"], errors="ignore")

    lines = []
    course_names = []
    for i, (_, row) in enumerate(results.iterrows(), 1):
        name = row.get("nimi_et", row.get("nimi_en", "?"))
        name_en = row.get("nimi_en", "")
        eap = row.get("eap", "?")
        sem = row.get("semester", "?")
        keel = row.get("keel", "?")
        veebiope = row.get("veebiope", "?")
        oppeaste = row.get("oppeaste", "?")
        linn = row.get("linn", "?")
        kirjeldus = str(row.get("kirjeldus", ""))[:500] if pd.notna(row.get("kirjeldus")) else ""
        eesmargid = str(row.get("eesmargid", ""))[:300] if pd.notna(row.get("eesmargid")) else ""
        opivaljundid = str(row.get("opivaljundid", ""))[:300] if pd.notna(row.get("opivaljundid")) else ""

        lines.append(
            f"{i}. {name} ({name_en})\n"
            f"   EAP: {eap} | Semester: {sem} | Keel: {keel} | Õppeviis: {veebiope}\n"
            f"   Õppeaste: {oppeaste} | Linn: {linn}\n"
            f"   Kirjeldus: {kirjeldus}\n"
            f"   Eesmärgid: {eesmargid}\n"
            f"   Õpiväljundid: {opivaljundid}"
        )
        course_names.append(name)
    return "\n\n".join(lines), course_names


def call_llm_stream(client, messages_to_send):
    """Voogesitab LLM vastuse, tagastab teksti ja kasutusstatistika."""
    stream = client.chat.completions.create(
        model="google/gemma-3-27b-it",
        messages=messages_to_send,
        stream=True,
        stream_options={"include_usage": True},
    )
    placeholder = st.empty()
    full_text = ""
    usage_data = None
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            full_text += chunk.choices[0].delta.content
            placeholder.markdown(full_text)
        if hasattr(chunk, "usage") and chunk.usage:
            usage_data = chunk.usage
    return full_text, usage_data


def update_tokens(usage):
    """Uuendab tokenite loendureid."""
    if usage:
        st.session_state.total_tokens["prompt"] += usage.prompt_tokens or 0
        st.session_state.total_tokens["completion"] += usage.completion_tokens or 0


def build_system_prompt(context_text: str, course_names: list[str], active_filters: str) -> dict:
    """Koostab süsteemi-prompti RAG kontekstiga."""
    allowlist = "\n".join(f"- {name}" for name in course_names)
    return {
        "role": "system",
        "content": (
            f"Oled Tartu Ülikooli kursuste nõustaja. Sinu ülesanne on soovitada kasutajale kursuseid.\n\n"
            f"Rakendatud filtrid: {active_filters}\n\n"
            f"LUBATUD KURSUSED – sa tohid mainida AINULT neid {len(course_names)} kursust:\n"
            f"{allowlist}\n\n"
            f"TÄIELIKUD ANDMED NENDE KURSUSTE KOHTA:\n"
            f"{context_text}\n\n"
            f"REEGLID:\n"
            f"1. Soovita kasutajale maksimaalselt 3 kõige sobivamat kursust ülaltoodud nimekirjast.\n"
            f"2. Kui ükski kursus ei sobi kasutaja päringuga hästi, ütle ausalt, et sobivaid kursuseid ei leidu "
            f"ja soovita muuta filtreid või otsingulauset.\n"
            f"3. Maini AINULT ülalloetletud kursuseid. Ära leiuta ega lisa omalt poolt kursuseid.\n"
            f"4. Kasuta kursuse TÄPSET nime.\n"
            f"5. Esita iga soovitatud kursuse kohta: nimi, EAP, semester, keel, õppeviis ja lühike kirjeldus.\n"
            f"6. Kui kasutaja küsib jätkuküsimusi leitud kursuste kohta, vasta andmete põhjal.\n"
            f"7. Vasta eesti keeles."
        ),
    }


# ---------------------------------------------------------------------------
# Vestluse ajaloo kuvamine
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Kasutaja sisend
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Kirjelda, mida soovid õppida..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not api_key:
            error_msg = "Palun sisesta OpenRouter API võti külgribas!"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

            # Kas see on esimene päring või jätkuvestlus?
            is_first_query = st.session_state.rag_context is None

            if is_first_query:
                # ---- Esimene päring: filtreerimine + RAG ----
                with st.spinner("Otsin sobivaid kursusi..."):
                    merged = pd.merge(df, embeddings_df, on="unique_ID")
                    mask = build_filter_mask(merged)
                    filtered_df = merged[mask].copy()

                    total_count = len(merged)
                    filtered_count = len(filtered_df)

                    # Aktiivsed filtrid teksti kujul
                    active = []
                    if filter_semester != "Pole oluline":
                        active.append(f"semester: {filter_semester}")
                    if filter_keel != "Pole oluline":
                        active.append(f"keel: {filter_keel}")
                    if filter_oppeaste != "Pole oluline":
                        active.append(f"õppeaste: {filter_oppeaste}")
                    if filter_veebiope != "Pole oluline":
                        active.append(f"õppeviis: {filter_veebiope}")
                    if filter_linn != "Pole oluline":
                        active.append(f"linn: {filter_linn}")
                    if filter_eap != (1, 36):
                        active.append(f"EAP: {filter_eap[0]}–{filter_eap[1]}")
                    active_str = ", ".join(active) if active else "filtrid puuduvad"

                    st.caption(f"Filtritele vastas **{filtered_count}** kursust {total_count}-st.")

                if filtered_count == 0:
                    no_result = (
                        "Antud filtritega ei leidu ühtegi kursust. "
                        "Proovi muuta filtreid külgribal või alusta otsast."
                    )
                    st.warning(no_result)
                    st.session_state.messages.append({"role": "assistant", "content": no_result})
                else:
                    context_text, course_names = do_rag(prompt, filtered_df, n=3)

                    if context_text is None:
                        no_result = "Sobivaid kursuseid ei leitud. Proovi muuta otsingupäringut või filtreid."
                        st.warning(no_result)
                        st.session_state.messages.append({"role": "assistant", "content": no_result})
                    else:
                        # Salvesta RAG kontekst jätkuvestluse jaoks
                        st.session_state.rag_context = context_text
                        st.session_state.course_names = course_names

                        system_prompt = build_system_prompt(context_text, course_names, active_str)
                        messages_to_send = [system_prompt] + st.session_state.messages

                        try:
                            full_text, usage = call_llm_stream(client, messages_to_send)
                            update_tokens(usage)
                            st.session_state.messages.append({"role": "assistant", "content": full_text})
                        except Exception as e:
                            st.error(f"Viga: {e}")
            else:
                # ---- Jätkuvestlus: kasuta salvestatud RAG konteksti ----
                active = []
                if filter_semester != "Pole oluline":
                    active.append(f"semester: {filter_semester}")
                if filter_keel != "Pole oluline":
                    active.append(f"keel: {filter_keel}")
                if filter_oppeaste != "Pole oluline":
                    active.append(f"õppeaste: {filter_oppeaste}")
                if filter_veebiope != "Pole oluline":
                    active.append(f"õppeviis: {filter_veebiope}")
                if filter_linn != "Pole oluline":
                    active.append(f"linn: {filter_linn}")
                if filter_eap != (1, 36):
                    active.append(f"EAP: {filter_eap[0]}–{filter_eap[1]}")
                active_str = ", ".join(active) if active else "filtrid puuduvad"

                system_prompt = build_system_prompt(
                    st.session_state.rag_context,
                    st.session_state.course_names,
                    active_str,
                )
                messages_to_send = [system_prompt] + st.session_state.messages

                try:
                    full_text, usage = call_llm_stream(client, messages_to_send)
                    update_tokens(usage)
                    st.session_state.messages.append({"role": "assistant", "content": full_text})
                except Exception as e:
                    st.error(f"Viga: {e}")
