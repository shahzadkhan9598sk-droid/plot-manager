import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(page_title="Plot Manager Pro", layout="wide")

# --- 2. Database & Admin Config ---
# Aapka Diya Hua Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1cHYIjWDbamIVXeVX_AwIydJtNgV5Z64JQ_2mrMqTE5I/edit?usp=sharing"

# Admin Details (Yahan badal sakte hain)
ADMIN_USER = "admin"
ADMIN_PWD = "admin123" 

# --- 3. Database Connection ---
try:
    # URL ko strip() kiya hai taaki extra space se error na aaye
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL.strip())
    df = df.dropna(how="all")
except Exception as e:
    st.error("Error connecting to Google Sheets. Please check your URL and Secrets.")
    df = pd.DataFrame(columns=["Plot_No", "Location", "Area_sqft", "Status", "Price_Lakhs", "Length", "Width", "Lat", "Lon"])

# Login session maintain karne ke liye
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. UI Design ---
st.title("🏗️ Digital Plot Manager")
tab1, tab2, tab3 = st.tabs(["🗺️ Site Map", "📋 Inventory & Booking", "🔐 Admin Panel"])

# --- TAB 1: Map ---
with tab1:
    st.subheader("📍 Live Location Map")
    if not df.empty and "Lat" in df.columns:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                color="Status", 
                                color_discrete_map={"Available": "green", "Sold": "red", "Booked": "orange"},
                                zoom=12, height=500)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No plot data with Lat/Lon available yet.")

# --- TAB 2: Inventory ---
with tab2:
    search = st.text_input("🔍 Search Plot No...")
    f_df = df[df["Plot_No"].astype(str).str.contains(search)] if search else df
    
    for i, row in f_df.iterrows():
        status_color = "green" if row['Status'] == "Available" else "red"
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; border-left: 10px solid {status_color}; margin-bottom: 15px; background-color: #f9f9f9;">
            <h3 style="margin:0;">🏠 Plot #{row['Plot_No']}</h3>
            <p style="margin:5px 0;">📍 <b>Location:</b> {row['Location']} | 💰 <b>Price:</b> ₹{row['Price_Lakhs']} Lakhs</p>
            <p style="margin:5px 0;">📐 <b>Size:</b> {row['Area_sqft']} sqft</p>
            <p style="margin:0;"><b>Status:</b> <span style="color:{status_color};">{row['Status']}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        msg = urllib.parse.quote(f"Hi, I'm interested in Plot #{row['Plot_No']} at {row['Location']}.")
        st.link_button(f"💬 WhatsApp Inquiry for #{row['Plot_No']}", f"https://wa.me/919876543210?text={msg}")

# --- TAB 3: Admin (Login) ---
with tab3:
    if not st.session_state['logged_in']:
        st.subheader("🔐 Admin Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == ADMIN_USER and p == ADMIN_PWD:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Credentials!")
    else:
        st.success("Welcome Admin!")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.write("### 🛠️ Edit Plot Database")
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save Changes to Google Sheet"):
            conn.update(spreadsheet=SHEET_URL.strip(), data=edited_df)
            st.success("Data Saved Successfully!")
