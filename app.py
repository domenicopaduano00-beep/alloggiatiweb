import streamlit as st
from datetime import datetime
import base64
import json
from openai import OpenAI

# Configurazione pagina Streamlit
st.set_page_config(page_title="Alloggiati Web - Multi-Ospite con IA", layout="wide")

# Inizializzazione client OpenAI usando la chiave salvata nei Secrets
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

CODICE_ITALIA = "100000100"

def estrai_dati_da_immagine(image_bytes, mime_type):
    """
    Invia l'immagine del documento a GPT-4o-mini chiedendo l'estrazione dati in formato JSON.
    """
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = """
    Analizza la foto di questo documento d'identità ed estrai i seguenti dati in formato JSON strictly valid.
    Rispondi SOLO ed ESCLUSIVAMENTE con il JSON senza altri blocchi di testo o frasi introduttive.

    Campi da estrarre:
    - nome: (stringa, MAIUSCOLO)
    - cognome: (stringa, MAIUSCOLO)
    - sesso: ("1" per Maschio, "2" per Femmina)
    - data_nascita: (formato GG/MM/AAAA)
    - comune_nascita: (nome del comune di nascita in MAIUSCOLO o dello Stato estero)
    - prov_nascita: (sigla provincia di 2 lettere in MAIUSCOLO, oppure vuoto se estero)
    - tipo_doc: ("IDENT" per carta d'identità, "PASSP" per passaporto, "PATEN" per patente)
    - num_doc: (numero del documento senza spazi, in MAIUSCOLO)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        # Pulizia da eventuali markup markdown es. ```json
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        dati = json.loads(content)
        return dati
    except Exception as e:
        st.error(f"Errore nella lettura dell'immagine via IA: {e}")
        return None

def formatta_riga_alloggiati(tipo_alloggiato, data_arrivo, permanenza, cognome, nome, sesso, 
                            data_nascita, comune_nascita, prov_nascita, stato_nascita, 
                            cittadinanza, tipo_doc, num_doc, rilascio_doc):
    """
    Formatta una riga posizionale da 168 caratteri per il portale Alloggiati Web.
    """
    riga = (
        f"{tipo_alloggiato:<2}"
        f"{data_arrivo:<10}"
        f"{permanenza:02d}"
        f"{cognome[:50]:<50}"
        f"{nome[:30]:<30}"
        f"{sesso:<1}"
        f"{data_nascita:<10}"
        f"{comune_nascita[:9]:<9}"
        f"{prov_nascita[:2]:<2}"
        f"{stato_nascita[:9]:<9}"
        f"{cittadinanza[:9]:<9}"
        f"{tipo_doc[:5]:<5}"
        f"{num_doc[:20]:<20}"
        f"{rilascio_doc[:9]:<9}"
    )
    return riga

# Intestazione App
st.title(" Alloggiati Web - Lettura IA da Foto")
st.write("Carica le foto dei documenti: l'Intelligenza Artificiale estrarrà automaticamente i dati dell'ospite.")

# Upload dei documenti
uploaded_files = st.file_uploader(
    "Carica foto di Carte d'Identità, Passaporti o Patenti", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    righe_txt = []
    
    st.info(f"📁 Documenti caricati: **{len(uploaded_files)}**. L'IA sta analizzando le immagini...")

    for idx, file in enumerate(uploaded_files):
        st.markdown("---")
        st.subheader(f"📄 Ospite #{idx+1} (File: {file.name})")
        
        # Leggi i byte della foto
        image_bytes = file.read()
        
        # Esegui l'OCR via IA solo se i dati non sono già presenti nello stato della sessione
        if f"dati_{idx}" not in st.session_state:
            with st.spinner("Estrazione dati in corso con IA..."):
                dati_estratti = estrai_dati_da_immagine(image_bytes, file.type)
                if not dati_estratti:
                    dati_estratti = {}
                st.session_state[f"dati_{idx}"] = dati_estratti
        else:
            dati_estratti = st.session_state[f"dati_{idx}"]

        # Scelta del ruolo per ciascun alloggiato
        tipo_alloggiato = st.selectbox(
            "Seleziona il Ruolo / Tipo Alloggiato",
            options=["16", "17", "18", "19", "20"],
            format_func=lambda x: {
                "16": "16 - Ospite Singolo",
                "17": "17 - Capo Famiglia",
                "18": "18 - Capo Gruppo",
                "19": "19 - Familiare (Esente da doc)",
                "20": "20 - Membro Gruppo (Esente da doc)"
            }[x],
            index=0 if idx == 0 else 3,
            key=f"tipo_{idx}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome", value=dati_estratti.get("nome", ""), key=f"nome_{idx}")
            cognome = st.text_input("Cognome", value=dati_estratti.get("cognome", ""), key=f"cog_{idx}")
            sesso_val = dati_estratti.get("sesso", "1")
            sesso = st.selectbox("Sesso (1=M, 2=F)", ["1", "2"], index=0 if sesso_val == "1" else 1, key=f"sesso_{idx}")
            data_nascita = st.text_input("Data Nascita (GG/MM/AAAA)", value=dati_estratti.get("data_nascita", ""), key=f"dn_{idx}")
            comune_nascita = st.text_input("Codice Belfiore / Comune Nascita (es. F839 per Napoli)", value=dati_estratti.get("comune_nascita", ""), key=f"cn_{idx}")
            
        with col2:
            prov_nascita = st.text_input("Provincia Nascita (es. NA)", value=dati_estratti.get("prov_nascita", ""), key=f"pn_{idx}")
            data_arrivo = st.text_input("Data Arrivo (GG/MM/AAAA)", value=datetime.today().strftime('%d/%m/%Y'), key=f"da_{idx}")
            permanenza = st.number_input("Notti Permanenza", value=3, min_value=1, key=f"perm_{idx}")

            if tipo_alloggiato in ["19", "20"]:
                tipo_doc = ""
                num_doc = ""
                st.caption("ℹ️ *I campi documento sono vuoti per familiari e membri del gruppo.*")
            else:
                doc_type_val = dati_estratti.get("tipo_doc", "IDENT")
                doc_index = 0
                if doc_type_val == "PASSP": doc_index = 1
                elif doc_type_val == "PATEN": doc_index = 2
                
                tipo_doc = st.selectbox("Tipo Documento", ["IDENT", "PASSP", "PATEN"], index=doc_index, key=f"td_{idx}")
                num_doc = st.text_input("Numero Documento", value=dati_estratti.get("num_doc", ""), key=f"nd_{idx}")

        # Generazione della riga posizionale per l'ospite corrente
        riga = formatta_riga_alloggiati(
            tipo_alloggiato=tipo_alloggiato,
            data_arrivo=data_arrivo,
            permanenza=int(permanenza),
            cognome=cognome.upper(),
            nome=nome.upper(),
            sesso=sesso,
            data_nascita=data_nascita,
            comune_nascita=comune_nascita.upper(),
            prov_nascita=prov_nascita.upper(),
            stato_nascita=CODICE_ITALIA,
            cittadinanza=CODICE_ITALIA,
            tipo_doc=tipo_doc,
            num_doc=num_doc.upper(),
            rilascio_doc=comune_nascita.upper() if tipo_doc else ""
        )
        righe_txt.append(riga)

    # Output del file finale
    contenuto_finale = "\r\n".join(righe_txt)
    contenuto_bytes = contenuto_finale.encode('iso-8859-1')

    st.markdown("---")
    st.subheader("📋 Anteprima del Testo Generato")
    st.code(contenuto_finale, language="text")
    
    st.download_button(
        label="📥 Scarica File .txt Unico per Alloggiati Web",
        data=contenuto_bytes,
        file_name=f"alloggiati_{datetime.today().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
