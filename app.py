import streamlit as st
from datetime import datetime

# Configurazione pagina Streamlit
st.set_page_config(page_title="Alloggiati Web", layout="wide")

# Costanti di default per la Polizia di Stato
CODICE_ITALIA = "100000100"

def formatta_riga_alloggiati(tipo_alloggiato, data_arrivo, permanenza, cognome, nome, sesso, 
                            data_nascita, comune_nascita, prov_nascita, stato_nascita, 
                            cittadinanza, tipo_doc, num_doc, rilascio_doc):
    """
    Formatta una singola riga per il file TXT di Alloggiati Web (lunghezza esatta: 168 caratteri).
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
st.title(" Alloggiati Web")
st.write("Carica le foto dei documenti degli ospiti, seleziona il ruolo di ciascuno e genera il file `.txt` unico per alloggiati WEB.")

# Upload dei documenti
uploaded_files = st.file_uploader(
    "Carica le foto dei documenti (JPG, PNG)", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    righe_txt = []
    
    st.info(f"📁 Documenti caricati: **{len(uploaded_files)}**. Compila o verifica i dati di ciascun ospite sottostante.")

    for idx, file in enumerate(uploaded_files):
        st.markdown("---")
        st.subheader(f"📄 Ospite #{idx+1} (File: {file.name})")
        
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
            index=0 if idx == 0 else 3,  # Imposta di default il 1° come Singolo e i successivi come Familiari
            key=f"tipo_{idx}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome", value="MARIO", key=f"nome_{idx}")
            cognome = st.text_input("Cognome", value="ROSSI", key=f"cog_{idx}")
            sesso = st.selectbox("Sesso (1=M, 2=F)", ["1", "2"], index=0, key=f"sesso_{idx}")
            data_nascita = st.text_input("Data Nascita (GG/MM/AAAA)", value="15/05/1985", key=f"dn_{idx}")
            comune_nascita = st.text_input("Codice Belfiore / Comune Nascita (es. F839 per Napoli)", value="F839", key=f"cn_{idx}")
            
        with col2:
            prov_nascita = st.text_input("Provincia Nascita (es. NA)", value="NA", key=f"pn_{idx}")
            data_arrivo = st.text_input("Data Arrivo (GG/MM/AAAA)", value=datetime.today().strftime('%d/%m/%Y'), key=f"da_{idx}")
            permanenza = st.number_input("Notti Permanenza", value=3, min_value=1, key=f"perm_{idx}")

            # Se si tratta di un Familiare o Membro Gruppo, il documento può essere facoltativo/vuoto
            if tipo_alloggiato in ["19", "20"]:
                tipo_doc = ""
                num_doc = ""
                st.caption("ℹ️ *I campi documento sono vuoti per familiari e membri del gruppo.*")
            else:
                tipo_doc = st.selectbox("Tipo Documento", ["IDENT", "PASSP", "PATEN"], key=f"td_{idx}")
                num_doc = st.text_input("Numero Documento", value="CA12345AA", key=f"nd_{idx}")

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

    # Creazione della stringa finale unendo tutte le righe con il terminatore CRLF (\r\n)
    contenuto_finale = "\r\n".join(righe_txt)
    contenuto_bytes = contenuto_finale.encode('iso-8859-1')

    st.markdown("---")
    st.subheader("📋 Anteprima del Testo Generato")
    st.code(contenuto_finale, language="text")
    
    # Pulsante per il download del file .txt
    st.download_button(
        label="📥 Scarica File .txt Unico per Alloggiati Web",
        data=contenuto_bytes,
        file_name=f"alloggiati_{datetime.today().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )