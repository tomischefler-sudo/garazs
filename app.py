import streamlit as st
import pandas as pd
import base64
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

st.cache_data.clear()

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    df.columns = df.columns.str.strip()
except Exception as e:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"])

# ---- OLDALSÁV: INFORMÁCIÓK ----
st.sidebar.header("ℹ️ Navigáció")
st.sidebar.info("💡 Az új autókat és adatokat közvetlenül a Google Táblázatban tudjátok bővíteni. Ha valami hiányzik (pl. fénykép), azt a kártyákon lévő gombokkal utólag is pótolhatjátok!")

TABLAZAT_LINK = "https://google.com"
st.sidebar.link_button("📝 Google Táblázat megnyitása", TABLAZAT_LINK)

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

if not df.empty:
    df.columns = [str(col).strip() for col in df.columns]

szukseges_oszlopok = ["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"]
for col in szukseges_oszlopok:
    if col not in df.columns:
        if col == "Kép_Bazis64" and "Kép_Bázis64" in df.columns:
            df.rename(columns={"Kép_Bázis64": "Kép_Bazis64"}, inplace=True)
        else:
            df[col] = ""

df_tisztitott = df[df["Autó márkája"].notna() & (df["Autó márkája"].astype(str).str.strip() != "")]

if df_tisztitott.empty:
    st.info("A garázs listája még üres a Google Táblázatban.")
else:
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
                # Ellenőrizzük, hogy közvetlen internetes link-e vagy Base64 kód
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
            
            # Ha nincs fénykép, felajánljuk a pótlást szövegesen, vagy egyedi linken keresztül
            if not has_image:
                st.warning("⚠️ Hiányzik a fénykép!")
                # Amíg nincs Google Form-otok, a táblázat linkjére irányítjuk őket pontosan az adott sorhoz
                st.link_button("📷 Fénykép link beillesztése a Táblázatba", TABLAZAT_LINK)
            
            # Külső link kezelése (Auto-Data vagy bármi más)
            link_val = row.get('Auto_Data_Link', '')
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("📊 Technikai adatok / Részletek", str(link_val))
            else:
                # Ha nincs link, itt is felajánljuk a közvetlen pótlást
                st.link_button("🔗 Link hozzáadása", TABLAZAT_LINK)
            
            st.markdown("---")
            megjelenitett_autok += 1
