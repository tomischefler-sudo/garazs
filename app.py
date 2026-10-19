import streamlit as st
import pandas as pd
import base64
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

# Kényszerítjük a memóriatörlést a friss adatokért
st.cache_data.clear()

# Kapcsolódás a Google Táblázathoz a Secrets-ben megadott link alapján
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ÚJÍTÁS: Nem adunk meg fülnevet, így automatikusan a legelső (bal szélső) fület olvassa be!
    df = conn.read()
    df.columns = df.columns.str.strip()  # Megtisztítjuk a fejléceket a szóközöktől
except Exception as e:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Base64", "Auto_Data_Link"])

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
            "Kép_Bazis64": img_base64,
            "Auto_Data_Link": auto_data_url
        }])
        
        # Hozzáadjuk az online adathoz és visszamentjük a Google Táblázatba
        df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=df)
        st.sidebar.success("Sikeresen elmentve!")
        st.rerun()
    else:
        st.sidebar.error("Kérlek, add meg a márkát és típust!")

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

# Megtisztítjuk a betöltött táblázat oszlopneveit, hogy biztosan egyezzenek
if not df.empty:
    df.columns = [str(col).strip() for col in df.columns]

# Biztosítjuk a szükséges oszlopok meglétét, ha a táblázat üres lenne
szukseges_oszlopok = ["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"]
for col in szukseges_oszlopok:
    if col not in df.columns:
        # Ha ékezetes formában van a táblázatban, átnevezzük a kódhoz
        if col == "Kép_Bazis64" and "Kép_Bázis64" in df.columns:
            df.rename(columns={"Kép_Bázis64": "Kép_Bazis64"}, inplace=True)
        else:
            df[col] = ""

# Kiszűrjük a teljesen üres sorokat
df_tisztitott = df[df["Autó márkája"].notna() & (df["Autó márkája"].astype(str).str.strip() != "")]

if df_tisztitott.empty:
    st.info("A garázs listája még üres. Nyisd meg a bal oldali menüt a nyíllal (>), töltsd ki az adatokat, és mentsd el az első kisautódat!")
else:
    # Szűrés tulajdonos szerint
    tulajok = list(set([str(auto).strip() for auto in df_tisztitott["Tulajdonos"].dropna() if str(auto).strip() != ""]))
    view_filter = st.selectbox("Szűrés tulajdonos szerint:", ["Mindegyik"] + tulajok)
    
    filtered_cars = df_tisztitott if view_filter == "Mindegyik" else df_tisztitott[df_tisztitott["Tulajdonos"] == view_filter]

    cols = st.columns(4)
    megjelenitett_autok = 0
    
    for idx, row in filtered_cars.iterrows():
        with cols[megjelenitett_autok % 4]:
            st.markdown(f"### {row['Autó márkája']}")
            st.markdown(f"**{row['Autó típusa']}**")
            st.caption(f"📅 Évjárat: {row['Évjárat']} | 👤: {row['Tulajdonos']}")
            
            # Fénykép megjelenítése
            img_val = row.get('Kép_Bazis64', '')
            if pd.notna(img_val) and str(img_val).strip() != "":
                try:
                    img_bytes = base64.b64decode(str(img_val).strip())
                    st.image(img_bytes, use_container_width=True)
                except Exception:
                    st.caption("ℹ️ Fénykép megjelenítési hiba.")
            else:
                st.caption("ℹ️ Nincs saját fénykép feltöltve.")
            
            # Link gomb
            link_val = row.get('Auto_Data_Link', '')
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("📊 Technikai adatok / Részletek", str(link_val))
            
            st.markdown("---")
            megjelenitett_autok += 1
