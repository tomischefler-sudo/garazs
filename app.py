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
    # Automatikusan a legelső (bal szélső) fület olvassa be, ha nincs megadva specifikus név
    df = conn.read()
    df.columns = df.columns.str.strip()  # Megtisztítjuk a fejléceket a szóközöktől
except Exception as e:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"])

# ---- OLDALSÁV: INFORMÁCIÓK ----
st.sidebar.header("ℹ️ Navigáció")
st.sidebar.info("💡 Az új autókat és azok adatait közvetlenül a Google Táblázatban tudjátok bővíteni, az alkalmazás pedig automatikusan megjeleníti őket itt!")

TABLAZAT_LINK = "https://google.com"
st.sidebar.link_button("📝 Google Táblázat megnyitása", TABLAZAT_LINK)

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

# Megtisztítjuk a betöltött táblázat oszlopneveit, hogy biztosan egyezzenek
if not df.empty:
    df.columns = [str(col).strip() for col in df.columns]

# Biztosítjuk a szükséges oszlopok megnyitását
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
    st.info("A garázs listája még üres a Google Táblázatban.")
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
