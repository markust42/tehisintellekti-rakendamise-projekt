import os
import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

# Pealkirjad
st.title("🎓 AI Kursuse Nõustaja - RAGiga")
st.caption("Täisväärtuslik RAG süsteem semantilise otsinguga.")

# Külgriba API võtme jaoks (sidebar) - kui .env-is pole, saab käsitsi sisestada
env_key = os.getenv("OPENROUTER_API_KEY", "")
api_key = st.sidebar.text_input("OpenRouter API võti:", value=env_key, type="password")

# UUS
# Mudeli, andmetabeli ja vektoriseeritud andmete laadimine
# OLULINE: andmed on juba vektoriteks tehtud, loe need .pkl failist
# Eeldame, et puhtad_andmed_embeddings.pkl on pd.dataframe: veergudega (unique_ID, embedding}
# tuleb kasutada streamliti cache_resource, et me mudelit ja andmeid pidevalt uuesti ei laeks 
@st.cache_resource
def get_models():
    # Kasutame SentenceTransformer teeki ja sama mudelit, millega tehti embeddings
    embedder = SentenceTransformer("BAAI/bge-m3")
    df = pd.read_csv("puhtad_andmed.csv")
    embeddings_df = pd.read_pickle("puhtad_andmed_embeddings.pkl")
    # Koostame dict: unique_ID -> embedding vektor
    embeddings_dict = dict(zip(embeddings_df["unique_ID"], embeddings_df["embedding"]))
    return embedder, df, embeddings_dict

embedder, df, embeddings_dict = get_models()

# 1. Algatame vestluse ajaloo, kui seda veel pole
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Kuvame vestluse senise ajaloo (History)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. KOrjame üles kasutaja sõnumi
if prompt := st.chat_input("Kirjelda, mida soovid õppida..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not api_key:
            error_msg = "Palun sisesta API võti!"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            # UUS Semantiline otsing (RAG)
            with st.spinner("Otsin sobivaid kursusi..."):
                # Teeme kasutaja küsimusest vektori (query)
                query_vector = embedder.encode([prompt])

                # Ühendame .pkl failis olevad veerud csv-st loetud andmetabeliga
                merged_df = df.copy()
                merged_df["embedding"] = merged_df["unique_ID"].map(embeddings_dict)
                merged_df = merged_df.dropna(subset=["embedding"])

                # Arvutame koosinussarnasuse query ja "embedding" veeru vahel
                emb_matrix = np.stack(merged_df["embedding"].values)
                scores = cosine_similarity(query_vector, emb_matrix)[0]
                merged_df["skoor"] = scores

                # Sorteerime skoori alusel, võtame 5 parimat
                results_df = merged_df.sort_values("skoor", ascending=False).head(5)

                # Eemaldame ebavajalikud veerud
                results_df = results_df.drop(columns=["skoor", "embedding", "unique_ID"], errors="ignore")

                context_text = results_df.to_string()

            # 3. LLM vastus koos kontekstiga
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            system_prompt = {
                "role": "system", 
                "content": f"Oled nõustaja. Kasuta järgmisi RAGi leitud kursusi vastamiseks:\n\n{context_text}"
            }
            
            messages_to_send = [system_prompt] + st.session_state.messages
            
            try:
                stream = client.chat.completions.create(
                    model="google/gemma-3-27b-it",
                    messages=messages_to_send,
                    stream=True
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Viga: {e}")