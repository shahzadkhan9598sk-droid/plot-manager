import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import get_geolocation
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(page_title="Plot Manager Pro", layout="wide")

# Custom CSS for better graphics (Card look)
st.markdown("""
    <style>
    .plot-card {
        border-radius: 15px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-left: 10px solid #25D366;
        margin-bottom: 20px;
    }
    .status-booked { border-left-color: #FF4B4B !important; }
    .status-sold { border-left-color: #808080 !important; }
    .price-tag { color: #1E88E5; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Database URL ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1cHYIjWDbamIVXeVX_AwIydJtNgV5Z64JQ_2mrMqTE5I/edit?usp=sharing"

# --- 3. Google Sheets Connection ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL.strip())
    df = df.dropna(how="all")
except:
    df = pd.DataFrame(columns=["Plot_No", "Location", "Area_sqft", "Status", "Price_Lakhs", "Lat", "Lon"])

# Session State for Login and GPS
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'lat_val' not in st.session_state: st.session_state['lat_val'] = 0.0
if 'lon_val' not in st.session_state: st.session_state['lon_val'] = 0.0

# --- 4. Main UI Tabs ---
st.title("🏙️ Plot Management Dashboard")
tab1, tab2, tab3 = st.tabs(["🗺️ Live Site Map", "📋 Plot Inventory", "🔐 Admin Dashboard"])

# --- TAB 1: Map View ---
with tab1:
    if not df.empty and 'Lat' in df.columns:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                color="Status", 
                                color_discrete_map={"Available": "#25D366", "Booked": "#FF4B4B", "Sold": "#808080"},
                                zoom=14, height=600)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: Inventory with Graphics ---
with tab2:
    search_q = st.text_input("🔍 Plot Number ya Location se search karein...")
    f_df = df[df.apply(lambda row: search_q.lower() in str(row).lower(), axis=1)] if search_q else df
    
    for i, row in f_df.iterrows():
        # Dynamic classes based on status
        card_class = "plot-card"
        if row['Status'] == "Booked": card_class += " status-booked"
        elif row['Status'] == "Sold": card_class += " status-sold"
        
        # HTML Card Design
        st.markdown(f"""
        <div class="{card_class}">
            <span style="float:right; font-weight:bold; color:#555;">Status: {row['Status']}</span>
            <h2 style="margin:0;">🏠 Plot #{row['Plot_No']}</h2>
            <p style="color:#666; font-size:16px;">📍 {row['Location']}</p>
            <hr>
            <div style="display: flex; justify-content: space-between;">
                <div>📏 <b>Area:</b> {row['Area_sqft']} sqft</div>
                <div class="price-tag">₹ {row['Price_Lakhs']} Lakhs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # WhatsApp Button with Rupee symbol in message
        msg = urllib.parse.quote(f"Mujhe Plot #{row['Plot_No']} (₹{row['Price_Lakhs']} Lakhs) ke baare mein jaankari chahiye.")
        st.link_button(f"💬 Plot #{row['Plot_No']} ke liye WhatsApp karein", f"https://wa.me/919876543210?text={msg}")

# --- TAB 3: Admin Panel ---
with tab3:
    if not st.session_state['logged_in']:
        st.subheader("🔐 Admin Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "admin" and p == "plot123":
                st.session_state['logged_in'] = True
                st.rerun()
    else:
        st.success("Welcome Admin!")
        # GPS & Form Logic (Same as before but with Rupee help text)
        st.info("Naya plot add karte waqt Price Lakhs mein likhein (Rupee symbol auto add ho jayega)")
        
        # Live GPS Capture Button
        if st.button("📍 Phone GPS se Location lein"):
            loc = get_geolocation()
            if loc:
                st.session_state['lat_val'] = loc['coords']['latitude']
                st.session_state['lon_val'] = loc['coords']['longitude']
                st.success("Location Captured!")

        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1:
                p_no = st.number_input("Plot No", step=1)
                p_loc = st.text_input("Location Name")
                p_price = st.number_input("Price (₹ Lakhs)")
            with c2:
                p_area = st.number_input("Area (sqft)")
                p_status = st.selectbox("Status", ["Available", "Booked", "Sold"])
                p_lat = st.number_input("Latitude", value=st.session_state['lat_val'], format="%.6f")
                p_lon = st.number_input("Longitude", value=st.session_state['lon_val'], format="%.6f")
            
            if st.form_submit_button("Sheet mein Save karein"):
                # Save logic here...
                new_row = pd.DataFrame([{"Plot_No": p_no, "Location": p_loc, "Area_sqft": p_area, "Status": p_status, "Price_Lakhs": p_price, "Lat": p_lat, "Lon": p_lon}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL.strip(), data=updated_df)
                st.success("Saved!")
