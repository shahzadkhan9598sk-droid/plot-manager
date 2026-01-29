import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import get_geolocation
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(page_title="Plot Manager Pro", layout="wide")

# Modern UI Graphics (CSS)
st.markdown("""
    <style>
    /* Main Card Style */
    .plot-card {
        border-radius: 20px;
        padding: 25px;
        background: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        transition: transform 0.3s ease;
    }
    .plot-card:hover { transform: translateY(-5px); }
    
    /* Green for Available */
    .available-card { 
        border-top: 8px solid #28a745; 
        background: linear-gradient(180deg, #f8fff9 0%, #ffffff 100%);
    }
    
    /* Red for Booked */
    .booked-card { 
        border-top: 8px solid #dc3545; 
        background: linear-gradient(180deg, #fffafa 0%, #ffffff 100%);
    }
    
    /* Price Styling */
    .price-badge {
        font-size: 24px;
        font-weight: 800;
        color: #1e3a8a;
    }
    
    /* Status Labels */
    .status-lbl {
        padding: 6px 12px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-green { background-color: #d4edda; color: #155724; }
    .status-red { background-color: #f8d7da; color: #721c24; }
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

# Session Management
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'lat_val' not in st.session_state: st.session_state['lat_val'] = 0.0
if 'lon_val' not in st.session_state: st.session_state['lon_val'] = 0.0

# --- 4. Sidebar Branding ---
st.sidebar.title("🏢 Plot Portal")
st.sidebar.info("Live Status: Manage & Book Plots")

# --- 5. Navigation Tabs ---
tab1, tab2, tab3 = st.tabs(["📍 Site Map", "🏠 Plot Gallery", "🛠️ Admin Portal"])

# --- TAB 1: Site Map (Advanced Graphics) ---
with tab1:
    if not df.empty and 'Lat' in df.columns:
        fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                color="Status", 
                                color_discrete_map={"Available": "#28a745", "Booked": "#dc3545", "Sold": "#6c757d"},
                                zoom=14, height=600)
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0},
                          showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: Gallery View (Graphic Cards) ---
with tab2:
    st.subheader("Explore Available & Booked Plots")
    search = st.text_input("🔍 Search by Plot No or Location", placeholder="e.g. Plot 101...")
    
    f_df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)] if search else df
    
    for i, row in f_df.iterrows():
        is_booked = row['Status'] == "Booked"
        card_type = "booked-card" if is_booked else "available-card"
        lbl_type = "status-red" if is_booked else "status-green"
        
        st.markdown(f"""
        <div class="plot-card {card_type}">
            <div style="display: flex; justify-content: space-between;">
                <h2 style="margin:0; color:#333;">🏠 Plot #{row['Plot_No']}</h2>
                <span class="status-lbl {lbl_type}">{row['Status']}</span>
            </div>
            <p style="margin:10px 0; color:#777;">📍 {row['Location']}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top:20px;">
                <div style="font-size:18px; color:#555;">📐 <b>{row['Area_sqft']}</b> sqft</div>
                <div class="price-badge">₹ {row['Price_Lakhs']} Lakhs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # WhatsApp Inquiry Button with context
        wa_text = urllib.parse.quote(f"Hi, I want to inquire about Plot #{row['Plot_No']} (₹{row['Price_Lakhs']} L) at {row['Location']}.")
        st.link_button(f"📲 Inquiry for Plot {row['Plot_No']}", f"https://wa.me/919876543210?text={wa_text}")

# --- TAB 3: Admin Dashboard ---
with tab3:
    if not st.session_state['logged_in']:
        with st.container():
            st.subheader("🔑 Admin Secure Login")
            u = st.text_input("Admin ID")
            p = st.text_input("Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                if u == "admin" and p == "plot123":
                    st.session_state['logged_in'] = True
                    st.rerun()
    else:
        st.success("Admin Panel Active")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

        # GPS & Data Form
        st.markdown("---")
        st.subheader("➕ Quick Entry Form")
        if st.button("📍 Get Current Location (Site GPS)"):
            loc = get_geolocation()
            if loc:
                st.session_state['lat_val'] = loc['coords']['latitude']
                st.session_state['lon_val'] = loc['coords']['longitude']
                st.success("GPS Data Captured!")

        with st.form("admin_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_no = st.number_input("Plot No", step=1)
                p_loc = st.text_input("Location Name")
                p_stat = st.selectbox("Current Status", ["Available", "Booked", "Sold"])
            with col2:
                p_price = st.number_input("Price (₹ Lakhs)")
                p_lat = st.number_input("Latitude", value=st.session_state['lat_val'], format="%.6f")
                p_lon = st.number_input("Longitude", value=st.session_state['lon_val'], format="%.6f")
            
            if st.form_submit_button("Sync with Google Sheets", use_container_width=True):
                new_entry = pd.DataFrame([{"Plot_No": p_no, "Location": p_loc, "Status": p_stat, "Price_Lakhs": p_price, "Lat": p_lat, "Lon": p_lon}])
                final_df = pd.concat([df, new_entry], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL.strip(), data=final_df)
                st.balloons()
