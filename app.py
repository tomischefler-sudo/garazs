import streamlit as st
import pandas as pd
import base64
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

# Kényszerítjük a memóriatörlést, hogy mindenki az élő online adatokat lássa azonnal
st.cache_data.clear()

# Kapcsolódás a Google Táblázathoz a Secrets-ben megadott link alapján
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Garazs")
    df.columns = df.columns.str.strip()  # Megtisztítjuk a fejléceket
except Exception as e:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bázis64", "Auto_Data_Link"])

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
        
        # Új autó sorának létrehozása
        new_row = pd.DataFrame([{
            "Tulajdonos": owner, 
            "Autó márkája": car_brand, 
            "Autó típusa": car_type, 
            "Évjárat": year,
            "Kép_Bázis64": img_base64,
            "Auto_Data_Link": auto_data_url
        }])
        
        # Hozzáadjuk az online adathoz és visszamentjük a Google Táblázatba
        df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=df, worksheet="Garazs")
        st.sidebar.success("Sikeresen elmentve!")
        st.rerun()
    else:
        st.sidebar.error("Kérlek, add meg a márkát és típust!")

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

if df.empty or len(df) == 0:
    st.info("A garázs listája még üres. Nyisd meg a bal oldali menüt a nyíllal (>), töltsd ki az adatokat, és mentsd el az első kisautódat!")
else:
    # Biztosítjuk az oszlopok meglétét
    szukseges_oszlopok = ["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bázis64", "Auto_Data_Link"]
    for col in szukseges_oszlopok:
        if col not in df.columns:
            df[col] = ""

    # Szűrés tulajdonos szerint
    tulajok = list(set([auto for auto in df["Tulajdonos"].dropna().astype(str) if auto.strip() != ""]))
    view_filter = st.selectbox("Szűrés tulajdonos szerint:", ["Mindegyik"] + tulajok)
    
    filtered_cars = df if view_filter == "Mindegyik" else df[df["Tulajdonos"] == view_filter]

    cols = st.columns(4)
    megjelenitett_autok = 0
    
    for idx, row in filtered_cars.iterrows():
        if pd.notna(row['Autó márkája']) and str(row['Autó márkája']).strip() != "":
            with cols[megjelenitett_autok % 4]:
                st.markdown(f"### {row['Autó márkája']}")
                st.markdown(f"**{row['Autó típusa']}**")
                st.caption(f"📅 Évjárat: {row['Évjárat']} | 👤: {row['Tulajdonos']}")
                
                if pd.notna(row['Kép_Bázis64']) and str(row['Kép_Bázis64']).strip() != "":
                    try:
                        img_bytes = base64.b64decode(str(row['Kép_Bázis64']))
                        st.image(img_bytes, use_container_width=True)
                    except Exception:
                        st.caption("ℹ️ Fénykép megjelenítési hiba.")
                else:
                    st.caption("ℹ️ Nincs saját fénykép feltöltve.")
                
                if pd.notna(row['Auto_Data_Link']) and str(row['Auto_Data_Link']).startswith("http"):
                    st.link_button("📊 Technikai adatok / Részletek", str(row['Auto_Data_Link']))
                
                st.markdown("---")
                megjelenitett_autok += 1
