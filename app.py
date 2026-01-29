import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import urllib.parse
from geopy.geocoders import Nominatim

# --- 1. Page Config ---
st.set_page_config(page_title="Real Estate Pro", layout="wide")

# --- 2. Database & URL (Aapka Link) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1cHYIjWDbamIVXeVX_AwIydJtNgV5Z64JQ_2mrMqTE5I/edit?usp=sharing"

# --- 3. Google Sheets Connection ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL.strip())
    df = df.dropna(how="all")
except:
    df = pd.DataFrame(columns=["Plot_No", "Location", "Area_sqft", "Status", "Price_Lakhs", "Length", "Width", "Lat", "Lon"])

# Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. Main UI ---
st.title("🏗️ Smart Plot Management System")
tab1, tab2, tab3 = st.tabs(["🗺️ Site Map (Live GPS)", "📋 Inventory List", "🔐 Admin Panel"])

# --- TAB 1: Site Map (Live GPS) ---
with tab1:
    st.subheader("📍 Live Site Map")
    if not df.empty and 'Lat' in df.columns:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                hover_data=["Location", "Price_Lakhs"],
                                color="Status", zoom=14, height=600)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No location data found in Google Sheets.")

# --- TAB 2: Inventory Section ---
with tab2:
    st.subheader("📊 Property Inventory")
    search = st.text_input("🔍 Search Plot No or Location")
    
    # Filter
    f_df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)] if search else df
    
    for i, row in f_df.iterrows():
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"### Plot #{row['Plot_No']} - {row['Location']}")
                st.write(f"📏 Size: {row['Area_sqft']} sqft | 💰 Price: ₹{row['Price_Lakhs']} Lakhs")
            with col_b:
                st.write(f"Status: **{row['Status']}**")
                msg = urllib.parse.quote(f"I want to book Plot #{row['Plot_No']}")
                st.link_button("WhatsApp", f"https://wa.me/919876543210?text={msg}")
            st.divider()

# --- TAB 3: Admin Panel (With Add Plot Form) ---
with tab3:
    if not st.session_state['logged_in']:
        st.subheader("Admin Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "admin" and p == "plot123": # Yahan apna password badal sakte hain
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Login")
    else:
        st.success("Admin Access Granted")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

        # --- NEW FORM TO ADD PLOT ---
        st.markdown("---")
        st.subheader("📝 Add New Plot Entry")
        with st.form("new_plot_form", clear_on_submit=True):
            p_no = st.number_input("Plot Number", step=1)
            p_loc = st.text_input("Location Name")
            p_area = st.number_input("Area (sqft)")
            p_price = st.number_input("Price (Lakhs)")
            p_status = st.selectbox("Status", ["Available", "Booked", "Sold"])
            
            st.write("📍 GPS Coordinates (Google Map se dekh kar bharein)")
            p_lat = st.number_input("Latitude (e.g. 26.8467)", format="%.6f")
            p_lon = st.number_input("Longitude (e.g. 80.9462)", format="%.6f")
            
            submitted = st.form_submit_button("Add to Inventory")
            if submitted:
                # Naya data create karna
                new_data = pd.DataFrame([{
                    "Plot_No": p_no, "Location": p_loc, "Area_sqft": p_area,
                    "Status": p_status, "Price_Lakhs": p_price, "Lat": p_lat, "Lon": p_lon
                }])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL.strip(), data=updated_df)
                st.success("Plot successfully added to Google Sheets!")
                st.balloons()
