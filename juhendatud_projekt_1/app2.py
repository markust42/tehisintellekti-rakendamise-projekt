import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Iluasjad: pealkiri, allkiri
st.title("🎓 AI Kursuse Nõustaja - Samm 2")
st.caption("Vestlus päris tehisintellektiga (Gemma 3).")

# Külgriba API võtme jaoks (sidebar) - kui .env-is pole, saab käsitsi sisestada
env_key = os.getenv("OPENROUTER_API_KEY", "")
api_key = st.sidebar.text_input("OpenRouter API võti:", value=env_key, type="password")

# 1. Algatame vestluse ajaloo, kui seda veel pole
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Kuvame vestluse senise ajaloo (History)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Korjame üles uue kasutaja sisendi
if prompt := st.chat_input("Kirjelda, mida soovid õppida..."):
    # Lisame kasutaja sisendi seansi ajalukku
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not api_key:
            error_msg = "⚠️ Palun sisesta OpenRouter API võti külgribas (või lisa .env faili)!"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )

            # --- PARANDATUD OSA ALGAB SIIT ---
            # Kuna Gemma 3 ei toeta eraldi "system" rolli, paneme süsteemi juhised
            # vestlusajaloo kõige esimese sõnumi sisse kokku kasutaja esimese küsimusega.
            
            api_messages = []
            system_instruction = "Süsteemi juhis: Sa oled abivalmis AI kursuse nõustaja. Aita kasutajal leida õppematerjale ja vasta tema küsimustele tehisintellekti õppimise kohta.\n\n---\n"

            for i, msg in enumerate(st.session_state.messages):
                if i == 0 and msg["role"] == "user":
                    # Esimene kasutaja sõnum saab süsteemi juhised endale ette
                    api_messages.append({
                        "role": "user", 
                        "content": system_instruction + msg["content"]
                    })
                else:
                    api_messages.append(msg)
            # --- PARANDATUD OSA LÕPPEB SIIN ---

            try:
                # Saadame mudelile modifitseeritud api_messages listi
                stream = client.chat.completions.create(
                    model="google/gemma-3-27b-it:free",
                    messages=api_messages,
                    stream=True
                )

                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Viga API-ga suhtlemisel: {e}")