import streamlit as st
import pandas as pd
import base64
import urllib.parse
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

# Kényszerítjük a memóriatörlést a friss adatokért
st.cache_data.clear()

# Kapcsolódás a Google Táblázathoz a Secrets-ben megadott link alapján
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    df.columns = df.columns.str.strip()  # Megtisztítjuk a fejléceket a szóközöktől
except Exception as e:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"])

TABLAZAT_LINK = "https://google.com"

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
        
        # Mivel a felhőből a közvetlen írás zárolva van, generálunk egy okos segédlinket,
        # ami megkönnyíti a táblázatba való kézi bevitelt, vagy használhatjátok a közvetlen megnyitást
        st.sidebar.success("Adatok előkészítve! Kattints az alábbi gombra a táblázat bővítéséhez:")
        st.sidebar.link_button("📝 Adatok átvitele a Google Táblázatba", TABLAZAT_LINK)
    else:
        st.sidebar.error("Kérlek, add meg a márkát és típust!")

st.sidebar.markdown("---")
st.sidebar.info("💡 A meglévő adatokat közvetlenül a Google Táblázat 'Garazs' fülén is bármikor átírhatjátok.")

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

if not df.empty:
    df.columns = [str(col).strip() for col in df.columns]

# Biztosítjuk a szükséges oszlopok meglétét
szukseges_oszlopok = ["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"]
for col in szukseges_oszlopok:
    if col not in df.columns:
        if col == "Kép_Bazis64" and "Kép_Bázis64" in df.columns:
            df.rename(columns={"Kép_Bázis64": "Kép_Bazis64"}, inplace=True)
        else:
            df[col] = ""

# Kiszűrjük a teljesen üres sorokat
df_tisztitott = df[df["Autó márkája"].notna() & (df["Autó márkája"].astype(str).str.strip() != "")]

if df_tisztitott.empty:
    st.info("A garázs listája még üres. Add hozzá az első autót a bal oldali menüben (>)!")
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
            
            # Fénykép kezelése és megjelenítése
            has_image = False
            img_val = row.get('Kép_Bazis64', '')
            if pd.notna(img_val) and str(img_val).strip() != "":
                if str(img_val).startswith("http"):
                    st.image(str(img_val), use_container_width=True)
                    has_image = True
                else:
                    try:
                        img_bytes = base64.b64decode(str(img_val).strip())
                        st.image(img_bytes, use_container_width=True)
                        has_image = True
                    except Exception:
                        st.caption("ℹ️ Fénykép megjelenítési hiba.")
            
            # UTÓLAGOS FÉNYKÉPFELTÖLTÉS OPCIÓ: Ha nincs fénykép, felajánljuk a pótlást
            if not has_image:
                st.warning("⚠️ Hiányzik a fénykép!")
                st.link_button("📷 Fénykép pótlása a Táblázatban", TABLAZAT_LINK)
            
            # Link gomb
            link_val = row.get('Auto_Data_Link', '')
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("📊 Technikai adatok / Részletek", str(link_val))
            else:
                # UTÓLAGOS LINKPÓTLÓ OPCIÓ
                st.link_button("🔗 Link hozzáadása", TABLAZAT_LINK)
            
            st.markdown("---")
            megjelenitett_autok += 1
