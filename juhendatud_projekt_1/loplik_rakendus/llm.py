import streamlit as st

from config import MODEL_NAME


def build_system_prompt(context_text: str, course_names: list[str],
                        active_filters: str, total_count: int = 0,
                        filtered_count: int = 0) -> dict:
    """Builds the system-role message with RAG context."""
    allowlist = "\n".join(f"- {name}" for name in course_names)

    if active_filters == "filtrid puuduvad":
        filter_info = "Kasutaja ei rakendanud ühtegi metaandmete filtrit."
    else:
        filter_info = (
            f"Kasutaja rakendas järgmised filtrid: {active_filters}.\n"
            f"Filtrite tulemusel jäi andmestikku {filtered_count} kursust (kokku {total_count})."
        )

    return {
        "role": "system",
        "content": (
            "Oled Tartu Ülikooli kursuste nõustaja. Sinu ülesanne on anda lakoonilisi ja selgeid soovitusi.\n\n"
            f"{filter_info}\n\n"
            f"Süsteem leidis semantilise otsingu abil {len(course_names)} potentsiaalset kursust:\n"
            f"{allowlist}\n\n"
            f"TÄIELIKUD ANDMED NENDE KOHTA:\n{context_text}\n\n"
            "REEGLID LÕPLIKUKS VALIKUKS:\n"
            "1. Otsusta loetelu põhjal rangelt, millised kursused PÄRISELT sobivad kliendi sooviga.\n"
            "2. Esita asjakohased kursused konkreetsete ja lühikeste loetelupunktidena (bullet-points).\n"
            "3. Kui ükski ei sobi, ütle lihtsalt: Sobivaid kursuseid ei leidu.\n"
            "4. Sinu vastus EI TOHI sisaldada muid kursuseid peale nende, mis on nimekirjas.\n"
            "5. Iga sobiva kursuse juures pead väljastama JÄRGMISED read:\n"
            "   - **Kursuse nimi**\n"
            "   - Aine kood: [Aine Kood]\n"
            "   - ÕIS link: [URL]\n"
            "   - EAP: [EAP] | Keel: [Keel] | Õppeviis: [Õppeviis] | Semester: [Semester]\n"
            "   - 1-2 lauseline kokkuvõte aine kirjeldusest, ära uusi asju leiuta juurde.\n"
            "   - Sobivus: Lühike lause, miks see aine sobib kliendi päringuga.\n"
            "6. ÕIS link peab viitama samale ainekoodile; kui otsest URL-i ei ole andmetes, moodusta link kujul https://ois2.ut.ee/#/courses/[Aine Kood].\n"
            "7. Ära vabanda, ära räägi tehnilistest detailidest, filtritest, Andmebaasist ega RAG süsteemist.\n"
            "8. Ole kasutajaga viisakas ja sõbralik, kuid ära lisa ebavajalikku teksti."
        ),
    }


def call_llm_stream(client, messages_to_send):
    """Streams LLM response into a Streamlit placeholder. Returns (text, usage)."""
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages_to_send,
        stream=True,
        stream_options={"include_usage": True},
    )
    placeholder = st.empty()
    full_text, usage_data = "", None
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            full_text += chunk.choices[0].delta.content
            placeholder.markdown(full_text)
        if hasattr(chunk, "usage") and chunk.usage:
            usage_data = chunk.usage
    return full_text, usage_data
