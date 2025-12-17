import streamlit as st
import json
import os
import pandas as pd
import sys
import datetime
import time
try:
    from gtts import gTTS
    import io
    import base64
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Add 'src' to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.diagnosis import analyze_vehicle
from src.agent_graph import app as agent_app
from src.utils import fetch_owner_details
from src.chatbot import get_chatbot
from src.mqim import get_mqim
from src.ueba import get_ueba, USERS_DB
from src.database import get_database
from src.analytics import FleetAnalytics

# --- CONFIGURATION ---
st.set_page_config(
    page_title="AutoGuard Enterprise Command Center",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🔷"
)

# Force sidebar to stay visible
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

# --- CUSTOM CSS MATCHING TEMPLATE ---
st.markdown("""
<style>
    /* Main background - Light blue for login, will be overridden for dashboard */
    .stApp {
        background-color: #E8F0F8;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Sidebar styling - Lighter blue for better readability, 46% wider */
    [data-testid="stSidebar"] {
        background: #4A5F8C !important;
        padding: 2rem 1.5rem;
        min-width: 380px !important;
        max-width: 380px !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar text - white by default */
    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }
    
    /* Override for button text specifically - BLACK text in white buttons */
    [data-testid="stSidebar"] button[kind="secondary"] p,
    [data-testid="stSidebar"] button[kind="secondary"] div,
    [data-testid="stSidebar"] button[kind="secondary"] span,
    [data-testid="stSidebar"] button[kind="secondary"] * {
        color: #2C3E50 !important;
    }
    
    /* Ensure Logout button text is also visible */
    [data-testid="stSidebar"] button[kind="secondary"]::before {
        color: #2C3E50 !important;
    }
    
    /* Force sidebar to stay expanded */
    [data-testid="stSidebar"][aria-expanded="false"] {
        margin-left: 0 !important;
        transform: none !important;
    }
    
    /* Hide sidebar collapse button if needed */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Full width content - maximize horizontal space */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Main content area - maximize width */
    .main {
        margin-left: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure content doesn't hide behind sidebar */
    section[data-testid="stSidebar"] + section {
        padding-left: 1rem;
    }
    
    /* Make columns use full width */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    /* Maximize container width */
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Typography - Much larger for readability */
    h1 {
        font-size: 32px !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        color: #2C3E50 !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-size: 28px !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
        margin-bottom: 0.75rem !important;
    }
    
    p {
        font-size: 16px !important;
        line-height: 1.6 !important;
        color: #6C757D !important;
    }
    
    /* Subheader styling */
    .stSubheader {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
    }
    
    /* Card styling - Matching template with optimized padding */
    .metric-card {
        background: white;
        padding: 24px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: none;
        margin: 0;
        transition: all 0.2s ease;
        height: 100%;
        width: 100%;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    
    .status-card {
        background: white;
        padding: 24px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 0;
        width: 100%;
    }
    
    /* Icon placeholder */
    .metric-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 12px;
    }
    
    /* Status badges - Template colors */
    .status-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
        margin: 4px 0;
    }
    
    /* Template Color Palette */
    /* Primary: Navy Blue (#3B4A8C) */
    /* Success: Green (#4CAF50) */
    /* Warning: Orange (#FF9F43) */
    /* Danger: Red (#E74C3C) */
    
    .badge-critical {
        background-color: #FADBD8;
        color: #C0392B;
        border: none;
    }
    
    .badge-high {
        background-color: #FFE8D1;
        color: #E67E22;
        border: none;
    }
    
    .badge-medium {
        background-color: #FFF4E0;
        color: #FF9F43;
        border: none;
    }
    
    .badge-low {
        background-color: #D6EAF8;
        color: #2E86C1;
        border: none;
    }
    
    .badge-normal {
        background-color: #D5F4E6;
        color: #27AE60;
        border: none;
    }
    
    /* Metrics styling - Much larger */
    [data-testid="stMetricValue"] {
        font-size: 42px !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 15px !important;
        color: #95A5A6 !important;
        font-weight: 600 !important;
        margin-bottom: 10px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Buttons - 3-color scheme (Blue, White, Black) */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 17px;
        border: none;
        padding: 14px 28px;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: #4A5F8C !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(74, 95, 140, 0.3);
    }
    
    .stButton > button[kind="primary"] p {
        color: #FFFFFF !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #3B4D70 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(74, 95, 140, 0.4);
        transform: translateY(-1px);
    }
    
    .stButton > button[kind="secondary"] {
        background: white !important;
        color: #000000 !important;
        border: 2px solid #4A5F8C;
    }
    
    .stButton > button[kind="secondary"] p {
        color: #000000 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #E8F0F8 !important;
        color: #000000 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #F5F7FA !important;
        border-color: #3B4D70;
        color: #1E293B !important;
    }
    
    /* Tables - Light/White theme, larger fonts, full width - AGGRESSIVE BLACK TEXT */
    
    /* Streamlit dataframe container - white background */
    [data-testid="stDataFrame"] {
        background-color: white !important;
    }
    
    [data-testid="stDataFrame"] > div {
        background-color: white !important;
    }
    
    /* Force white background on all table elements */
    div[data-testid="stDataFrame"] div {
        background-color: white !important;
    }
    
    /* AGGRESSIVE Force BLACK text on ALL table elements */
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrame"] div,
    div[data-testid="stDataFrame"] span,
    div[data-testid="stDataFrame"] p,
    div[data-testid="stDataFrame"] td,
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] tbody,
    div[data-testid="stDataFrame"] thead {
        color: #000000 !important;
    }
    
    .dataframe {
        border: none !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        width: 100% !important;
        background-color: white !important;
    }
    
    .dataframe * {
        color: #000000 !important;
    }
    
    .dataframe thead tr th {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        border: none !important;
        border-bottom: 2px solid #E0E6ED !important;
        padding: 18px !important;
        text-align: left !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .dataframe tbody tr td {
        border: none !important;
        border-bottom: 1px solid #E8EDF5 !important;
        padding: 18px !important;
        font-size: 16px !important;
        color: #000000 !important;
        background-color: white !important;
    }
    
    .dataframe tbody tr:last-child td {
        border-bottom: none !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #F5F8FA !important;
    }
    
    .dataframe tbody tr:hover td {
        background-color: #F5F8FA !important;
        color: #000000 !important;
    }
    
    /* Override Streamlit's default table styling */
    .stDataFrame, .stDataFrame * {
        background-color: white !important;
        color: #000000 !important;
    }
    
    /* Table headers in light gray with BLACK text */
    table thead th, table thead th * {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border-bottom: 2px solid #E0E6ED !important;
    }
    
    /* Table body cells white with BLACK text */
    table tbody td, table tbody td * {
        background-color: white !important;
        color: #000000 !important;
        border-bottom: 1px solid #E8EDF5 !important;
    }
    
    /* Table row hover */
    table tbody tr:hover, table tbody tr:hover * {
        background-color: #F5F8FA !important;
        color: #000000 !important;
    }
    
    table tbody tr:hover td, table tbody tr:hover td * {
        background-color: #F5F8FA !important;
        color: #000000 !important;
    }
    
    /* Override ALL possible text color properties */
    table, table * {
        color: #000000 !important;
    }
    
    /* Tabs - Template style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 0;
        border-bottom: 2px solid #E0E6ED;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 14px;
        color: #6C757D;
        background: transparent;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #3B4A8C;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #3B4A8C !important;
        border-bottom-color: #3B4A8C !important;
        font-weight: 600 !important;
    }
    
    /* Input fields - 3-color scheme */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E0E6ED;
        padding: 14px 18px;
        font-size: 17px;
        color: #2C3E50;
        transition: all 0.2s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4A5F8C;
        box-shadow: 0 0 0 3px rgba(74, 95, 140, 0.1);
        outline: none;
    }
    
    .stTextInput label {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #2C3E50 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3B4A8C;
        box-shadow: 0 0 0 3px rgba(59, 74, 140, 0.1);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #95A5A6;
    }
    
    /* Selectbox - Larger */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #E0E6ED;
        padding: 6px;
        transition: all 0.2s ease;
        background: white !important;
        font-size: 17px;
    }
    
    /* Selectbox text color - Make it visible! */
    .stSelectbox > div > div > div {
        color: #000000 !important;
        background: white !important;
    }
    
    .stSelectbox input {
        color: #000000 !important;
        background: white !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: white !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        color: #000000 !important;
        background: white !important;
    }
    
    .stSelectbox [data-baseweb="select"] span {
        color: #000000 !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #BDC3C7;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #4A5F8C;
        box-shadow: 0 0 0 3px rgba(74, 95, 140, 0.1);
    }
    
    .stSelectbox label, .stMultiSelect label {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #2C3E50 !important;
    }
    
    /* Selectbox dropdown options */
    [data-baseweb="popover"] {
        background: white !important;
    }
    
    [data-baseweb="menu"] {
        background: white !important;
    }
    
    [data-baseweb="menu"] > ul {
        background: white !important;
    }
    
    [data-baseweb="menu"] li {
        color: #000000 !important;
        background: white !important;
    }
    
    [data-baseweb="menu"] li > div {
        color: #000000 !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background: #E8F0F8 !important;
        color: #000000 !important;
    }
    
    [role="option"] {
        color: #000000 !important;
        background: white !important;
    }
    
    [role="option"]:hover {
        background: #E8F0F8 !important;
    }
    
    /* Multi-select larger */
    .stMultiSelect > div > div {
        font-size: 17px;
        padding: 8px 12px;
    }
    
    /* Progress bars - Template colors */
    .stProgress > div > div > div {
        background: #3B4A8C;
        border-radius: 4px;
    }
    
    .stProgress > div > div {
        background: #E0E6ED;
        border-radius: 4px;
    }
    
    /* Expander - Clean design */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
        font-weight: 500;
        font-size: 14px;
        color: #334155;
        padding: 12px;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #F8FAFC;
        border-color: #CBD5E1;
    }
    
    /* Chat messages - Generous spacing */
    .stChatMessage {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    
    /* Alert boxes - 3-color scheme */
    .stAlert {
        border-radius: 8px;
        border: 2px solid;
        padding: 14px 16px;
        margin: 12px 0;
        font-size: 15px;
        font-weight: 500;
    }
    
    /* Success - Blue theme */
    [data-testid="stSuccess"] {
        background-color: #E8F0F8;
        color: #2C3E50;
        border-color: #4A5F8C;
    }
    
    /* Warning - Black/White theme */
    [data-testid="stWarning"] {
        background-color: white;
        color: #2C3E50;
        border-color: #2C3E50;
    }
    
    /* Error - Black on white */
    [data-testid="stError"] {
        background-color: #F5F5F5;
        color: #2C3E50;
        border-color: #2C3E50;
    }
    
    /* Info - Blue theme */
    [data-testid="stInfo"] {
        background-color: #E8F0F8;
        color: #2C3E50;
        border-color: #4A5F8C;
    }
    
    /* Remove clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide Streamlit header toolbar */
    header[data-testid="stHeader"] {
        background: transparent !important;
        visibility: hidden !important;
    }
    
    /* Keep sidebar toggle visible */
    button[kind="header"] {
        visibility: visible !important;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 1rem !important;
    }
    
    /* Remove top margin/padding */
    .stApp > header {
        background-color: transparent !important;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Maximize horizontal width for all content */
    [data-testid="stVerticalBlock"] > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Full width for horizontal layouts */
    [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        gap: 1rem !important;
    }
    
    /* Remove excessive margins */
    .element-container {
        width: 100% !important;
    }
    
    /* Sidebar navigation items - Much larger font with proper contrast */
    [data-testid="stSidebar"] button {
        border-radius: 8px;
        margin: 10px 0;
        font-size: 19px;
        padding: 18px 24px;
        text-align: left;
        background: transparent;
        color: white !important;
        border: none;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] button:hover {
        background: rgba(255, 255, 255, 0.15);
        color: white !important;
    }
    
    /* Active/selected button - darker blue background with WHITE text */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Ensure ALL text in active button is WHITE */
    [data-testid="stSidebar"] button[kind="primary"] p,
    [data-testid="stSidebar"] button[kind="primary"] div,
    [data-testid="stSidebar"] button[kind="primary"] span,
    [data-testid="stSidebar"] button[kind="primary"] * {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    }
    
    /* Secondary buttons (white background) - make text BLACK */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: white !important;
        color: #2C3E50 !important;
        font-weight: 500;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }
    
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: #F5F7FA !important;
        color: #1E293B !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'vehicles.json')

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "dashboard"
if "selected_vehicle" not in st.session_state:
    st.session_state["selected_vehicle"] = None
if "live_messages" not in st.session_state:
    st.session_state["live_messages"] = []
if "diagnosis_result" not in st.session_state:
    st.session_state["diagnosis_result"] = None

# --- HELPERS ---
@st.cache_data(ttl=1)  # Cache for 1 second to allow updates
def load_data(db_path: str):
    if not os.path.exists(db_path):
        return []
    # Get file modification time to force cache refresh on file change
    mtime = os.path.getmtime(db_path)
    with open(db_path, 'r') as f:
        vehicles = json.load(f)
    
    # Transform nested structure to flat structure for dashboard
    flattened = []
    for vehicle in vehicles:
        # Quick diagnosis based on telemetry
        tel = vehicle.get('telematics', {})
        brake_mm = tel.get('brake_pad_thickness_mm', 10)
        coolant_temp = tel.get('coolant_temp_c', 90)
        battery_v = tel.get('battery_voltage_v', 12.6)
        
        # Determine status and issue
        if brake_mm < 3:
            status = 'Critical'
            issue = f'Critical Brake Wear ({brake_mm}mm)'
            confidence = '99%'
        elif coolant_temp > 110:
            status = 'High'
            issue = f'Engine Overheating ({coolant_temp}°C)'
            confidence = '95%'
        elif battery_v < 12.0:
            status = 'High'
            issue = f'Low Battery ({battery_v}V)'
            confidence = '90%'
        elif brake_mm < 5:
            status = 'Medium'
            issue = f'Brake Wear ({brake_mm}mm)'
            confidence = '85%'
        elif coolant_temp > 100:
            status = 'Medium'
            issue = f'High Temperature ({coolant_temp}°C)'
            confidence = '80%'
        elif battery_v < 12.4:
            status = 'Low'
            issue = f'Battery Check ({battery_v}V)'
            confidence = '75%'
        else:
            status = 'Normal'
            issue = 'None'
            confidence = '100%'
        
        flat_vehicle = {
            'vehicle_id': vehicle.get('vehicle_id', 'Unknown'),
            'owner': vehicle.get('owner_name', 'Unknown'),
            'make': vehicle.get('metadata', {}).get('make', 'Unknown'),
            'model': vehicle.get('metadata', {}).get('model', 'Unknown'),
            'status': status,
            'current_issue': issue,
            'confidence': confidence
        }
        flattened.append(flat_vehicle)
    
    return flattened

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# --- AUTHENTICATION VIEW ---
def render_login():
    # Simple centered login page
    st.markdown("""
    <style>
        /* Hide default elements */
        header {display: none !important;}
        #MainMenu {display: none !important;}
        footer {display: none !important;}
        .stDeployButton {display: none !important;}
        section[data-testid="stSidebar"] {display: none !important;}
        
        /* Center the login form */
        .block-container {
            max-width: 500px;
            padding-top: 5rem;
        }
        
        /* Login box styling */
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        st.markdown("""
        <h1 style="text-align: center; color: #2C3E50; margin-bottom: 8px;">AutoGuard Fleet Command</h1>
        <p style="text-align: center; color: #7F8C8D; margin-bottom: 30px;">Secure Access Portal</p>
        """, unsafe_allow_html=True)
        
        email = st.text_input("Email Address", placeholder="user@autoguard.com", key="email_input")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="password_input")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Sign In", type="primary", use_container_width=True):
                if email:
                    ueba = get_ueba()
                    success, user_info, error = ueba.authenticate_user(email, password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = user_info
                        ueba.log_activity(user_info['user_id'], "login", {"location": "Dashboard", "timestamp": get_time()})
                        st.rerun()
                else:
                    st.error("Please enter your email")
        
        with col_b:
            if st.button("Quick Demo", type="secondary", use_container_width=True):
                ueba = get_ueba()
                demo_email = "alice.manager@autoguard.com"
                success, user_info, error = ueba.authenticate_user(demo_email, "password")
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = user_info
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN DASHBOARD ---
def render_dashboard(user):
    # Override login page background for dashboard
    st.markdown("""
    <style>
        .stApp {
            background-color: #F5F7FA !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Force sidebar to stay visible with JavaScript
    st.markdown("""
    <script>
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            sidebar.style.transform = 'none';
            sidebar.style.marginLeft = '0';
        }
    </script>
    """, unsafe_allow_html=True)
    
    # === SIDEBAR NAVIGATION ===
    with st.sidebar:
        # Logo/Header
        st.markdown("""
        <div style="padding: 20px 15px; margin-bottom: 30px; border-bottom: 2px solid rgba(255,255,255,0.2);">
            <div style="font-size: 28px; font-weight: 600; color: white; margin-bottom: 8px; letter-spacing: -0.5px;">AUTOGUARD</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 2px;">Fleet Command</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        if 'active_page' not in st.session_state:
            st.session_state.active_page = 'fleet'
        
        st.markdown('<div style="margin-bottom: 30px; color: rgba(255,255,255,0.7); font-size: 23px; text-transform: uppercase; letter-spacing: 3px; padding: 0 30px; font-weight: 600;">Navigation</div>', unsafe_allow_html=True)
        
        if st.button("Dashboard", key="nav_dashboard", type="primary" if st.session_state.active_page == 'fleet' else "secondary", use_container_width=True):
            st.session_state.active_page = 'fleet'
            st.rerun()
        
        if st.button("Manufacturing", key="nav_manufacturing", type="primary" if st.session_state.active_page == 'manufacturing' else "secondary", use_container_width=True):
            st.session_state.active_page = 'manufacturing'
            st.rerun()
        
        if st.button("Security", key="nav_security", type="primary" if st.session_state.active_page == 'security' else "secondary", use_container_width=True):
            st.session_state.active_page = 'security'
            st.rerun()
        
        if st.button("Analytics", key="nav_analytics", type="primary" if st.session_state.active_page == 'analytics' else "secondary", use_container_width=True):
            st.session_state.active_page = 'analytics'
            st.rerun()
        
        if st.button("Customer Chat", key="nav_chat", type="primary" if st.session_state.active_page == 'chat' else "secondary", use_container_width=True):
            st.session_state.active_page = 'chat'
            st.rerun()
        
        if st.button("Service Operations", key="nav_scheduling", type="primary" if st.session_state.active_page == 'scheduling' else "secondary", use_container_width=True):
            st.session_state.active_page = 'scheduling'
            st.rerun()
        
        # User info at bottom
        st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 16px 20px; border-radius: 8px;">
            <div style="font-weight: 600; font-size: 16px; margin-bottom: 6px; color: white;">
                """ + user['name'] + """
            </div>
            <div style="font-size: 13px; opacity: 0.8; color: rgba(255,255,255,0.9);">
                """ + user['role'].replace('_', ' ').title() + """
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        
        if st.button("Logout", type="secondary", use_container_width=True):
            # Log logout activity
            ueba = get_ueba()
            ueba.log_activity(
                user['user_id'],
                "logout",
                {"timestamp": get_time()}
            )
            
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = None
            st.rerun()
    
    # === MAIN CONTENT AREA ===
    # Render content based on active page
    if st.session_state.active_page == 'fleet':
        render_fleet_dashboard(user)
    elif st.session_state.active_page == 'manufacturing':
        render_mqim_dashboard(user)
    elif st.session_state.active_page == 'security':
        render_ueba_dashboard(user)
    elif st.session_state.active_page == 'analytics':
        render_analytics_dashboard(user)
    elif st.session_state.active_page == 'chat':
        render_customer_chat(user)
    elif st.session_state.active_page == 'scheduling':
        render_scheduling_page(user)

def run_full_diagnostic(vehicle_id, user):
    """Run the full multi-agent diagnostic workflow"""
    with st.spinner("Running comprehensive diagnostic analysis..."):
        # Log the diagnostic action
        ueba = get_ueba()
        ueba.log_activity(
            user['user_id'],
            "run_diagnostics",
            {"vehicle_id": vehicle_id, "timestamp": get_time()}
        )
        
        # Run the agent workflow
        initial_state = {
            "vehicle_id": vehicle_id,
            "user_id": user['user_id'],
            "telematics_data": {},
            "diagnosis_report": {},
            "severity": "Unknown",
            "messages": [],
            "mqim_notification": {},
            "security_threat": {}
        }
        
        result = agent_app.invoke(initial_state)
        
        # Save results to session state
        st.session_state["diagnosis_result"] = result
        
        # Display results
        if result.get('security_threat', {}).get('blocked'):
            st.error("🚫 Access Denied: Security threat detected. This action has been blocked.")
        else:
            st.success("✅ Diagnostic complete!")
            
            # Show severity
            severity = result.get('severity', 'Unknown')
            if severity == "Critical":
                st.error(f"⚠️ Severity: {severity}")
            elif severity == "High":
                st.warning(f"⚠️ Severity: {severity}")
            else:
                st.info(f"ℹ️ Severity: {severity}")
            
            # Show issues
            issues = result.get('diagnosis_report', {}).get('issues', [])
            if issues:
                st.markdown("**Issues Found:**")
                for issue in issues:
                    st.markdown(f"- {issue}")
            
            # Show MQIM notification
            mqim = result.get('mqim_notification', {})
            if mqim:
                with st.expander("Manufacturing Quality Alert", expanded=True):
                    st.markdown(f"**Manufacturer:** {mqim.get('manufacturer', 'N/A')}")
                    st.markdown(f"**Part Type:** {mqim.get('part_type', 'N/A')}")
                    st.markdown(f"**Recall Risk:** {mqim.get('recall_risk', 'N/A')}")
                    st.markdown(f"**Similar Failures:** {mqim.get('similar_failures', 0)}")

# --- FLEET DASHBOARD TAB ---
def render_fleet_dashboard(user):
    st.markdown('<h2 style="font-size: 48px; font-weight: 600; color: #2C3E50; margin-bottom: 36px;">Fleet Overview</h2>', unsafe_allow_html=True)
    
    # Load data
    vehicles = load_data(DB_PATH)
    df = pd.DataFrame(vehicles)
    
    # Calculate metrics BEFORE renaming columns
    total = len(df)
    critical = len(df[df['status'] == 'Critical']) if 'status' in df.columns else 0
    high_risk = len(df[df['status'] == 'High']) if 'status' in df.columns else 0
    at_risk = len(df[df['status'] == 'Medium']) if 'status' in df.columns else 0
    healthy = len(df[df['status'] == 'Normal']) if 'status' in df.columns else 0
    
    # Display metrics in cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = {
        "Total": total,
        "Critical": critical,
        "High Risk": high_risk,
        "At Risk": at_risk,
        "Healthy": healthy
    }
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 21px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.75px;">TOTAL FLEET</div>
                    <div style="font-size: 72px; font-weight: 600; color: #2C3E50; margin-bottom: 12px; line-height: 1;">{metrics["Total"]}</div>
                    <div style="color: #4CAF50; font-size: 24px; font-weight: 500;">Active</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                <div style="color: #95A5A6; font-size: 21px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.75px;">CRITICAL</div>
                <div style="font-size: 72px; font-weight: 600; color: #E74C3C; margin-bottom: 12px; line-height: 1;">{metrics["Critical"]}</div>
                <div style="color: #E74C3C; font-size: 24px; font-weight: 500;">Immediate Action</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                <div style="color: #95A5A6; font-size: 21px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.75px;">HIGH RISK</div>
                <div style="font-size: 72px; font-weight: 600; color: #FF9F43; margin-bottom: 12px; line-height: 1;">{metrics["High Risk"]}</div>
                <div style="color: #FF9F43; font-size: 24px; font-weight: 500;">Service Soon</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                <div style="color: #95A5A6; font-size: 21px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.75px;">AT RISK</div>
                <div style="font-size: 72px; font-weight: 600; color: #F39C12; margin-bottom: 12px; line-height: 1;">{metrics["At Risk"]}</div>
                <div style="color: #F39C12; font-size: 24px; font-weight: 500;">Monitor Closely</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                <div style="color: #95A5A6; font-size: 21px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.75px;">HEALTHY</div>
                <div style="font-size: 72px; font-weight: 600; color: #27AE60; margin-bottom: 12px; line-height: 1;">{metrics["Healthy"]}</div>
                <div style="color: #27AE60; font-size: 24px; font-weight: 500;">Optimal Status</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Prepare dataframe for display
    df_display = df.rename(columns={
        'vehicle_id': 'ID',
        'owner': 'Owner',
        'make': 'Make',
        'model': 'Model',
        'status': 'Status',
        'current_issue': 'Issue',
        'confidence': 'Confidence'
    })
    
    df_display = df_display[['ID', 'Owner', 'Make', 'Model', 'Status', 'Issue', 'Confidence']]
    
    # Filters with session state management
    if 'filter_status' not in st.session_state:
        st.session_state.filter_status = ["Critical", "High", "Medium", "Low", "Normal"]
    
    # Filter section with better spacing - aligned layout
    label_col, filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, search_col = st.columns([1.5, 1, 1, 1, 1, 1, 3])
    
    with label_col:
        st.markdown('<p style="color: #2C3E50; font-size: 14px; font-weight: 500; margin-bottom: 8px; margin-top: 8px;">Filter by Status:</p>', unsafe_allow_html=True)
    
    statuses = ["Critical", "High", "Medium", "Low", "Normal"]
    filter_cols = [filter_col1, filter_col2, filter_col3, filter_col4, filter_col5]
    temp_filters = []
    
    for idx, status in enumerate(statuses):
        with filter_cols[idx]:
            if st.checkbox(status, value=status in st.session_state.filter_status, key=f"filter_{status}"):
                temp_filters.append(status)
    
    st.session_state.filter_status = temp_filters if temp_filters else st.session_state.filter_status
    filter_status = st.session_state.filter_status
    
    with search_col:
        st.markdown('<p style="color: #2C3E50; font-size: 14px; font-weight: 500; margin-bottom: 8px;">Search by Vehicle ID:</p>', unsafe_allow_html=True)
        search_id = st.text_input("Search Vehicle ID:", placeholder="e.g., V-005", label_visibility="collapsed")
    
    # Blue checkboxes
    st.markdown("""
    <style>
        /* Checkbox styling */
        div[data-testid="stCheckbox"] {
            background-color: transparent !important;
            padding: 4px 0px;
        }
        
        div[data-testid="stCheckbox"] label {
            color: #2C3E50 !important;
            font-weight: 400;
            font-size: 14px;
        }
        
        /* Blue checkmark */
        div[data-testid="stCheckbox"] input[type="checkbox"] {
            accent-color: #4A5F8C !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = df_display[df_display["Status"].isin(filter_status)]
    if search_id:
        filtered_df = filtered_df[filtered_df["ID"].str.contains(search_id, case=False)]
    
    # Fleet table section - Template style with full width
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); width: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="margin: 0; font-size: 30px; font-weight: 600; color: #2C3E50;">Live Fleet Status</h3>
            <div style="color: #95A5A6; font-size: 20px;">Updated: Real-time</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display with custom styling - WHITE/LIGHT THEME with BLACK TEXT
    st.markdown("""
    <style>
        /* Dataframe container */
        div[data-testid="stDataFrame"] {
            background-color: white !important;
        }
        
        /* Force BLACK text on ALL dataframe elements */
        div[data-testid="stDataFrame"] * {
            color: #000000 !important;
        }
        
        /* Table headers */
        table thead, table thead * {
            color: #000000 !important;
            background-color: #F8F9FA !important;
        }
        
        .vehicle-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
            background-color: white !important;
        }
        .vehicle-table thead th {
            background-color: #F8F9FA !important;
            color: #000000 !important;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            padding: 12px;
            text-align: left;
            border: none;
            border-bottom: 2px solid #E0E6ED !important;
        }
        .vehicle-table tbody tr {
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .vehicle-table tbody td {
            padding: 12px;
            border: none;
            color: #000000 !important;
            font-size: 14px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create custom HTML table instead of st.dataframe for full control
    table_html = '<div style="overflow-x: auto; max-height: 400px; overflow-y: auto; border-radius: 8px; border: 1px solid #E0E6ED;">'
    table_html += '<table style="width: 100%; border-collapse: collapse; background-color: white;">'
    
    # Table header
    table_html += '<thead style="position: sticky; top: 0; z-index: 10; background-color: #F8F9FA;">'
    table_html += '<tr>'
    for col in filtered_df.columns:
        table_html += f'<th style="padding: 18px; text-align: left; font-size: 12px; font-weight: 600; color: #000000; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #E0E6ED; background-color: #F8F9FA;">{col}</th>'
    table_html += '</tr>'
    table_html += '</thead>'
    
    # Table body
    table_html += '<tbody>'
    for idx, row in filtered_df.iterrows():
        # Determine row background color based on status (blue shades)
        status_value = str(row['Status'])
        row_bg_colors = {
            'Critical': '#DBEAFE',     # Light blue
            'High': '#BFDBFE',         # Medium blue
            'Medium': '#E0F2FE',       # Lighter blue
            'Low': '#EFF6FF',          # Very light blue
            'Normal': '#F0F9FF'        # Palest blue
        }
        row_bg = row_bg_colors.get(status_value, '#FFFFFF')
        
        table_html += f'<tr style="border-bottom: 1px solid #E8EDF5; background-color: {row_bg};" onmouseover="this.style.backgroundColor=\'#C7D2FE\'" onmouseout="this.style.backgroundColor=\'{row_bg}\'">'
        for col in filtered_df.columns:
            value = str(row[col])
            
            # Add status badge styling with blue shades
            if col == 'Status':
                badge_colors = {
                    'Critical': 'background-color: #3B82F6; color: #FFFFFF;',
                    'High': 'background-color: #60A5FA; color: #FFFFFF;',
                    'Medium': 'background-color: #93C5FD; color: #1E3A8A;',
                    'Low': 'background-color: #BFDBFE; color: #1E40AF;',
                    'Normal': 'background-color: #DBEAFE; color: #1E40AF;'
                }
                badge_style = badge_colors.get(value, '')
                cell_content = f'<span style="{badge_style} padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block;">{value}</span>'
            else:
                cell_content = value
            
            table_html += f'<td style="padding: 18px; font-size: 16px; color: #000000; background-color: transparent;">{cell_content}</td>'
        table_html += '</tr>'
    table_html += '</tbody>'
    table_html += '</table>'
    table_html += '</div>'
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons section - Template style with full width
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); width: 100%;">
        <h3 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #2C3E50;">Diagnostic Actions</h3>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        v_ids = filtered_df['ID'].tolist()
        if v_ids:
            default_idx = v_ids.index("V-005") if "V-005" in v_ids else 0
            st.markdown('<p style="color: #2C3E50; font-size: 14px; font-weight: 500; margin-bottom: 8px;">Select Vehicle for Analysis:</p>', unsafe_allow_html=True)
            selected_id = st.selectbox("Select Vehicle for Analysis:", v_ids, index=default_idx, label_visibility="collapsed")
        else:
            st.warning("No vehicles match the current filters")
            selected_id = None
    
    with col_b:
        st.markdown('<p style="color: transparent; font-size: 14px; margin-bottom: 8px;">.</p>', unsafe_allow_html=True)
        if selected_id and st.button("🔧 Run Diagnostic & Connect with Customer", type="primary", use_container_width=True):
            # Run diagnostic in background
            run_full_diagnostic(selected_id, user)
            # Switch to Customer Chat tab (for V-005 prototype demo)
            if selected_id == "V-005":
                st.session_state.active_page = 'chat'
                st.success("✅ Critical alert detected! Connecting with customer Arjun Mehta...")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- MQIM DASHBOARD TAB ---
def render_mqim_dashboard(user):
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import random
    
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="font-size: 26px; font-weight: 600; color: #2C3E50; margin: 0 0 8px 0;">
            Manufacturing Quality Insights
        </h2>
        <p style="color: #95A5A6; margin: 0; font-size: 15px;">Track part failures, identify patterns, and manage manufacturer notifications</p>
    </div>
    """, unsafe_allow_html=True)
    
    mqim = get_mqim()
    
    # Get summary stats
    total_failures = mqim.get_total_failures()
    failures_by_mfr = mqim.get_failures_by_manufacturer()
    recall_candidates = mqim.get_recall_candidates()
    
    # Calculate critical failures
    total_critical = sum(1 for f in mqim.failures if f.severity in ['Critical', 'High'])
    
    # 1. KPI ROW - Executive Impact Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        warranty_saved = 4500000  # ₹45L
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Warranty Costs Saved</div>
                    <div style="font-size: 32px; font-weight: 600; color: #27AE60; margin-bottom: 4px;">₹{warranty_saved/100000:.1f}L</div>
                    <div style="color: #27AE60; font-size: 12px;">↑ 35% vs last quarter</div>
                </div>
                <div class="metric-icon" style="background: #D5F4E6;">
                    <span style="font-size: 24px;">💰</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        recurring_defects = max(12, total_critical)
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Recurring Defects</div>
                    <div style="font-size: 32px; font-weight: 600; color: #E74C3C; margin-bottom: 4px;">{recurring_defects}</div>
                    <div style="color: #E74C3C; font-size: 12px;">↓ 60% reduction</div>
                </div>
                <div class="metric-icon" style="background: #FADBD8;">
                    <span style="font-size: 24px;">⚠️</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        active_recalls = max(1, len(recall_candidates))
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Active Recalls</div>
                    <div style="font-size: 32px; font-weight: 600; color: #FF9F43; margin-bottom: 4px;">{active_recalls}</div>
                    <div style="color: #FF9F43; font-size: 12px;">Under investigation</div>
                </div>
                <div class="metric-icon" style="background: #FFE8D1;">
                    <span style="font-size: 24px;">🔍</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        predictive_accuracy = 94
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Predictive Accuracy</div>
                    <div style="font-size: 32px; font-weight: 600; color: #4A5F8C; margin-bottom: 4px;">{predictive_accuracy}%</div>
                    <div style="color: #27AE60; font-size: 12px;">↑ ML model performance</div>
                </div>
                <div class="metric-icon" style="background: #D6EAF8;">
                    <span style="font-size: 24px;">🎯</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 2. Before vs After AI - Grouped Bar Chart
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Before vs. After AI Impact</h3>
        """, unsafe_allow_html=True)
        
        components = ['Brake Pad', 'Fuel Pump', 'Battery']
        reactive_before = [25, 18, 12]
        predictive_after = [10, 15, 9]
        
        fig_grouped = go.Figure()
        
        fig_grouped.add_trace(go.Bar(
            name='Reactive (Before)',
            x=components,
            y=reactive_before,
            marker_color='#7B8FAD',
            text=reactive_before,
            textposition='outside'
        ))
        
        fig_grouped.add_trace(go.Bar(
            name='Predictive (After)',
            x=components,
            y=predictive_after,
            marker_color='#4A5F8C',
            text=predictive_after,
            textposition='outside'
        ))
        
        fig_grouped.update_layout(
            barmode='group',
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=False,
                title=dict(text='Component', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Defect Count', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_grouped, use_container_width=True, key="before_after")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 5. Donut Chart - Failure Mode Classification
    with chart_col2:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Failure Mode Classification</h3>
        """, unsafe_allow_html=True)
        
        failure_modes = ['Friction Wear', 'Warping', 'Cracking', 'Sensor Drift']
        failure_values = [65, 20, 10, 5]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=failure_modes,
            values=failure_values,
            hole=0.5,
            marker=dict(colors=['#4A5F8C', '#7B8FAD', '#A3B8D9', '#C5D5EA']),
            textinfo='label+percent',
            textfont=dict(size=11, color='#2C3E50')
        )])
        
        fig_donut.update_layout(
            showlegend=True,
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#000000', size=11)),
            annotations=[dict(text='Brake<br>Failures', x=0.5, y=0.5, font_size=14, showarrow=False, font_color='#000000')]
        )
        
        st.plotly_chart(fig_donut, use_container_width=True, key="failure_modes")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 3. Pareto Chart - Root Cause Analysis
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Pareto Analysis - Root Causes</h3>
        """, unsafe_allow_html=True)
        
        failure_codes = ['P012<br>Brake Wear', 'B104<br>Battery', 'E201<br>Engine', 'T505<br>Tire', 'F308<br>Fuel']
        frequencies = [45, 28, 18, 12, 7]
        
        # Calculate cumulative percentage
        total = sum(frequencies)
        cumulative = []
        cum_sum = 0
        for freq in frequencies:
            cum_sum += freq
            cumulative.append((cum_sum / total) * 100)
        
        fig_pareto = go.Figure()
        
        # Add bars
        fig_pareto.add_trace(go.Bar(
            x=failure_codes,
            y=frequencies,
            name='Frequency',
            marker_color='#4A5F8C',
            yaxis='y',
            text=frequencies,
            textposition='outside'
        ))
        
        # Add cumulative line
        fig_pareto.add_trace(go.Scatter(
            x=failure_codes,
            y=cumulative,
            name='Cumulative %',
            marker_color='#FF9F43',
            yaxis='y2',
            mode='lines+markers',
            line=dict(width=2)
        ))
        
        fig_pareto.update_layout(
            height=280,
            margin=dict(l=40, r=40, t=20, b=60),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(color='#000000', size=10)
            ),
            yaxis=dict(
                title=dict(text='Frequency', font=dict(color='#000000', size=12)),
                showgrid=True,
                gridcolor='#E8EDF5',
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis2=dict(
                title=dict(text='Cumulative %', font=dict(color='#000000', size=12)),
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, 100],
                tickfont=dict(color='#000000', size=11)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True, key="pareto")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Supplier Quality Heatmap
    with chart_col4:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Supplier Quality Heatmap</h3>
        """, unsafe_allow_html=True)
        
        suppliers = ['Apex Dynamics', 'Volt Systems', 'AutoParts Inc', 'PrimeMfg']
        batches = ['#901', '#902', '#903', '#904', '#905']
        
        # Defect rates (higher = worse, highlight Apex #904)
        defect_matrix = [
            [2, 3, 2, 15, 3],  # Apex Dynamics - #904 is the hotspot
            [4, 3, 5, 4, 3],   # Volt Systems
            [3, 2, 3, 2, 4],   # AutoParts Inc
            [2, 3, 2, 3, 2]    # PrimeMfg
        ]
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=defect_matrix,
            x=batches,
            y=suppliers,
            colorscale=[
                [0, '#E8F0F8'],      # Light blue (low defects)
                [0.3, '#4A5F8C'],    # Medium blue
                [0.7, '#FF9F43'],    # Orange
                [1, '#E74C3C']       # Red (high defects)
            ],
            text=defect_matrix,
            texttemplate='%{text}%',
            textfont={"size": 12, "color": "white"},
            colorbar=dict(
                title=dict(text="Defect<br>Rate %", font=dict(color='#000000', size=11)),
                tickfont=dict(color='#000000', size=10)
            )
        ))
        
        fig_heatmap.update_layout(
            height=280,
            margin=dict(l=100, r=40, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                title=dict(text='Batch Number', font=dict(color='#000000', size=12)),
                side='bottom',
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                title=dict(text='Supplier', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            )
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 6. Stacked Area Chart - Warranty Cost Timeline
    chart_col5, chart_col6 = st.columns(2)
    
    with chart_col5:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Warranty Cost Trend</h3>
        """, unsafe_allow_html=True)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        labor_cost = [150000, 140000, 130000, 115000, 100000, 90000]
        parts_cost = [200000, 190000, 175000, 160000, 140000, 120000]
        logistics_cost = [50000, 48000, 45000, 42000, 38000, 35000]
        
        fig_area = go.Figure()
        
        fig_area.add_trace(go.Scatter(
            x=months, y=labor_cost,
            mode='lines',
            name='Labor Cost',
            fill='tonexty',
            line=dict(width=0.5, color='#4A5F8C'),
            fillcolor='rgba(74, 95, 140, 0.6)',
            stackgroup='one'
        ))
        
        fig_area.add_trace(go.Scatter(
            x=months, y=parts_cost,
            mode='lines',
            name='Parts Replacement',
            fill='tonexty',
            line=dict(width=0.5, color='#7B8FAD'),
            fillcolor='rgba(123, 143, 173, 0.6)',
            stackgroup='one'
        ))
        
        fig_area.add_trace(go.Scatter(
            x=months, y=logistics_cost,
            mode='lines',
            name='Logistics',
            fill='tonexty',
            line=dict(width=0.5, color='#A3B8D9'),
            fillcolor='rgba(163, 184, 217, 0.6)',
            stackgroup='one'
        ))
        
        fig_area.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Cost (₹)', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(color='#000000', size=11)),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_area, use_container_width=True, key="warranty_trend")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 7. Scatter Plot - Predictive Confidence vs Actual Wear
    with chart_col6:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">AI Confidence vs. Actual Wear</h3>
        """, unsafe_allow_html=True)
        
        actual_wear = [2.1, 2.5, 3.2, 3.8, 4.5, 5.1, 5.8, 6.2, 7.0, 7.5, 8.2, 9.0]
        ai_confidence = [0.99, 0.97, 0.92, 0.89, 0.85, 0.81, 0.78, 0.75, 0.70, 0.68, 0.65, 0.62]
        severity = ['Critical']*4 + ['High']*4 + ['Medium']*4
        
        color_map = {'Critical': '#E74C3C', 'High': '#FF9F43', 'Medium': '#4A5F8C'}
        
        fig_scatter = go.Figure()
        
        for sev in ['Critical', 'High', 'Medium']:
            indices = [i for i, s in enumerate(severity) if s == sev]
            fig_scatter.add_trace(go.Scatter(
                x=[actual_wear[i] for i in indices],
                y=[ai_confidence[i] for i in indices],
                mode='markers',
                name=sev,
                marker=dict(size=12, color=color_map[sev], line=dict(width=2, color='white')),
                hovertemplate='<b>%{text}</b><br>Wear: %{x:.1f}mm<br>Confidence: %{y:.0%}<extra></extra>',
                text=[f'{sev} Case' for _ in indices]
            ))
        
        fig_scatter.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Actual Wear (mm)', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='AI Confidence', font=dict(color='#000000', size=12)),
                tickformat='.0%',
                tickfont=dict(color='#000000', size=11)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True, key="confidence_scatter")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 8. Horizontal Bar Chart - Recommended Design Actions
    st.markdown("""
    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Recommended Design Actions</h3>
    """, unsafe_allow_html=True)
    
    actions = [
        'Recall Batch #904',
        'Update Firmware v2.1',
        'Switch Friction Material',
        'Redesign Brake Pad Geometry',
        'Enhanced Testing Protocol'
    ]
    priority_scores = [95, 88, 82, 75, 68]
    
    fig_actions = go.Figure(go.Bar(
        x=priority_scores,
        y=actions,
        orientation='h',
        marker=dict(
            color=priority_scores,
            colorscale=[
                [0, '#A3B8D9'],
                [0.5, '#7B8FAD'],
                [1, '#4A5F8C']
            ],
            showscale=False
        ),
        text=priority_scores,
        textposition='outside',
        texttemplate='%{text}'
    ))
    
    fig_actions.update_layout(
        height=300,
        margin=dict(l=180, r=40, t=20, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='#E8EDF5',
            title=dict(text='Priority Score', font=dict(color='#000000', size=12)),
            range=[0, 105],
            tickfont=dict(color='#000000', size=11)
        ),
        yaxis=dict(
            showgrid=False,
            title=dict(text='Action Item', font=dict(color='#000000', size=12)),
            tickfont=dict(color='#000000', size=11)
        )
    )
    
    st.plotly_chart(fig_actions, use_container_width=True, key="actions")
    st.markdown('</div>', unsafe_allow_html=True)

# --- UEBA DASHBOARD TAB ---
def render_ueba_dashboard(user):
    import plotly.graph_objects as go
    import math
    from datetime import datetime, timedelta
    import random
    
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="font-size: 26px; font-weight: 600; color: #2C3E50; margin: 0 0 8px 0;">
            User & Entity Behavior Analytics (UEBA)
        </h2>
        <p style="color: #95A5A6; margin: 0; font-size: 15px;">Real-time, adaptive security monitoring and threat detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize attack simulation state
    if 'attack_simulated' not in st.session_state:
        st.session_state.attack_simulated = False
    
    ueba = get_ueba()
    threat_summary = ueba.get_threat_summary()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI Metrics
    threat_count = max(threat_summary['total_active_threats'], 3 if st.session_state.attack_simulated else 0)
    critical_count = max(threat_summary['by_severity'].get('Critical', 0), 1 if st.session_state.attack_simulated else 0)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Active Threats</div>
                    <div style="font-size: 32px; font-weight: 600; color: {'#E74C3C' if st.session_state.attack_simulated else '#4A5F8C'}; margin-bottom: 4px;">{threat_count}</div>
                    <div style="color: #95A5A6; font-size: 12px;">{'⚠️ Attack in progress' if st.session_state.attack_simulated else 'Being monitored'}</div>
                </div>
                <div class="metric-icon" style="background: {'#FADBD8' if st.session_state.attack_simulated else '#D6EAF8'};">
                    <span style="font-size: 24px;">👁️</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Critical Alerts</div>
                    <div style="font-size: 32px; font-weight: 600; color: #E74C3C; margin-bottom: 4px;">{critical_count}</div>
                    <div style="color: #E74C3C; font-size: 12px;">Immediate response</div>
                </div>
                <div class="metric-icon" style="background: #FADBD8;">
                    <span style="font-size: 24px;">🔴</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        anomaly_score = 0.92 if st.session_state.attack_simulated else 0.15
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Anomaly Score</div>
                    <div style="font-size: 32px; font-weight: 600; color: {'#E74C3C' if anomaly_score > 0.8 else '#4A5F8C'}; margin-bottom: 4px;">{anomaly_score:.2f}</div>
                    <div style="color: {'#E74C3C' if anomaly_score > 0.8 else '#27AE60'}; font-size: 12px;">{'Above threshold!' if anomaly_score > 0.8 else 'Normal range'}</div>
                </div>
                <div class="metric-icon" style="background: {'#FADBD8' if anomaly_score > 0.8 else '#D6EAF8'};">
                    <span style="font-size: 24px;">📊</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Blocked Users</div>
                    <div style="font-size: 32px; font-weight: 600; color: #FF9F43; margin-bottom: 4px;">{threat_summary['blocked_users']}</div>
                    <div style="color: #FF9F43; font-size: 12px;">Access denied</div>
                </div>
                <div class="metric-icon" style="background: #FFE8D1;">
                    <span style="font-size: 24px;">🚫</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 1. Hero Chart - Threat Score Timeline
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Threat Score Timeline</h3>
        """, unsafe_allow_html=True)
        
        # Generate time series with spike if attack simulated
        time_points = list(range(60))
        if st.session_state.attack_simulated:
            anomaly_scores = [random.uniform(0.1, 0.3) for _ in range(45)] + [random.uniform(0.85, 0.95) for _ in range(15)]
        else:
            anomaly_scores = [random.uniform(0.1, 0.35) for _ in range(60)]
        
        fig_timeline = go.Figure()
        
        # Add anomaly score line
        fig_timeline.add_trace(go.Scatter(
            x=time_points,
            y=anomaly_scores,
            mode='lines',
            name='Anomaly Score',
            line=dict(color='#4A5F8C', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 95, 140, 0.2)'
        ))
        
        # Add critical threshold line
        fig_timeline.add_hline(
            y=0.8,
            line_dash="dash",
            line_color="#E74C3C",
            line_width=2,
            annotation_text="Critical Threshold (0.80)",
            annotation_position="right"
        )
        
        fig_timeline.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Time (10s intervals)', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Anomaly Score', font=dict(color='#000000', size=12)),
                range=[0, 1.05],
                tickfont=dict(color='#000000', size=11)
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True, key="threat_timeline")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. Behavior Radar - Baseline vs Anomaly
    with chart_col2:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Behavioral Baseline vs. Current</h3>
        """, unsafe_allow_html=True)
        
        categories = ['API Calls', 'Data Volume', 'Login Freq', 'Error Rate', 'After Hours']
        
        if st.session_state.attack_simulated:
            current_session = [85, 95, 75, 80, 90]  # Spiky/Large
        else:
            current_session = [45, 40, 50, 35, 30]
        
        baseline = [40, 35, 45, 30, 25]
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=baseline + [baseline[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='Historical Average',
            line_color='#4A5F8C',
            fillcolor='rgba(74, 95, 140, 0.3)'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=current_session + [current_session[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='Current Session',
            line_color='#E74C3C' if st.session_state.attack_simulated else '#7B8FAD',
            fillcolor=f'rgba(231, 76, 60, 0.3)' if st.session_state.attack_simulated else 'rgba(123, 143, 173, 0.3)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor='#E8EDF5',
                    tickfont=dict(color='#000000', size=11)
                ),
                angularaxis=dict(
                    tickfont=dict(color='#000000', size=11)
                ),
                bgcolor='white'
            ),
            showlegend=True,
            height=280,
            margin=dict(l=60, r=60, t=20, b=20),
            paper_bgcolor='white',
            font=dict(color='#000000', size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_radar, use_container_width=True, key="behavior_radar")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Continue with more charts...
    # 3 & 4: Geo Map and Live Logs
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Login Locations (Geo-Map)</h3>
        """, unsafe_allow_html=True)
        
        # Simple world map scatter
        locations = [
            {'city': 'Pune (HQ)', 'lat': 18.5204, 'lon': 73.8567, 'type': 'Normal'},
            {'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'type': 'Normal'},
        ]
        
        if st.session_state.attack_simulated:
            locations.append({'city': 'Unknown IP (Russia)', 'lat': 55.7558, 'lon': 37.6173, 'type': 'Suspicious'})
        
        fig_map = go.Figure()
        
        for loc in locations:
            color = '#E74C3C' if loc['type'] == 'Suspicious' else '#4A5F8C'
            size = 15 if loc['type'] == 'Suspicious' else 10
            
            fig_map.add_trace(go.Scattergeo(
                lon=[loc['lon']],
                lat=[loc['lat']],
                text=[loc['city']],
                mode='markers+text',
                marker=dict(size=size, color=color, line=dict(width=2, color='white')),
                textposition="top center",
                name=loc['city'],
                showlegend=False
            ))
        
        fig_map.update_layout(
            height=280,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='white',
            font=dict(color='#000000', size=10),
            geo=dict(
                showland=True,
                landcolor='#E8F0F8',
                showcountries=True,
                countrycolor='#C5D5EA',
                showlakes=True,
                lakecolor='white',
                projection_type='natural earth',
                bgcolor='white'
            )
        )
        
        st.plotly_chart(fig_map, use_container_width=True, key="geo_map")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Live Log Terminal
    with chart_col4:
        st.markdown("""
        <div style="background: #1E293B; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #E8F0F8;">Live System Logs</h3>
        """, unsafe_allow_html=True)
        
        logs = [
            "[14:02:10] [INFO] User 'Alice' login successful",
            "[14:02:15] [INFO] API request: GET /vehicles/list",
            "[14:02:18] [INFO] Data access: Vehicle records (10 items)"
        ]
        
        if st.session_state.attack_simulated:
            logs.extend([
                "[14:02:22] [WARN] User 'Demo_User' BULK_EXPORT attempted",
                "[14:02:23] [CRITICAL] Anomaly detected: 5000 records requested",
                "[14:02:23] [ALERT] BLOCKED by UEBA - Threshold exceeded",
                "[14:02:24] [WARN] Multiple failed auth attempts detected",
                "[14:02:25] [CRITICAL] Insider threat protocol activated"
            ])
        else:
            logs.extend([
                "[14:02:22] [INFO] Scheduled backup completed",
                "[14:02:30] [INFO] System health check: OK"
            ])
        
        logs_html = '<div style="background: #0F172A; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 11px; height: 200px; overflow-y: auto;">'
        for log in logs[-8:]:
            if 'CRITICAL' in log or 'ALERT' in log:
                color = '#EF4444'
            elif 'WARN' in log:
                color = '#F59E0B'
            else:
                color = '#10B981'
            logs_html += f'<div style="color: {color}; margin-bottom: 4px;">{log}</div>'
        logs_html += '</div>'
        
        st.markdown(logs_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 5 & 6: Risk Leaderboard and Access Heatmap
    chart_col5, chart_col6 = st.columns(2)
    
    with chart_col5:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">User Risk Leaderboard</h3>
        """, unsafe_allow_html=True)
        
        # Risk leaderboard data
        if st.session_state.attack_simulated:
            risk_data = [
                {'user': 'Demo_User', 'role': 'Admin', 'score': 92, 'status': 'Locked'},
                {'user': 'Alice', 'role': 'Manager', 'score': 15, 'status': 'Active'},
                {'user': 'Bob', 'role': 'Mechanic', 'score': 12, 'status': 'Active'},
                {'user': 'Charlie', 'role': 'Admin', 'score': 8, 'status': 'Active'},
                {'user': 'Eve', 'role': 'External', 'score': 45, 'status': 'Active'}
            ]
        else:
            risk_data = [
                {'user': 'Alice', 'role': 'Manager', 'score': 15, 'status': 'Active'},
                {'user': 'Bob', 'role': 'Mechanic', 'score': 12, 'status': 'Active'},
                {'user': 'Charlie', 'role': 'Admin', 'score': 8, 'status': 'Active'},
                {'user': 'Eve', 'role': 'External', 'score': 25, 'status': 'Active'},
                {'user': 'Frank', 'role': 'Analyst', 'score': 5, 'status': 'Active'}
            ]
        
        # Create table
        table_html = '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
        table_html += '<thead><tr style="border-bottom: 2px solid #E0E6ED;">'
        table_html += '<th style="padding: 10px; text-align: left; color: #000000;">User</th>'
        table_html += '<th style="padding: 10px; text-align: left; color: #000000;">Role</th>'
        table_html += '<th style="padding: 10px; text-align: left; color: #000000;">Risk</th>'
        table_html += '<th style="padding: 10px; text-align: center; color: #000000;">Status</th>'
        table_html += '</tr></thead><tbody>'
        
        for user in risk_data:
            risk_color = '#E74C3C' if user['score'] > 70 else '#FF9F43' if user['score'] > 40 else '#4A5F8C'
            status_color = '#E74C3C' if user['status'] == 'Locked' else '#27AE60'
            
            table_html += '<tr style="border-bottom: 1px solid #E8EDF5;">'
            table_html += f'<td style="padding: 10px; color: #000000; font-weight: 500;">{user["user"]}</td>'
            table_html += f'<td style="padding: 10px; color: #000000;">{user["role"]}</td>'
            table_html += f'<td style="padding: 10px;"><div style="background: #E8F0F8; border-radius: 4px; height: 8px; width: 100px; position: relative;"><div style="background: {risk_color}; height: 100%; width: {user["score"]}%; border-radius: 4px;"></div></div><span style="color: {risk_color}; font-size: 11px; font-weight: 600; margin-left: 4px;">{user["score"]}/100</span></td>'
            table_html += f'<td style="padding: 10px; text-align: center;"><span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600;">{user["status"]}</span></td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        
        st.markdown(table_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 6. Access Pattern Heatmap
    with chart_col6:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Access Pattern Heatmap</h3>
        """, unsafe_allow_html=True)
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        hours = ['00', '04', '08', '12', '16', '20']
        
        # Generate activity data (normal 9-5 pattern + suspicious 3AM spike if attacked)
        activity_matrix = []
        for day_idx in range(7):
            day_data = []
            for hour_idx in range(6):
                hour = int(hours[hour_idx])
                # Normal activity during business hours (8-16)
                if 8 <= hour <= 16 and day_idx < 5:  # Weekdays
                    activity = random.randint(15, 30)
                elif st.session_state.attack_simulated and day_idx == 5 and hour == 0:  # Saturday 3AM
                    activity = 45  # Suspicious hotspot
                else:
                    activity = random.randint(1, 5)
                day_data.append(activity)
            activity_matrix.append(day_data)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=activity_matrix,
            x=hours,
            y=days,
            colorscale=[
                [0, '#E8F0F8'],
                [0.3, '#4A5F8C'],
                [0.7, '#FF9F43'],
                [1, '#E74C3C']
            ],
            text=activity_matrix,
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(
                title=dict(text="Activity", font=dict(color='#000000', size=11)),
                tickfont=dict(color='#000000', size=10)
            )
        ))
        
        fig_heatmap.update_layout(
            height=280,
            margin=dict(l=60, r=40, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                title=dict(text='Hour of Day', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                title=dict(text='Day', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            )
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True, key="access_heatmap")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 7 & 8: Auth Trends and Threat Types
    chart_col7, chart_col8 = st.columns(2)
    
    # 7. Authentication Flow - Success vs Failure
    with chart_col7:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Authentication Trends</h3>
        """, unsafe_allow_html=True)
        
        time_labels = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00']
        
        if st.session_state.attack_simulated:
            successful_auth = [25, 28, 30, 27, 15, 8]
            failed_auth = [2, 3, 2, 5, 25, 40]  # Brute force spike
        else:
            successful_auth = [25, 28, 30, 27, 29, 26]
            failed_auth = [2, 3, 2, 3, 2, 3]
        
        fig_auth = go.Figure()
        
        fig_auth.add_trace(go.Bar(
            x=time_labels,
            y=successful_auth,
            name='Successful',
            marker_color='#4A5F8C',
            text=successful_auth,
            textposition='inside'
        ))
        
        fig_auth.add_trace(go.Bar(
            x=time_labels,
            y=failed_auth,
            name='Failed',
            marker_color='#E74C3C',
            text=failed_auth,
            textposition='inside'
        ))
        
        fig_auth.update_layout(
            barmode='stack',
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                showgrid=False,
                title=dict(text='Time', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Auth Attempts', font=dict(color='#000000', size=12)),
                tickfont=dict(color='#000000', size=11)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_auth, use_container_width=True, key="auth_trends")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 8. Threat Category Breakdown
    with chart_col8:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Threat Type Distribution</h3>
        """, unsafe_allow_html=True)
        
        if st.session_state.attack_simulated:
            threat_categories = ['Data Exfiltration', 'Privilege Escalation', 'Unusual Location', 'Brute Force']
            threat_values = [40, 30, 20, 10]
        else:
            threat_categories = ['Unusual Location', 'After Hours', 'Failed Auth', 'Minor']
            threat_values = [40, 30, 20, 10]
        
        fig_threats = go.Figure(data=[go.Pie(
            labels=threat_categories,
            values=threat_values,
            hole=0.5,
            marker=dict(colors=['#E74C3C', '#FF9F43', '#4A5F8C', '#7B8FAD']),
            textinfo='label+percent',
            textfont=dict(size=11, color='#2C3E50')
        )])
        
        fig_threats.update_layout(
            showlegend=True,
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#000000', size=11)),
            annotations=[dict(text='Threats<br>Active', x=0.5, y=0.5, font_size=14, showarrow=False, font_color='#000000')]
        )
        
        st.plotly_chart(fig_threats, use_container_width=True, key="threat_types")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Active threats
    active_threats = ueba.get_active_threats()
    
    if active_threats:
        st.markdown("""
        <div style="background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); width: 100%;">
            <h3 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #2C3E50;">Active Security Threats</h3>
        """, unsafe_allow_html=True)
        
        df_threats = pd.DataFrame([
            {
                "User ID": t.user_id,
                "Threat Type": t.threat_type,
                "Severity": t.severity,
                "Details": t.details,
                "Timestamp": t.timestamp
            }
            for t in active_threats
        ])
        st.dataframe(df_threats, use_container_width=True, hide_index=True)
        
        st.markdown('<br>', unsafe_allow_html=True)
        
        # Threat actions
        st.markdown("""
        <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin: 20px 0 10px 0;">
            Threat Management
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            user_to_block = st.text_input("User ID to block:", key="block_user")
            if st.button("Block User", type="primary"):
                if user_to_block:
                    ueba.block_user(user_to_block)
                    st.success(f"✅ User {user_to_block} has been blocked")
                    st.rerun()
        
        with col2:
            threat_to_resolve = st.number_input("Threat ID to resolve:", min_value=1, step=1, key="resolve_threat")
            if st.button("Resolve Threat", type="secondary"):
                ueba.resolve_threat(threat_to_resolve)
                st.success(f"✅ Threat #{threat_to_resolve} marked as resolved")
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("✅ No active security threats detected")
    
    # User activity monitoring
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); width: 100%;">
        <div style="font-size: 18px; font-weight: 600; color: #1F2937; margin-bottom: 15px;">
            User Activity Monitoring
        </div>
    """, unsafe_allow_html=True)
    
    user_to_monitor = st.selectbox("Select user to monitor:", [u['user_id'] for u in USERS_DB])
    
    if user_to_monitor:
        # Define unique data for each user
        user_mock_data = {
            'U001': {'actions': 245, 'status': 'ACTIVE', 'status_color': '#27AE60', 'role': 'Fleet Manager'},
            'U002': {'actions': 182, 'status': 'ACTIVE', 'status_color': '#27AE60', 'role': 'Mechanic'},
            'U003': {'actions': 318, 'status': 'ACTIVE', 'status_color': '#27AE60', 'role': 'Admin'},
            'U004': {'actions': 47, 'status': 'ACTIVE', 'status_color': '#27AE60', 'role': 'External'},
        }
        
        # Get data for selected user (default to U001 if not found)
        user_data = user_mock_data.get(user_to_monitor, user_mock_data['U001'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="color: #6B7280; font-size: 12px; font-weight: 600;">TOTAL ACTIONS (24H)</div>
                <div style="font-size: 28px; font-weight: 700; color: #1F2937; margin-top: 8px;">{user_data['actions']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="color: #6B7280; font-size: 12px; font-weight: 600;">STATUS</div>
                <div style="font-size: 18px; font-weight: 700; color: {user_data['status_color']}; margin-top: 8px;">{user_data['status']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="color: #6B7280; font-size: 12px; font-weight: 600;">ROLE</div>
                <div style="font-size: 16px; font-weight: 600; color: #1F2937; margin-top: 8px;">{user_data['role']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- ANALYTICS DASHBOARD TAB ---
def render_analytics_dashboard(user):
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime, timedelta
    import random
    import numpy as np
    
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="font-size: 26px; font-weight: 600; color: #2C3E50; margin: 0 0 8px 0;">
            AI-Powered Predictive Command Center
        </h2>
        <p style="color: #95A5A6; margin: 0; font-size: 15px;">Real-time forecasting, cost optimization, and risk prediction</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load fleet data
    vehicles = load_data(DB_PATH)
    
    if not vehicles:
        st.warning("No vehicle data available")
        return
    
    # Initialize analytics
    analytics = FleetAnalytics(vehicles)
    
    # 1. ROI "Hero" Cards with Sparklines
    col1, col2, col3, col4 = st.columns(4)
    
    # Generate sparkline data
    sparkline_savings = [random.uniform(10, 13) for _ in range(10)]
    sparkline_downtime = [random.randint(420, 480) for _ in range(10)]
    sparkline_catch = [random.uniform(91, 95) for _ in range(10)]
    sparkline_util = [random.uniform(96, 99) for _ in range(10)]
    
    with col1:
        # Projected Savings
        fig_spark1 = go.Figure()
        fig_spark1.add_trace(go.Scatter(
            y=sparkline_savings,
            mode='lines',
            line=dict(color='#27AE60', width=2),
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.2)',
            showlegend=False
        ))
        fig_spark1.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div style="color: #95A5A6; font-size: 11px; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">Projected Monthly Savings</div>
                <div style="font-size: 28px; font-weight: 700; color: #27AE60; margin-bottom: 2px;">₹12.5L</div>
                <div style="color: #27AE60; font-size: 11px; font-weight: 600;">↑ 15% vs last month</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_spark1, use_container_width=True, config={'displayModeBar': False}, key="spark1")
    
    with col2:
        # Downtime Avoided
        fig_spark2 = go.Figure()
        fig_spark2.add_trace(go.Scatter(
            y=sparkline_downtime,
            mode='lines',
            line=dict(color='#4A5F8C', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 95, 140, 0.2)',
            showlegend=False
        ))
        fig_spark2.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div style="color: #95A5A6; font-size: 11px; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">Downtime Hours Saved</div>
                <div style="font-size: 28px; font-weight: 700; color: #4A5F8C; margin-bottom: 2px;">450</div>
                <div style="color: #4A5F8C; font-size: 11px; font-weight: 600;">This month</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_spark2, use_container_width=True, config={'displayModeBar': False}, key="spark2")
    
    with col3:
        # Predictive Catch Rate
        fig_spark3 = go.Figure()
        fig_spark3.add_trace(go.Scatter(
            y=sparkline_catch,
            mode='lines',
            line=dict(color='#27AE60', width=2),
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.2)',
            showlegend=False
        ))
        fig_spark3.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div style="color: #95A5A6; font-size: 11px; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">Predictive Catch Rate</div>
                <div style="font-size: 28px; font-weight: 700; color: #27AE60; margin-bottom: 2px;">94%</div>
                <div style="color: #27AE60; font-size: 11px; font-weight: 600;">↑ 8% improvement</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_spark3, use_container_width=True, config={'displayModeBar': False}, key="spark3")
    
    with col4:
        # Fleet Utilization
        fig_spark4 = go.Figure()
        fig_spark4.add_trace(go.Scatter(
            y=sparkline_util,
            mode='lines',
            line=dict(color='#4A5F8C', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 95, 140, 0.2)',
            showlegend=False
        ))
        fig_spark4.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div style="color: #95A5A6; font-size: 11px; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">Fleet Utilization</div>
                <div style="font-size: 28px; font-weight: 700; color: #4A5F8C; margin-bottom: 2px;">98%</div>
                <div style="color: #4A5F8C; font-size: 11px; font-weight: 600;">Operational efficiency</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig_spark4, use_container_width=True, config={'displayModeBar': False}, key="spark4")
    
    
    # 2. Cost Strategy Comparison Chart
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Cost Strategy Comparison</h3>
        """, unsafe_allow_html=True)
        
        strategies = ['Reactive', 'Preventive', 'Predictive<br>(AI)']
        costs = [450000, 280000, 125000]  # in rupees
        colors = ['#E74C3C', '#FF9F43', '#27AE60']
        
        fig_cost = go.Figure()
        
        fig_cost.add_trace(go.Bar(
            x=strategies,
            y=costs,
            marker_color=colors,
            text=['₹4.5L', '₹2.8L', '₹1.25L'],
            textposition='outside',
            textfont=dict(size=14, color='#2C3E50', weight='bold')
        ))
        
        fig_cost.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=60),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=12, color='#2C3E50')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Monthly Cost', font=dict(color='#2C3E50', size=12))
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig_cost, use_container_width=True, key="cost_comparison")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 3. 7-Day Health Forecast - Side by Side Comparison
    with chart_col2:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">7-Day Health Forecast</h3>
        """, unsafe_allow_html=True)
        
        # Create grouped bar chart showing today vs predicted
        categories = ['Healthy', 'Warning', 'Critical']
        today_values = [45, 4, 1]
        predicted_values = [42, 5, 3]  # Shows degradation
        
        fig_forecast = go.Figure()
        
        fig_forecast.add_trace(go.Bar(
            name='Today',
            x=categories,
            y=today_values,
            marker_color='#4A5F8C',
            text=today_values,
            textposition='inside',
            textfont=dict(size=14, color='white', weight='bold')
        ))
        
        fig_forecast.add_trace(go.Bar(
            name='Predicted (+7 Days)',
            x=categories,
            y=predicted_values,
            marker_color='#7B8FAD',
            text=predicted_values,
            textposition='inside',
            textfont=dict(size=14, color='white', weight='bold')
        ))
        
        fig_forecast.update_layout(
            barmode='group',
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=12, color='#2C3E50')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Vehicles', font=dict(color='#2C3E50', size=12))
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_forecast, use_container_width=True, key="health_forecast")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 4. Service Demand Forecast & 5. Failure Probability Distribution
    chart_col3, chart_col4 = st.columns(2)
    
    # 4. Service Demand Forecast
    with chart_col3:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">14-Day Service Demand Forecast</h3>
        """, unsafe_allow_html=True)
        
        days_forecast = list(range(14))
        demand = [random.randint(5, 12) for _ in range(14)]
        demand[4] = 18  # Tuesday spike
        upper_bound = [d + random.randint(2, 4) for d in demand]
        lower_bound = [max(0, d - random.randint(2, 4)) for d in demand]
        
        fig_demand = go.Figure()
        
        # Confidence interval
        fig_demand.add_trace(go.Scatter(
            x=days_forecast + days_forecast[::-1],
            y=upper_bound + lower_bound[::-1],
            fill='toself',
            fillcolor='rgba(74, 95, 140, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False,
            name='Confidence Interval'
        ))
        
        # Forecast line
        fig_demand.add_trace(go.Scatter(
            x=days_forecast,
            y=demand,
            mode='lines+markers',
            line=dict(color='#4A5F8C', width=2),
            marker=dict(size=6, color='#4A5F8C'),
            name='Predicted Demand'
        ))
        
        fig_demand.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Days Ahead', font=dict(color='#2C3E50', size=12))
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Service Bays Needed', font=dict(color='#2C3E50', size=12))
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig_demand, use_container_width=True, key="demand_forecast")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 5. Failure Probability Distribution
    with chart_col4:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Failure Probability Distribution</h3>
        """, unsafe_allow_html=True)
        
        # Create histogram data (most vehicles low risk, few high risk)
        probabilities = []
        for _ in range(40):
            probabilities.append(random.uniform(0, 25))  # Safe vehicles
        for _ in range(8):
            probabilities.append(random.uniform(25, 60))  # Medium risk
        for _ in range(2):
            probabilities.append(random.uniform(75, 95))  # V-005 and one more
        
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Histogram(
            x=probabilities,
            nbinsx=15,
            marker_color='#4A5F8C',
            marker_line_color='white',
            marker_line_width=1
        ))
        
        fig_hist.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                title=dict(text='Failure Probability (%)', font=dict(color='#2C3E50', size=12))
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Number of Vehicles', font=dict(color='#2C3E50', size=12))
            ),
            showlegend=False,
            bargap=0.1
        )
        
        st.plotly_chart(fig_hist, use_container_width=True, key="risk_histogram")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # 6. Component Wear Trends & 7. Downtime Reduction Trend
    chart_col5, chart_col6 = st.columns(2)
    
    # 6. Component Wear Trends
    with chart_col5:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Component Wear Trends (30 Days)</h3>
        """, unsafe_allow_html=True)
        
        days_wear = list(range(30))
        
        # Brake pads degrading (V-005 crossing threshold)
        brake_pads = [10 - (i * 0.25) for i in range(30)]
        battery = [12.8 - (i * 0.02) for i in range(30)]
        oil_quality = [100 - (i * 1.5) for i in range(30)]
        
        fig_wear = go.Figure()
        
        # Brake pads (critical)
        fig_wear.add_trace(go.Scatter(
            x=days_wear,
            y=brake_pads,
            mode='lines',
            name='Brake Pads (mm)',
            line=dict(color='#E74C3C', width=2)
        ))
        
        # Battery health
        fig_wear.add_trace(go.Scatter(
            x=days_wear,
            y=battery,
            mode='lines',
            name='Battery (V)',
            line=dict(color='#4A5F8C', width=2)
        ))
        
        # Oil quality
        fig_wear.add_trace(go.Scatter(
            x=days_wear,
            y=oil_quality,
            mode='lines',
            name='Oil Quality (%)',
            line=dict(color='#27AE60', width=2),
            yaxis='y2'
        ))
        
        # Red threshold for brake pads
        fig_wear.add_hline(
            y=3,
            line_dash="dash",
            line_color="#E74C3C",
            line_width=1,
            annotation_text="Critical (3mm)",
            annotation_position="right"
        )
        
        fig_wear.update_layout(
            height=280,
            margin=dict(l=40, r=50, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Days Ago', font=dict(color='#2C3E50', size=12))
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Brake/Battery', font=dict(color='#2C3E50', size=11))
            ),
            yaxis2=dict(
                overlaying='y',
                side='right',
                showgrid=False,
                title=dict(text='Oil %', font=dict(color='#2C3E50', size=11))
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_wear, use_container_width=True, key="wear_trends")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 7. Downtime Reduction Trend
    with chart_col6:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Downtime Reduction (6 Months)</h3>
        """, unsafe_allow_html=True)
        
        # Downtime declining sharply after AI adoption (60% decrease)
        months_down = ['M-6', 'M-5', 'M-4', 'M-3', 'M-2', 'M-1']
        downtime_hours = [420, 380, 310, 245, 185, 168]  # 60% reduction
        
        fig_downtime = go.Figure()
        
        fig_downtime.add_trace(go.Scatter(
            x=months_down,
            y=downtime_hours,
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.3)',
            line=dict(color='#27AE60', width=3),
            mode='lines+markers',
            marker=dict(size=8, color='#27AE60'),
            name='Unplanned Downtime'
        ))
        
        # Add annotation for 60% reduction
        fig_downtime.add_annotation(
            x=2.5,
            y=350,
            text="60% Reduction<br>with AI",
            showarrow=True,
            arrowhead=2,
            arrowcolor='#27AE60',
            font=dict(size=12, color='#27AE60', weight='bold')
        )
        
        fig_downtime.update_layout(
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                title=dict(text='Month', font=dict(color='#2C3E50', size=12))
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E8EDF5',
                title=dict(text='Hours', font=dict(color='#2C3E50', size=12))
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig_downtime, use_container_width=True, key="downtime_trend")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    
    # 8. "At Risk" Drill-Down Table
    st.markdown("""
    <div style="background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px;">
        <h3 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #2C3E50;">🚨 Priority Risk Table - Action Required</h3>
        <p style="color: #6B7280; margin: 0 0 16px 0; font-size: 14px;">Top 5 vehicles requiring immediate attention, sorted by urgency</p>
    """, unsafe_allow_html=True)
    
    # Create at-risk vehicles table with V-005 at the top
    risk_table_data = [
        {
            'Vehicle ID': 'V-005',
            'Predicted Failure Date': '2025-12-20',
            'Component at Risk': 'Brake Pads',
            'Est. Repair Cost': '₹25,000',
            'Urgency Score': 95,
            'Status': '🔴 Critical'
        },
        {
            'Vehicle ID': 'V-023',
            'Predicted Failure Date': '2025-12-28',
            'Component at Risk': 'Battery',
            'Est. Repair Cost': '₹18,500',
            'Urgency Score': 82,
            'Status': '🟠 High'
        },
        {
            'Vehicle ID': 'V-041',
            'Predicted Failure Date': '2026-01-05',
            'Component at Risk': 'Oil Filter',
            'Est. Repair Cost': '₹8,200',
            'Urgency Score': 68,
            'Status': '🟠 High'
        },
        {
            'Vehicle ID': 'V-017',
            'Predicted Failure Date': '2026-01-12',
            'Component at Risk': 'Coolant System',
            'Est. Repair Cost': '₹32,000',
            'Urgency Score': 64,
            'Status': '🟡 Medium'
        },
        {
            'Vehicle ID': 'V-009',
            'Predicted Failure Date': '2026-01-18',
            'Component at Risk': 'Transmission',
            'Est. Repair Cost': '₹65,000',
            'Urgency Score': 59,
            'Status': '🟡 Medium'
        }
    ]
    
    # Create header row using columns
    header_cols = st.columns([1, 1.5, 1.5, 1, 1, 0.8])
    header_style = "font-weight: 600; color: #000000; font-size: 13px;"
    
    with header_cols[0]:
        st.markdown(f"<div style='{header_style}'>Vehicle ID</div>", unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown(f"<div style='{header_style}'>Predicted Failure Date</div>", unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown(f"<div style='{header_style}'>Component at Risk</div>", unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown(f"<div style='{header_style}'>Est. Repair Cost</div>", unsafe_allow_html=True)
    with header_cols[4]:
        st.markdown(f"<div style='{header_style}'>Urgency Score</div>", unsafe_allow_html=True)
    with header_cols[5]:
        st.markdown(f"<div style='{header_style}'>Status</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Create data rows
    for item in risk_table_data:
        # Determine row background color based on urgency (blue shades)
        if item['Urgency Score'] >= 90:
            row_bg = '#DBEAFE'  # Light blue for critical
        elif item['Urgency Score'] >= 70:
            row_bg = '#BFDBFE'  # Medium blue for high
        else:
            row_bg = '#E0F2FE'  # Lighter blue for medium
        
        row_style = f"padding: 10px; background: {row_bg}; border-radius: 5px; margin-bottom: 4px; color: #000000; font-size: 13px;"
        
        row_cols = st.columns([1, 1.5, 1.5, 1, 1, 0.8])
        
        with row_cols[0]:
            st.markdown(f"<div style='{row_style}; font-weight: 600;'>{item['Vehicle ID']}</div>", unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f"<div style='{row_style}'>{item['Predicted Failure Date']}</div>", unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f"<div style='{row_style}'>{item['Component at Risk']}</div>", unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f"<div style='{row_style}'>{item['Est. Repair Cost']}</div>", unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f"<div style='{row_style}; font-weight: 600;'>{item['Urgency Score']}</div>", unsafe_allow_html=True)
        with row_cols[5]:
            st.markdown(f"<div style='{row_style}; font-weight: 600;'>{item['Status']}</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top: 12px; padding: 12px; background: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 4px;">
        <strong style="color: #92400E;">⚡ Next Action:</strong> 
        <span style="color: #78350F;">Schedule maintenance for V-005 before Dec 20, 2025 to prevent brake failure.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- SERVICE OPERATIONS & SCHEDULING DASHBOARD ---
def render_scheduling_page(user):
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime, timedelta, time
    import random
    
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 26px; font-weight: 600; color: #2C3E50; margin: 0 0 8px 0;">
            Service Operations Command
        </h2>
        <p style="color: #95A5A6; margin: 0; font-size: 15px;">Real-time scheduling, bay optimization, and demand forecasting</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Header controls
    col_date, col_city, col_opt = st.columns([2, 2, 2])
    
    with col_date:
        selected_date = st.date_input("📅 Select Date", value=datetime.now(), key="schedule_date")
    
    with col_city:
        selected_city = st.selectbox("🏙️ Service City", ["Pune", "Mumbai", "Bangalore"], key="schedule_city")
    
    with col_opt:
        pass  # Removed Optimize button
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Today's Appointments</div>
                    <div style="font-size: 32px; font-weight: 600; color: #4A5F8C; margin-bottom: 4px;">18</div>
                    <div style="color: #27AE60; font-size: 12px; font-weight: 600;">↑ 3 vs yesterday</div>
                </div>
                <div class="metric-icon" style="background: #D6EAF8;">
                    <span style="font-size: 24px;">📅</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Bay Utilization</div>
                    <div style="font-size: 32px; font-weight: 600; color: #FF9F43; margin-bottom: 4px;">87%</div>
                    <div style="color: #FF9F43; font-size: 12px; font-weight: 600;">Near capacity</div>
                </div>
                <div class="metric-icon" style="background: #FFE8D1;">
                    <span style="font-size: 24px;">🏗️</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Avg Service Time</div>
                    <div style="font-size: 32px; font-weight: 600; color: #4A5F8C; margin-bottom: 4px;">1.8h</div>
                    <div style="color: #27AE60; font-size: 12px; font-weight: 600;">↓ 15% improvement</div>
                </div>
                <div class="metric-icon" style="background: #D6EAF8;">
                    <span style="font-size: 24px;">⏱️</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #95A5A6; font-size: 12px; font-weight: 500; margin-bottom: 8px; text-transform: uppercase;">Urgent/Critical Jobs</div>
                    <div style="font-size: 32px; font-weight: 600; color: #E74C3C; margin-bottom: 4px;">3</div>
                    <div style="color: #E74C3C; font-size: 12px; font-weight: 600;">Immediate attention</div>
                </div>
                <div class="metric-icon" style="background: #FADBD8;">
                    <span style="font-size: 24px;">🚨</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Row 1: Service Center Map & Bay Utilization
    map_col, bay_col = st.columns([1, 1])
    
    # Service Center Map
    with map_col:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Service Center Load Map</h3>
        """, unsafe_allow_html=True)
        
        # Mock service centers for Pune
        centers = [
            {"name": "Downtown Hub", "lat": 18.5204, "lon": 73.8567, "load": 92, "status": "Full"},
            {"name": "Kothrud Center", "lat": 18.5074, "lon": 73.8077, "load": 45, "status": "Available"},
            {"name": "Viman Nagar", "lat": 18.5679, "lon": 73.9143, "load": 78, "status": "Busy"},
            {"name": "Wakad Service", "lat": 18.5978, "lon": 73.7636, "load": 35, "status": "Available"},
            {"name": "Hadapsar Hub", "lat": 18.5018, "lon": 73.9263, "load": 88, "status": "Full"},
        ]
        
        df_centers = pd.DataFrame(centers)
        df_centers['color'] = df_centers['load'].apply(lambda x: '#E74C3C' if x > 80 else '#FF9F43' if x > 60 else '#27AE60')
        
        fig_map = go.Figure()
        
        for status_color in ['#27AE60', '#FF9F43', '#E74C3C']:
            df_subset = df_centers[df_centers['color'] == status_color]
            status_name = 'Available' if status_color == '#27AE60' else 'Busy' if status_color == '#FF9F43' else 'Full'
            
            fig_map.add_trace(go.Scattermapbox(
                lat=df_subset['lat'],
                lon=df_subset['lon'],
                mode='markers+text',
                marker=dict(size=20, color=status_color),
                text=df_subset['name'],
                textposition='top center',
                name=status_name,
                hovertemplate='<b>%{text}</b><br>Load: ' + df_subset['load'].astype(str) + '%<extra></extra>'
            ))
        
        fig_map.update_layout(
            mapbox=dict(
                style='carto-positron',
                center=dict(lat=18.5204, lon=73.8567),
                zoom=10
            ),
            height=350,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_map, use_container_width=True, key="service_map")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Bay Utilization Timeline (Gantt Chart)
    with bay_col:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Bay Utilization Timeline (Today)</h3>
        """, unsafe_allow_html=True)
        
        # Create Gantt chart data using Plotly's timeline
        df_gantt = pd.DataFrame([
            dict(Task="Bay 1", Start='2024-12-16 09:00:00', Finish='2024-12-16 11:00:00', Resource='Standard'),
            dict(Task="Bay 1", Start='2024-12-16 12:00:00', Finish='2024-12-16 14:30:00', Resource='Standard'),
            dict(Task="Bay 2", Start='2024-12-16 09:30:00', Finish='2024-12-16 12:00:00', Resource='Standard'),
            dict(Task="Bay 2", Start='2024-12-16 13:00:00', Finish='2024-12-16 16:00:00', Resource='Standard'),
            dict(Task="Bay 3 (Priority)", Start='2024-12-16 10:00:00', Finish='2024-12-16 13:00:00', Resource='Standard'),
            dict(Task="Bay 3 (Priority)", Start='2024-12-16 16:30:00', Finish='2024-12-16 18:00:00', Resource='V-005 Critical'),
            dict(Task="Bay 4", Start='2024-12-16 11:00:00', Finish='2024-12-16 15:00:00', Resource='Standard'),
            dict(Task="Bay 5", Start='2024-12-16 09:00:00', Finish='2024-12-16 12:30:00', Resource='Standard'),
            dict(Task="Bay 5", Start='2024-12-16 14:00:00', Finish='2024-12-16 17:00:00', Resource='Standard'),
        ])
        
        # Convert to datetime
        df_gantt['Start'] = pd.to_datetime(df_gantt['Start'])
        df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish'])
        
        # Create color mapping
        df_gantt['Color'] = df_gantt['Resource'].map({'Standard': '#4A5F8C', 'V-005 Critical': '#E74C3C'})
        
        # Use Plotly Express timeline
        fig_gantt = px.timeline(
            df_gantt,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Resource",
            color_discrete_map={'Standard': '#4A5F8C', 'V-005 Critical': '#E74C3C'},
            hover_data=["Resource"]
        )
        
        fig_gantt.update_layout(
            font=dict(color='#000000', size=12),
            xaxis=dict(
                title=dict(text='Time', font=dict(color='#000000', size=12)),
                tickformat='%H:%M',
                range=['2024-12-16 08:30:00', '2024-12-16 18:30:00'],
                tickfont=dict(color='#000000', size=11)
            ),
            yaxis=dict(
                title=dict(text='Service Bay', font=dict(color='#000000', size=12)),
                autorange="reversed",
                tickfont=dict(color='#000000', size=11)
            ),
            height=350,
            margin=dict(l=120, r=20, t=20, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color='#000000', size=11))
        )
        
        st.plotly_chart(fig_gantt, use_container_width=True, key="bay_gantt")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Demand Forecast
    st.markdown("""
    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2C3E50;">Weekly Demand Forecast</h3>
    """, unsafe_allow_html=True)
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    expected = [15, 18, 16, 20, 22, 12, 8]
    actual = [14, 19, 15, 18, 21, 13, 0]  # Sunday not yet happened
    
    fig_demand = go.Figure()
    
    fig_demand.add_trace(go.Scatter(
        x=days,
        y=expected,
        mode='lines+markers',
        name='Expected Inflow',
        line=dict(color='#7B8FAD', width=2, dash='dash'),
        marker=dict(size=8)
    ))
    
    fig_demand.add_trace(go.Scatter(
        x=days[:6],  # Only show actual for past days
        y=actual[:6],
        mode='lines+markers',
        name='Actual Inflow',
        line=dict(color='#4A5F8C', width=3),
        marker=dict(size=10)
    ))
    
    fig_demand.update_layout(
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E8EDF5',
            title=dict(text='Vehicles', font=dict(color='#2C3E50', size=12))
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig_demand, use_container_width=True, key="demand_forecast")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
    
    # Real-Time Appointment Register
    st.subheader("📋 Real-Time Appointment Register")
    st.caption("Live schedule for Downtown Hub - December 16, 2024")
    
    # Create appointment data as list of dicts for easier iteration
    appointments = [
        {"Time": "09:00 AM", "Vehicle": "V-012", "Owner": "Rajesh Kumar", "Service": "Oil Change", "Status": "✅ Completed", "Bay": "Bay 1", "priority": "normal"},
        {"Time": "10:30 AM", "Vehicle": "V-034", "Owner": "Priya Sharma", "Service": "Tire Rotation", "Status": "✅ Completed", "Bay": "Bay 2", "priority": "normal"},
        {"Time": "12:00 PM", "Vehicle": "V-018", "Owner": "Amit Patel", "Service": "Battery Replacement", "Status": "🔄 In Progress", "Bay": "Bay 4", "priority": "normal"},
        {"Time": "01:30 PM", "Vehicle": "V-027", "Owner": "Sneha Desai", "Service": "Coolant Service - High Priority", "Status": "🔄 In Progress", "Bay": "Bay 5", "priority": "high"},
        {"Time": "03:00 PM", "Vehicle": "V-041", "Owner": "Vikram Singh", "Service": "Transmission Check", "Status": "📅 Confirmed", "Bay": "Bay 2", "priority": "normal"},
        {"Time": "04:30 PM", "Vehicle": "V-005", "Owner": "Arjun Mehta", "Service": "🚨 Brake Replacement - CRITICAL", "Status": "📅 Confirmed", "Bay": "Bay 3 (Priority)", "priority": "critical"},
        {"Time": "05:00 PM", "Vehicle": "V-019", "Owner": "Neha Gupta", "Service": "General Inspection", "Status": "📅 Confirmed", "Bay": "Bay 1", "priority": "normal"},
    ]
    
    # Create header row
    header_cols = st.columns([1, 1, 1.5, 2.5, 1.5, 1.5])
    header_style = "font-weight: bold; color: #1F2937; padding: 8px; background: #F3F4F6; border-radius: 5px;"
    with header_cols[0]:
        st.markdown(f"<div style='{header_style}'>Time</div>", unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown(f"<div style='{header_style}'>Vehicle</div>", unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown(f"<div style='{header_style}'>Owner</div>", unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown(f"<div style='{header_style}'>Service Type</div>", unsafe_allow_html=True)
    with header_cols[4]:
        st.markdown(f"<div style='{header_style}'>Status</div>", unsafe_allow_html=True)
    with header_cols[5]:
        st.markdown(f"<div style='{header_style}'>Bay</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Create data rows
    for appt in appointments:
        # Determine background color
        if appt['priority'] == 'critical':
            bg_color = "#FEE2E2"  # Light red
            font_weight = "600"
        elif appt['priority'] == 'high':
            bg_color = "#FEF3C7"  # Light yellow
            font_weight = "500"
        else:
            bg_color = "#FFFFFF"  # White
            font_weight = "400"
        
        row_style = f"padding: 10px; background: {bg_color}; border-radius: 5px; margin-bottom: 4px; font-weight: {font_weight}; color: #374151;"
        
        row_cols = st.columns([1, 1, 1.5, 2.5, 1.5, 1.5])
        with row_cols[0]:
            st.markdown(f"<div style='{row_style}'>{appt['Time']}</div>", unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f"<div style='{row_style}'>{appt['Vehicle']}</div>", unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f"<div style='{row_style}'>{appt['Owner']}</div>", unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f"<div style='{row_style}'>{appt['Service']}</div>", unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f"<div style='{row_style}'>{appt['Status']}</div>", unsafe_allow_html=True)
        with row_cols[5]:
            st.markdown(f"<div style='{row_style}'>{appt['Bay']}</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.info("💡 **AI Optimization Active:** Critical job V-005 automatically prioritized to Bay 3. ETA: 1.5 hours. Customer Arjun Mehta notified via WhatsApp.")

# --- CUSTOMER CHAT TAB ---
def play_agent_audio(text):
    """Generate and play agent voice using gTTS"""
    if not GTTS_AVAILABLE:
        return
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        # Silently fail if internet is flaky
        pass

def render_customer_chat(user):
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 26px; font-weight: 600; color: #2C3E50; margin: 0 0 8px 0;">
            Customer Experience Console
        </h2>
        <p style="color: #95A5A6; margin: 0; font-size: 15px;">AI-powered support with voice and multilingual capabilities</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for the demo conversation
    if "demo_conversation_loaded" not in st.session_state:
        st.session_state["demo_conversation_loaded"] = False
        st.session_state["selected_language"] = "English"
        st.session_state["voice_enabled"] = False
        st.session_state["mic_clicked"] = False
        st.session_state["auto_play_done"] = False
        st.session_state["last_played_index"] = -1
    
    # Create 3-column layout: History | Chat | Profile with proper spacing
    left_panel, middle_panel, right_panel = st.columns([1.2, 2.5, 1.2], gap="medium")
    
    # ============================================
    # LEFT PANEL - Conversation History
    # ============================================
    with left_panel:
        st.markdown("""
        <div style="margin-bottom: 12px; border-bottom: 2px solid #4A5F8C; padding-bottom: 8px;">
            <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #2C3E50;">
                📋 Conversation History
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Mock conversation history
        history_items = [
            {"date": "Today", "topic": "Brake Alert", "status": "Active", "color": "#3B82F6"},
            {"date": "Yesterday", "topic": "10k Service Reminder", "status": "Closed", "color": "#60A5FA"},
            {"date": "Last Week", "topic": "Battery Voltage Inquiry", "status": "Resolved", "color": "#93C5FD"},
            {"date": "Oct 15", "topic": "Tire Pressure Alert", "status": "Resolved", "color": "#93C5FD"},
        ]
        
        for item in history_items:
            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {item['color']}; cursor: pointer; transition: all 0.2s;">
                <div style="font-size: 10px; color: #6B7280; margin-bottom: 3px;">{item['date']}</div>
                <div style="font-size: 12px; font-weight: 600; color: #2C3E50; margin-bottom: 3px;">{item['topic']}</div>
                <div style="font-size: 10px; color: {item['color']};">● {item['status']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================
    # MIDDLE PANEL - Live Active Chat
    # ============================================
    with middle_panel:
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 2px solid #4A5F8C; padding-bottom: 8px;">
            <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #2C3E50;">
                💬 Live Chat - Arjun Mehta (V-005)
            </h3>
            <div style="display: flex; align-items: center; gap: 6px;">
                <div style="width: 8px; height: 8px; background: #27AE60; border-radius: 50%;"></div>
                <span style="font-size: 11px; color: #27AE60; font-weight: 600;">CONNECTED</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Language selector in header
        selected_language = st.selectbox(
            "Select Language",
            ["English", "हिंदी (Hindi)", "తెలుగు (Telugu)", "தமிழ் (Tamil)"],
            key="chat_language",
            label_visibility="visible"
        )
        if selected_language != st.session_state["selected_language"]:
            st.session_state["selected_language"] = selected_language
        
        st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
        
        # Display sample conversation
        if st.session_state["selected_language"] == "English":
            conversation = [
                {"role": "assistant", "name": "AutoGuard AI", "content": "Hello Arjun. Critical brake wear detected. Our diagnostics have detected **critical brake pad wear (2.1mm)** on your Tesla Model Y (V-005). It is unsafe to continue driving normally.", "time": "14:32"},
            ]
        elif st.session_state["selected_language"] == "हिंदी (Hindi)":
            conversation = [
                {"role": "assistant", "name": "AutoGuard AI", "content": "नमस्ते अर्जुन। यह AutoGuard से एक जरूरी अलर्ट है। हमारे डायग्नोस्टिक्स ने आपकी Tesla Model Y (V-005) में **गंभीर ब्रेक पैड घिसाव (2.1mm)** का पता लगाया है। सामान्य रूप से गाड़ी चलाना असुरक्षित है।", "time": "14:32"},
                {"role": "user", "name": "Arjun Mehta", "content": "अरे नहीं। यह तो बहुत बुरा है। मुझे कल गाड़ी चाहिए। मुझे क्या करना चाहिए?", "time": "14:33"},
                {"role": "assistant", "name": "AutoGuard AI", "content": "गंभीरता को देखते हुए, **तत्काल सर्विस आवश्यक है**। मैंने डाउनटाउन सर्विस हब पर आज **शाम 4:30 बजे** एक प्राथमिकता स्लॉट पाया है। क्या मैं अभी इसे बुक कर दूं?", "time": "14:33"},
                {"role": "user", "name": "Arjun Mehta", "content": "हां, कृपया तुरंत बुक कर दें।", "time": "14:34"},
                {"role": "assistant", "name": "AutoGuard AI", "content": "**पुष्टि की गई।** आपकी अपॉइंटमेंट आज **शाम 4:30 बजे** डाउनटाउन सर्विस हब में तय है। आपके WhatsApp (+91 98765 43210) पर एक पुष्टिकरण भेजा गया है। कृपया सावधानी से सेंटर तक गाड़ी चलाएं।", "time": "14:34"},
            ]
        else:
            # Telugu or Tamil - show English with note
            conversation = [
                {"role": "assistant", "name": "AutoGuard AI", "content": f"**Language switched to {st.session_state['selected_language']}**\n\nHello Arjun. Critical brake alert detected. Immediate service required.", "time": "14:32"},
                {"role": "user", "name": "Arjun Mehta", "content": "Please help me book service.", "time": "14:33"},
                {"role": "assistant", "name": "AutoGuard AI", "content": "Confirmed. Service booked for 4:30 PM today.", "time": "14:34"},
            ]
        
        # Add simulated microphone response if button was clicked
        if st.session_state.get("mic_clicked", False):
            # Add user voice message
            conversation.append({
                "role": "user", 
                "name": "Arjun Mehta", 
                "content": "Yes, please book the appointment immediately for 4:30 pm tomorrow at the Bay 3 Main center.", 
                "time": "14:34"
            })
            # Add agent confirmation
            agent_response = "Confirmed. I have booked your appointment for tomorrow at 4:30 PM at Bay 3 Main center. A confirmation has been sent to your WhatsApp. Please drive cautiously to the center."
            conversation.append({
                "role": "assistant",
                "name": "AutoGuard AI",
                "content": f"**{agent_response}**",
                "time": "14:34"
            })
            # Play agent voice
            play_agent_audio(agent_response)
            st.session_state["mic_clicked"] = False  # Reset after showing
        
        # Auto-play opening message on first load
        if not st.session_state.get("auto_play_done", False) and len(conversation) > 0:
            first_msg = conversation[0]
            if first_msg["role"] == "assistant":
                play_agent_audio("Hello Arjun. Critical brake wear detected. Our diagnostics have detected critical brake pad wear on your Tesla Model Y. It is unsafe to continue driving normally.")
                st.session_state["auto_play_done"] = True
                st.session_state["last_played_index"] = 0
        
        # Auto-play voice for new agent messages
        if len(conversation) > 0:
            last_msg = conversation[-1]
            if last_msg["role"] == "assistant" and st.session_state.get("last_played_index", -1) < len(conversation) - 1:
                # Extract text without markdown for TTS
                text_content = last_msg["content"].replace("**", "").replace("*", "")
                play_agent_audio(text_content)
                st.session_state["last_played_index"] = len(conversation) - 1
        
        # Render conversation using Streamlit's native chat_message (no container wrapper)
        for msg in conversation:
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.caption(f"**{msg['name']}** • {msg['time']}")
                st.markdown(msg['content'])
        
        # Chat input at bottom - fixed position
        st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
        
        # Microphone button above input (visual only for prototype)
        mic_col1, mic_col2 = st.columns([1, 5])
        with mic_col1:
            st.button("🎤 Tap to Speak", use_container_width=True, help="Tap to speak", disabled=True)
        
        col_input, col_send = st.columns([6, 1.5])
        with col_input:
            chat_input = st.text_input("Type your message...", key="chat_input_field", placeholder="Ask a question or request assistance...", label_visibility="collapsed")
        with col_send:
            if st.button("Send", type="primary", use_container_width=True):
                # Trigger the simulated microphone response
                st.session_state["mic_clicked"] = True
                st.rerun()
    
    # ============================================
    # RIGHT PANEL - Customer & Vehicle Profile
    # ============================================
    with right_panel:
        st.markdown("""
        <div style="margin-bottom: 12px; border-bottom: 2px solid #4A5F8C; padding-bottom: 8px;">
            <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #2C3E50;">
                👤 Customer Profile
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Customer details - more compact
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="background: #4A5F8C; color: white; width: 56px; height: 56px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;">
                    AM
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 15px; font-weight: 600; color: #2C3E50; margin-bottom: 3px;">Arjun Mehta</div>
                <div style="font-size: 11px; color: #6B7280;">Premium Customer</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Contact info - more compact
        profile_fields = [
            {"icon": "📞", "label": "Phone", "value": "+91 98765 43210"},
            {"icon": "📧", "label": "Email", "value": "arjun.m@email.com"},
            {"icon": "🚗", "label": "Vehicle", "value": "Tesla Model Y"},
            {"icon": "🔢", "label": "VIN", "value": "V-005"},
            {"icon": "📅", "label": "Registration", "value": "Jan 15, 2023"},
            {"icon": "🛣️", "label": "Odometer", "value": "24,850 km"},
        ]
        
        for field in profile_fields:
            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 8px 10px; border-radius: 6px; margin-bottom: 6px;">
                <div style="font-size: 10px; color: #6B7280; margin-bottom: 2px;">{field['icon']} {field['label']}</div>
                <div style="font-size: 12px; font-weight: 600; color: #2C3E50;">{field['value']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Current Status Alert - more compact
        st.markdown("""
        <div style="background: #DBEAFE; border: 2px solid #3B82F6; padding: 10px; border-radius: 8px; margin-top: 12px;">
            <div style="font-size: 11px; font-weight: 600; color: #1E40AF; margin-bottom: 3px;">CURRENT STATUS</div>
            <div style="font-size: 12px; color: #1E3A8A; font-weight: 600;">Critical - Brake Fault</div>
            <div style="font-size: 10px; color: #1E40AF; margin-top: 3px;">Service: Today 4:30 PM</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick actions
        st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)
        

# --- MAIN APP ---
def main():
    if not st.session_state["authenticated"]:
        render_login()
    else:
        render_dashboard(st.session_state["current_user"])

if __name__ == "__main__":
    main()
