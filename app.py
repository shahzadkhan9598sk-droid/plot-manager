import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import get_geolocation
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(page_title="Admin Plot Control", layout="wide")

# Modern UI Graphics (CSS)
st.markdown("""
    <style>
    .admin-card {
        border-radius: 15px;
        padding: 20px;
        background: #f8f9fa;
        border-left: 8px solid #1e3a8a;
        margin-bottom: 20px;
    }
    .plot-card {
        border-radius: 15px;
        padding: 20px;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .status-booked { border-top: 5px solid #dc3545; }
    .status-available { border-top: 5px solid #28a745; }
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
st.sidebar.title("🏢 Plot Control Center")

# --- 5. Main Navigation (Admin First) ---
tab1, tab2 = st.tabs(["🔐 Admin Control Panel", "🌐 Public View (Gallery)"])

# --- TAB 1: ADMIN CONTROL PANEL (Sabse Pehle) ---
with tab1:
    if not st.session_state['logged_in']:
        st.subheader("🔑 Admin Secure Login")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            u = st.text_input("Admin ID", placeholder="username")
            p = st.text_input("Password", type="password", placeholder="password")
            if st.button("Login Now", use_container_width=True):
                if u == "admin" and p == "plot123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid ID or Password")
    else:
        # Logout & Welcome
        c_top1, c_top2 = st.columns([4,1])
        c_top1.success("Welcome back, Admin! Aap yahan se Site Map aur Inventory control kar sakte hain.")
        if c_top2.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

        # --- SECTION A: ADMIN SITE MAP ---
        st.markdown("### 🗺️ Live Site Map Control")
        if not df.empty and 'Lat' in df.columns:
            fig = px.scatter_mapbox(df, lat="Lat", lon="Lon", hover_name="Plot_No", 
                                    color="Status", 
                                    color_discrete_map={"Available": "#28a745", "Booked": "#dc3545", "Sold": "#6c757d"},
                                    zoom=14, height=400)
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)

        # --- SECTION B: NEW PLOT ENTRY FORM ---
        st.markdown("---")
        st.subheader("➕ Add New Plot & Live GPS")
        
        if st.button("📍 Stand on Plot & Capture GPS"):
            loc = get_geolocation()
            if loc:
                st.session_state['lat_val'] = loc['coords']['latitude']
                st.session_state['lon_val'] = loc['coords']['longitude']
                st.success(f"GPS Captured: {st.session_state['lat_val']}")

        with st.form("admin_inventory_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_no = st.number_input("Plot No", step=1)
                p_loc = st.text_input("Location Name")
                p_stat = st.selectbox("Status", ["Available", "Booked", "Sold"])
            with col2:
                p_price = st.number_input("Price (₹ Lakhs)")
                p_lat = st.number_input("Latitude", value=st.session_state['lat_val'], format="%.6f")
                p_lon = st.number_input("Longitude", value=st.session_state['lon_val'], format="%.6f")
            
            if st.form_submit_button("Update Inventory & Sheet", use_container_width=True):
                new_data = pd.DataFrame([{"Plot_No": p_no, "Location": p_loc, "Status": p_stat, "Price_Lakhs": p_price, "Lat": p_lat, "Lon": p_lon}])
                final_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL.strip(), data=final_df)
                st.balloons()
                st.success("Database Updated!")

        # --- SECTION C: BULK EDIT ---
        st.markdown("### ✏️ Edit Inventory Data")
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save Manual Changes"):
            conn.update(spreadsheet=SHEET_URL.strip(), data=edited_df)
            st.success("Changes Saved!")

# --- TAB 2: PUBLIC VIEW ---
with tab2:
    st.subheader("🏘️ Property Gallery")
    search = st.text_input("🔍 Search Plot...")
    
    f_df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)] if search else df
    
    for i, row in f_df.iterrows():
        status_cls = "status-booked" if row['Status']=="Booked" else "status-available"
        st.markdown(f"""
        <div class="plot-card {status_cls}">
            <h3>Plot #{row['Plot_No']} - {row['Location']}</h3>
            <p><b>Price:</b> ₹ {row['Price_Lakhs']} Lakhs | <b>Status:</b> {row['Status']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        wa_text = urllib.parse.quote(f"Hello, Inquiry for Plot #{row['Plot_No']}")
        st.link_button(f"Chat for Plot {row['Plot_No']}", f"https://wa.me/919876543210?text={wa_text}")
