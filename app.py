import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from geopy.geocoders import Nominatim

# --- 1. Basic Page Configuration ---
st.set_page_config(page_title="Real Estate Plot Manager", layout="wide", initial_sidebar_state="collapsed")

# SETTINGS - Change these as needed
ADMIN_PASSWORD = "admin123" 
MY_PHONE_NUMBER = "919876543210" # Enter your number with Country Code (e.g., 91 for India)
# Clean URL to avoid Unicode Errors
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE"

# --- 2. Database Connection ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL.strip())
    df = df.dropna(how="all")
except Exception as e:
    st.error("Error connecting to Google Sheets. Please check your URL and Secrets.")
    df = pd.DataFrame(columns=["Plot_No", "Location", "Area_sqft", "Status", "Price_Lakhs", "Length", "Width", "Lat", "Lon"])

# --- 3. Session State Management ---
if 'logged_in' not in st.session_state: 
    st.session_state['logged_in'] = False

# --- 4. Main App UI ---
st.title("🏗️ Digital Plot Manager")
tab1, tab2, tab3 = st.tabs(["🗺️ Site Map", "📋 Inventory & Booking", "🔐 Admin Panel"])

# --- TAB 1: Map View ---
with tab1:
    st.subheader("📍 Live Location Map")
    if not df.empty:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                color="Status", 
                                color_discrete_map={"Available": "green", "Sold": "red", "Booked": "orange"},
                                zoom=12, height=500)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No plot data available to display on map.")

# --- TAB 2: Inventory List & Booking ---
with tab2:
    search_query = st.text_input("🔍 Search by Plot Number or Location...")
    
    # Filter Data
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df['Plot_No'].astype(str).str.contains(search_query) | 
                                 filtered_df['Location'].str.contains(search_query, case=False)]

    for i, row in filtered_df.iterrows():
        status_color = "green" if row['Status'] == "Available" else "red" if row['Status'] == "Sold" else "orange"
        
        # Design Plot Card
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; border-left: 10px solid {status_color}; margin-bottom: 15px; background-color: #f9f9f9;">
            <h3 style="margin:0;">🏠 Plot #{row['Plot_No']}</h3>
            <p style="margin:5px 0;">📍 <b>Location:</b> {row['Location']} | 💰 <b>Price:</b> ₹{row['Price_Lakhs']} Lakhs</p>
            <p style="margin:5px 0;">📐 <b>Size:</b> {row['Length']}x{row['Width']} ({row['Area_sqft']} sqft)</p>
            <p style="margin:0;"><b>Status:</b> <span style="color:{status_color};">{row['Status']}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            whatsapp_msg = urllib.parse.quote(f"Hello, I am interested in Plot #{row['Plot_No']} at {row['Location']}.")
            st.link_button("💬 WhatsApp Inquiry", f"https://wa.me/{MY_PHONE_NUMBER}?text={whatsapp_msg}")
        with col2:
            if row['Status'] == "Available":
                if st.button(f"📝 Book Plot #{row['Plot_No']}", key=f"book_{row['Plot_No']}"):
                    st.session_state['booking_id'] = row['Plot_No']
                    st.session_state['show_bk_form'] = True
        with col3:
            with st.expander("🧊 3D View"):
                fig_3d = go.Figure(data=[go.Mesh3d(x=[0, row['Length'], row['Length'], 0, 0, row['Length'], row['Length'], 0],
                                                 y=[0, 0, row['Width'], row['Width'], 0, 0, row['Width'], row['Width']],
                                                 z=[0, 0, 0, 0, 8, 8, 8, 8], color=status_color, opacity=0.5)])
                st.plotly_chart(fig_3d, use_container_width=True)

    # Booking Form
    if st.session_state.get('show_bk_form'):
        st.divider()
        st.markdown(f"### 💳 Booking Request for Plot #{st.session_state['booking_id']}")
        with st.form("booking_form"):
            user_name = st.text_input("Full Name")
            user_phone = st.text_input("Mobile Number")
            st.write("Token Amount: **₹5,100/-**")
            # Payment QR Placeholder
            st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=yourid@upi", width=150)
            utr_number = st.text_input("Transaction ID (UTR)")
            if st.form_submit_button("Submit Booking Request"):
                st.success("Request sent! Admin will verify your payment and update the status.")
                st.session_state['show_bk_form'] = False

# --- TAB 3: Admin Panel ---
with tab3:
    if not st.session_state['logged_in']:
        login_pwd = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if login_pwd == ADMIN_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Password!")
    else:
        st.subheader("🛠️ Admin Dashboard")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
            
        with st.expander("➕ Add New Plot (Auto Location)"):
            with st.form("admin_add_form"):
                new_id = st.text_input("Plot Number")
                new_addr = st.text_input("Address (e.g. Sector 5, Lucknow)")
                
                if st.form_submit_button("Verify Location"):
                    geolocator = Nominatim(user_agent="real_estate_app")
                    try:
                        loc_data = geolocator.geocode(new_addr)
                        if loc_data:
                            st.session_state['lat_val'] = loc_data.latitude
                            st.session_state['lon_val'] = loc_data.longitude
                            st.success(f"📍 Found: {loc_data.address}")
                        else:
                            st.warning("Location not found. Enter manually.")
                    except:
                        st.error("Service error.")
                
                new_price = st.number_input("Price (Lakhs)")
                new_status = st.selectbox("Status", ["Available", "Sold", "Booked"])
                new_lat = st.number_input("Latitude", value=st.session_state.get('lat_val', 0.0), format="%.6f")
                new_lon = st.number_input("Longitude", value=st.session_state.get('lon_val', 0.0), format="%.6f")
                
                if st.form_submit_button("Preview Data"):
                    st.info("Edit the Data Editor below and click 'Save All Changes' to submit.")

        st.write("### Data Management")
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save All Changes to Google Sheet"):
            conn.update(spreadsheet=SHEET_URL.strip(), data=edited_df)
            st.success("Database Updated Successfully!")
