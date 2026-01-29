import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import get_geolocation
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(page_title="Plot Manager Pro", layout="wide")

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
st.title("🏢 Advanced Plot Management System")
tab1, tab2, tab3 = st.tabs(["🗺️ Live Site Map", "📋 Plot Inventory", "🔐 Admin Dashboard"])

# --- TAB 1: Live Site Map ---
with tab1:
    st.subheader("📍 Interactive Property Map")
    if not df.empty and 'Lat' in df.columns:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                hover_data=["Location", "Price_Lakhs", "Status"],
                                color="Status", 
                                color_discrete_map={"Available": "green", "Sold": "red", "Booked": "orange"},
                                zoom=14, height=600)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No plot locations found. Add plots with Lat/Lon from Admin Panel.")

# --- TAB 2: Inventory Search & View ---
with tab2:
    st.subheader("🔍 Search Property")
    search_q = st.text_input("Enter Plot Number or Area...")
    
    # Filter Logic
    f_df = df[df.apply(lambda row: search_q.lower() in str(row).lower(), axis=1)] if search_q else df
    
    for i, row in f_df.iterrows():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; border-left: 10px solid {'green' if row['Status']=='Available' else 'red'}; margin-bottom: 10px; background-color: #fcfcfc;">
            <h3 style="margin:0;">Plot #{row['Plot_No']} - {row['Location']}</h3>
            <p><b>Price:</b> ₹{row['Price_Lakhs']} Lakhs | <b>Size:</b> {row['Area_sqft']} sqft | <b>Status:</b> {row['Status']}</p>
        </div>
        """, unsafe_allow_html=True)
        msg = urllib.parse.quote(f"Inquiry for Plot #{row['Plot_No']} at {row['Location']}")
        st.link_button("💬 Inquiry on WhatsApp", f"https://wa.me/919876543210?text={msg}")

# --- TAB 3: Admin Panel (With GPS & Form) ---
with tab3:
    if not st.session_state['logged_in']:
        st.subheader("🔒 Admin Authentication")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "admin" and p == "plot123":
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Wrong Credentials")
    else:
        st.success("Admin Login Successful")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.divider()
        st.subheader("➕ Add New Plot Details")

        # --- LIVE GPS CAPTURE BUTTON ---
        st.write("Click below while standing at the plot site:")
        if st.button("📍 Capture My Current GPS"):
            loc = get_geolocation()
            if loc:
                st.session_state['lat_val'] = loc['coords']['latitude']
                st.session_state['lon_val'] = loc['coords']['longitude']
                st.success(f"Captured: {st.session_state['lat_val']}, {st.session_state['lon_val']}")
            else:
                st.warning("Location access denied. Please enable GPS in browser.")

        # --- DATA ENTRY FORM ---
        with st.form("plot_entry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_p_no = st.number_input("Plot Number", step=1)
                new_p_loc = st.text_input("Location Name")
                new_p_area = st.number_input("Area (sqft)")
            with c2:
                new_p_price = st.number_input("Price (Lakhs)")
                new_p_status = st.selectbox("Status", ["Available", "Booked", "Sold"])
                # GPS values automatically filled from Capture button
                final_lat = st.number_input("Latitude", value=st.session_state['lat_val'], format="%.6f")
                final_lon = st.number_input("Longitude", value=st.session_state['lon_val'], format="%.6f")

            if st.form_submit_button("Submit to Inventory"):
                new_row = pd.DataFrame([{
                    "Plot_No": new_p_no, "Location": new_p_loc, "Area_sqft": new_p_area,
                    "Status": new_p_status, "Price_Lakhs": new_p_price, 
                    "Lat": final_lat, "Lon": final_lon
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL.strip(), data=updated_df)
                st.success("Property Added to Google Sheet!")
                st.balloons()

        st.divider()
        st.subheader("✏️ Bulk Edit Database")
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save All Changes"):
            conn.update(spreadsheet=SHEET_URL.strip(), data=edited_df)
            st.success("Database Synchronized!")
