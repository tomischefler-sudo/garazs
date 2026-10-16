import streamlit as st
import base64
import os

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

ADAT_FAJL = "garazs_adatok.csv"

# Ha még nem létezik a fájl, létrehozzuk a megfelelő fejlécekkel
if not os.path.exists(ADAT_FAJL):
    with open(ADAT_FAJL, "w", encoding="utf-8") as f:
        f.write("Tulajdonos,Auto markaja,Auto tipusa,Evjarat,Kep_Bazis64,Auto_Data_Link\n")

# Natív adatbeolvasás Pandas nélkül a hiba kikerülésére
autok_listaja = []
if os.path.exists(ADAT_FAJL):
    with open(ADAT_FAJL, "r", encoding="utf-8") as f:
        sorok = f.readlines()
        if len(sorok) > 1:
            for sor in sorok[1:]:
                # Csak a biztonságos felosztás érdekében
                elemek = sor.strip().split(";")
                if len(elemek) >= 6:
                    autok_listaja.append({
                        "Tulajdonos": elemek[0],
                        "Autó márkája": elemek[1],
                        "Autó típusa": elemek[2],
                        "Évjárat": elemek[3],
                        "Kép_Bázis64": elemek[4],
                        "Auto_Data_Link": elemek[5]
                    })

# ---- OLDALSÁV: ÚJ AUTÓ REGISZTRÁLÁSA ----
st.sidebar.header("➕ Új... autó hozzáadása")
owner = st.sidebar.selectbox("Tulajdonos", ["Gergő", "Barni", "Tomi", "Imola"])
car_brand = st.sidebar.text_input("Autó márkája")
car_type = st.sidebar.text_input("Autó típusa")
year = st.sidebar.text_input("Évjárat")

uploaded_file = st.sidebar.file_uploader("Fénykép feltöltése", type=["png", "jpg", "jpeg"])
auto_data_url = st.sidebar.text_input("Link", placeholder="https://...")

if st.sidebar.button("💾 Autó mentése a Garázsba"):
    if car_brand and car_type:
        img_base64 = ""
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            img_base64 = base64.b64encode(bytes_data).decode("utf-8")
        
        # Új sor hozzáfűzése a fájl végére natív módon
        biztonsagos_sor = f"{owner};{car_brand};{car_type};{year};{img_base64};{auto_data_url}\n"
        with open(ADAT_FAJL, "a", encoding="utf-8") as f:
            f.write(biztonsagos_sor)
            
        st.sidebar.success("Sikeresen elmentve!")
        st.rerun()
    else:
        st.sidebar.error("Kérlek, add meg a márkát és típust!")

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

if not autok_listaja:
    st.info("A garázs listája még üres. Nyisd meg a bal oldali menüt a nyíllal (>), töltsd ki az adatokat, és mentsd el az első kisautódat!")
else:
    # Tulajdonosok listája a szűréshez
    tulajok = list(set([auto["Tulajdonos"] for auto in autok_listaja if auto["Tulajdonos"] != ""]))
    view_filter = st.selectbox("Szűrés tulajdonos szerint:", ["Mindegyik"] + tulajok)
    
    filtered_cars = autok_listaja if view_filter == "Mindegyik" else [a for a in autok_listaja if a["Tulajdonos"] == view_filter]

    cols = st.columns(4)
    for idx, row in enumerate(filtered_cars):
        if row['Autó márkája'].strip() != "":
            with cols[idx % 4]:
                st.markdown(f"### {row['Autó márkája']}")
                st.markdown(f"**{row['Autó típusa']}**")
                st.caption(f"📅 Évjárat: {row['Évjárat']} | 👤: {row['Tulajdonos']}")
                
                if row['Kép_Bázis64'].strip() != "":
                    try:
                        img_bytes = base64.b64decode(row['Kép_Bázis64'])
                        st.image(img_bytes, use_container_width=True)
                    except Exception:
                        st.caption("ℹ️ Fénykép megjelenítési hiba.")
                else:
                    st.caption("ℹ️ Nincs saját fénykép feltöltve.")
                
                if row['Auto_Data_Link'].startswith("http"):
                    st.link_button("📊 Technikai adatok / Részletek", row['Auto_Data_Link'])
                
                st.markdown("---")
