import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from geopy.geocoders import Nominatim

# --- CONFIG ---
st.set_page_config(page_title="Plot Manager Pro", layout="wide", initial_sidebar_state="collapsed")

# अपनी डिटेल्स यहाँ बदलें
ADMIN_PASSWORD = "admin123" 
MY_PHONE_NUMBER = "919876543210" # 91 के साथ अपना नंबर
SHEET_URL = "यहाँ_अपनी_गूगल_शीट_का_URL_पेस्ट_करें"

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=SHEET_URL)
df = df.dropna(how="all")

# --- LOGIN SESSION ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- UI TABS ---
st.title("🏡 Digital Plot App")
tab1, tab2, tab3 = st.tabs(["🗺️ नक्शा", "📋 इन्वेंटरी", "🔐 एडमिन"])

with tab1:
    st.subheader("प्लॉट की लोकेशन")
    if not df.empty:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", color="Status", zoom=12, height=450)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    search = st.text_input("प्लॉट नंबर खोजें...")
    filtered_df = df[df["Plot_No"].astype(str).str.contains(search)] if search else df
    
    for i, row in filtered_df.iterrows():
        color = "green" if row['Status'] == "Available" else "red"
        st.markdown(f"""<div style="border: 1px solid #ddd; padding: 10px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom:10px;">
            <h4>प्लॉट #{row['Plot_No']} - {row['Location']}</h4>
            <p>💰 ₹{row['Price_Lakhs']} लाख | 📏 {row['Area_sqft']} sqft</p>
            </div>""", unsafe_allow_html=True)
        
        # WhatsApp & Booking Buttons
        c1, c2 = st.columns(2)
        with c1:
            msg = urllib.parse.quote(f"Hello, I am interested in Plot #{row['Plot_No']}")
            st.link_button("💬 WhatsApp", f"https://wa.me/{MY_PHONE_NUMBER}?text={msg}")
        with c2:
            if row['Status'] == "Available":
                if st.button(f"📝 बुक करें #{row['Plot_No']}"):
                    st.info("पेमेंट के लिए एडमिन से संपर्क करें या QR स्कैन करें।")

with tab3:
    if not st.session_state['logged_in']:
        pwd = st.text_input("एडमिन पासवर्ड", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
    else:
        st.success("Welcome Admin!")
        # Auto Search Section
        geolocator = Nominatim(user_agent="plot_app")
        loc_name = st.text_input("नयी लोकेशन सर्च करें")
        if st.button("Search Lat/Lon"):
            location = geolocator.geocode(loc_name)
            if location:
                st.write(f"Lat: {location.latitude}, Lon: {location.longitude}")
        
        # Data Editor
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save Changes"):
            conn.update(spreadsheet=SHEET_URL, data=edited_df)
            st.toast("Data Saved!")