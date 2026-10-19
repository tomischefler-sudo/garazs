import streamlit as st
import pandas as pd
import base64
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="MiniGarázs Katalógus")
st.title("🚗 Garázs + TTTT")

st.cache_data.clear()

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Beolvassuk a legelső fület az átalakításhoz, de a Garazs fülre mentünk
    df = conn.read(worksheet="Garazs")
    df.columns = df.columns.str.strip()
except Exception:
    df = pd.DataFrame(columns=["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"])

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
        
        new_row = pd.DataFrame([{
            "Tulajdonos": owner, 
            "Autó márkája": car_brand, 
            "Autó típusa": car_type, 
            "Évjárat": year,
            "Kép_Bazis64": img_base64,
            "Auto_Data_Link": auto_data_url
        }])
        
        df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=df, worksheet="Garazs")
        st.sidebar.success("Sikeresen elmentve!")
        st.rerun()
    else:
        st.sidebar.error("Kérlek, add meg a márkát és típust!")

# ---- 🛠️ AUTOMATIKUS ADAT-ÁTHELYEZŐ (MIGRÁCIÓ) ----
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Rendszereszközök")
st.sidebar.warning("Figyelem: Az alábbi gomb átmásolja az összes autót a régi táblázatból a Garázs fülre!")

if st.sidebar.button("🔄 Régi autók automatikus másolása"):
    try:
        # Beolvassuk a legelső (alapértelmezett) munkalapot, ahol a függőleges adatok vannak
        regi_df = conn.read()
        
        # Az első oszlop tartalmazza a tulajdonságokat (Ár, Tömeg, Származás, stb.)
        # A többi oszlop fejlécében vannak az autók nevei
        regi_autok = regi_df.columns[1:].tolist()
        
        uj_autok_listaja = []
        
        for auto in regi_autok:
            # Megpróbáljuk kiszedni az évjáratot vagy a származást a függőleges listából, ha van
            # Feltételezzük, hogy az autó neve pl: "Alfa Romeo Giulia (2016)" vagy hasonló, 
            # de ha a táblázatban van fix sor, onnan is olvashatjuk.
            
            # Kettészedjük a nevet Márkára és Típusra az első szóköz alapján
            nev_reszek = auto.strip().split(" ", 1)
            marka = nev_reszek[0] if len(nev_reszek) > 0 else "Ismeretlen"
            tipus = nev_reszek[1] if len(nev_reszek) > 1 else ""
            
            # Megkeressük a 'Származás' vagy 'Évjárat' sort a régi táblázatban az adott autó oszlopában
            szarmazas_sor = regi_df[regi_df.iloc[:, 0].astype(str).str.contains("Származás", na=False, case=False)]
            evjarat_ertek = ""
            if not szarmazas_sor.empty:
                evjarat_ertek = str(szarmazas_sor[auto].values[0]) # Átmenetileg a származást vagy egyéb adatot tesszük be infónak
            
            uj_autok_listaja.append({
                "Tulajdonos": "Tomi",  # Alapértelmezett gazda, a felületen utólag módosítható
                "Autó márkája": marka,
                "Autó típusa": tipus,
                "Évjárat": evjarat_ertek,
                "Kép_Bazis64": "",
                "Auto_Data_Link": ""
            })
        
        migralt_df = pd.DataFrame(uj_autok_listaja)
        
        # Összefűzzük a jelenlegi Garazs fül tartalmával, hogy semmi ne vesszen el
        vegleges_df = pd.concat([df, migralt_df], ignore_index=True).drop_duplicates(subset=["Autó márkája", "Autó típusa"])
        
        # Elmentjük a Google Táblázat Garazs fülére
        conn.update(data=vegleges_df, worksheet="Garazs")
        st.sidebar.success(f"Sikeresen átmásolva {len(uj_autok_listaja)} db autó!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Hiba az áthelyezés során: {e}")

# ---- FŐOLDAL: GYŰJTEMÉNY MEGJELENÍTÉSE ----
st.subheader("A gyűjtemény")

if not df.empty:
    df.columns = [str(col).strip() for col in df.columns]

szukseges_oszlopok = ["Tulajdonos", "Autó márkája", "Autó típusa", "Évjárat", "Kép_Bazis64", "Auto_Data_Link"]
for col in szukseges_oszlopok:
    if col not in df.columns:
        df[col] = ""

df_tisztitott = df[df["Autó márkája"].notna() & (df["Autó márkája"].astype(str).str.strip() != "")]

if df_tisztitott.empty:
    st.info("A garázs listája még üres. Nyisd meg a bal oldali menüt a nyíllal (>), töltsd ki az adatokat, és mentsd el az első kisautódat!")
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
            
            img_val = row.get('Kép_Bazis64', '')
            if pd.notna(img_val) and str(img_val).strip() != "":
                try:
                    img_bytes = base64.b64decode(str(img_val).strip())
                    st.image(img_bytes, use_container_width=True)
                except Exception:
                    st.caption("ℹ️ Fénykép megjelenítési hiba.")
            else:
                st.caption("ℹ️ Nincs saját fénykép feltöltve.")
            
            link_val = row.get('Auto_Data_Link', '')
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("📊 Technikai adatok / Részletek", str(link_val))
            
            st.markdown("---")
            megjelenitett_autok += 1
