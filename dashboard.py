# Supabase logout function (Python equivalent)
def logout():
    """
    Log out the current user using Supabase authentication.
    """
    if not supabase:
        print("Supabase client not initialized.")
        return
    try:
        response = supabase.auth.sign_out()
        error = response.get('error', None)
        if error:
            print(f"Logout error: {error}")
        else:
            print("User logged out successfully")
    except Exception as e:
        print(f"Logout exception: {e}")

# Supabase get current user function (Python equivalent)
def get_current_user():
    """
    Get the current authenticated user from Supabase.
    """
    if not supabase:
        print("Supabase client not initialized.")
        return None
    try:
        response = supabase.auth.get_user()
        print(f"Current user: {response}")
        return response
    except Exception as e:
        print(f"Get user exception: {e}")
        return None

# Supabase auth state change handler (Python equivalent)
def on_auth_state_change(event, session):
    print(f"Auth event: {event}")
    print(f"Session: {session}")
# Supabase sign up and authentication function (Python equivalent)
def sign_up(email, password):
    """
    Sign up a new user using Supabase authentication.
    Returns the user data if successful, None otherwise.
    """
    if not supabase:
        print("Supabase client not initialized.")
        return None
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        data = response.get('data', {})
        error = response.get('error', None)
        if error:
            print(f"Sign up error: {error}")
            return None
        print(f"User signed up: {data.get('user')}")
        return data.get('user')
    except Exception as e:
        print(f"Sign up exception: {e}")
        return None
import streamlit as st
import pandas as pd
import joblib
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from dotenv import load_dotenv
import os



st.set_page_config(
    page_title="Museum Analytics Dashboard", 
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

# --- Supabase client initialization ---
supabase = None
try:
    load_dotenv()
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        st.warning("Supabase credentials not set in environment.")
except Exception as e:
    st.warning(f"Supabase client not initialized: {e}")

# Database helper functions
def create_admin_account(username, password, email, role="admin"):
    """
    Create a new admin account in the admin_users table.
    Uses the existing admin_users table structure with bigserial id,
    username, email, password_hash, role, created_at, and last_login.
    """
    if not supabase:
        return False, "Database connection not available"
    
    try:
        # Check if username already exists
        existing_user = supabase.table("admin_users").select("username").eq("username", username).execute()
        if existing_user.data:
            return False, "Username already exists"
        
        # Check if email already exists
        existing_email = supabase.table("admin_users").select("email").eq("email", email).execute()
        if existing_email.data:
            return False, "Email already exists"
        
        # Hash password and create admin user
        password_hash = hash_password(password)
        admin_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role
        }
        
        response = supabase.table("admin_users").insert(admin_data).execute()
        return True, "Admin account created successfully"
        
    except Exception as e:
        return False, f"Error creating admin account: {str(e)}"

# Authentication functions
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """
    Authenticate admin user against Supabase admin_users table.
    Returns True if authentication successful, False otherwise.
    Also updates last_login timestamp on successful authentication.
    """
    if not supabase:
        st.error("Database connection not available. Please check configuration.")
        return False
    
    try:
        # Hash the provided password for comparison
        password_hash = hash_password(password)
        
        # Query the admin_users table for matching credentials
        response = supabase.table("admin_users").select("*").eq("username", username).eq("password_hash", password_hash).execute()
        
        if response.data and len(response.data) > 0:
            # User found and password matches
            user_data = response.data[0]
            user_id = user_data.get("id")
            
            # Update last_login timestamp
            try:
                supabase.table("admin_users").update({"last_login": datetime.now().isoformat()}).eq("id", user_id).execute()
            except Exception as login_error:
                # Don't fail auth if we can't update last_login
                st.warning(f"Could not update last login: {login_error}")
            
            # Store user info in session
            st.session_state.user_role = user_data.get("role", "admin")
            st.session_state.user_id = user_id
            st.session_state.user_email = user_data.get("email")
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

# ================================================================
# DATA FETCHING FUNCTIONS FOR MUSEUM ANALYTICS
# ================================================================

def fetch_daily_metrics():
    """Fetch daily metrics data with environment conditions."""
    try:
        if not supabase:
            return None
        
        response = supabase.table("daily_metrics").select(
            "*, environment_conditions(condition, temperature_c, humidity, season)"
        ).order("date", desc=True).execute()
        
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching daily metrics: {str(e)}")
        return pd.DataFrame()

def fetch_models():
    """Fetch all models with their statistics."""
    try:
        if not supabase:
            return None
        
        response = supabase.table("models").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return pd.DataFrame()

def fetch_model_events(model_id=None, limit=100):
    """Fetch model scan events, optionally filtered by model."""
    try:
        if not supabase:
            return None
        
        query = supabase.table("model_events").select(
            "*, models(qr_name, description), admin_users(username)"
        ).order("created_at", desc=True).limit(limit)
        
        if model_id:
            query = query.eq("model_id", model_id)
            
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching model events: {str(e)}")
        return pd.DataFrame()

def fetch_view_sessions(model_id=None, limit=100):
    """Fetch model view sessions with duration statistics."""
    try:
        if not supabase:
            return None
            
        query = supabase.table("model_view_sessions").select(
            "*, models(qr_name, description), admin_users(username)"
        ).order("started_at", desc=True).limit(limit)
        
        if model_id:
            query = query.eq("model_id", model_id)
            
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching view sessions: {str(e)}")
        return pd.DataFrame()

def fetch_visitor_profiles():
    """Fetch visitor demographic data."""
    try:
        if not supabase:
            return None
            
        response = supabase.table("visitor_profiles").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching visitor profiles: {str(e)}")
        return pd.DataFrame()

def fetch_environment_conditions(limit=100):
    """Fetch recent environment conditions."""
    try:
        if not supabase:
            return None
            
        response = supabase.table("environment_conditions").select("*").order(
            "recorded_at", desc=True
        ).limit(limit).execute()
        
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching environment conditions: {str(e)}")
        return pd.DataFrame()

def fetch_session_context(limit=100):
    """Fetch session context with related data."""
    try:
        if not supabase:
            return None
            
        response = supabase.table("session_context").select(
            """*, 
            model_view_sessions(*, models(qr_name, description)), 
            environment_conditions(condition, temperature_c, humidity, season),
            visitor_profiles(age_group, country, preferred_language)"""
        ).order("day", desc=True).limit(limit).execute()
        
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching session context: {str(e)}")
        return pd.DataFrame()

def get_analytics_summary():
    """Get comprehensive analytics summary across all tables."""
    try:
        if not supabase:
            return {}
            
        summary = {}
        
        # Total models
        models_response = supabase.table("models").select("id", count="exact").execute()
        summary['total_models'] = models_response.count or 0
        
        # Total events today
        from datetime import datetime, date
        today = date.today().isoformat()
        events_response = supabase.table("model_events").select(
            "id", count="exact"
        ).gte("created_at", today).execute()
        summary['events_today'] = events_response.count or 0
        
        # Active sessions today
        sessions_response = supabase.table("model_view_sessions").select(
            "id", count="exact"
        ).gte("started_at", today).execute()
        summary['sessions_today'] = sessions_response.count or 0
        
        # Average session duration
        duration_response = supabase.table("model_view_sessions").select(
            "duration_seconds"
        ).not_.is_("ended_at", "null").execute()
        
        if duration_response.data:
            durations = [s['duration_seconds'] for s in duration_response.data if s['duration_seconds']]
            summary['avg_duration'] = sum(durations) / len(durations) if durations else 0
        else:
            summary['avg_duration'] = 0
            
        return summary
    except Exception as e:
        st.error(f"Error fetching analytics summary: {str(e)}")
        return {}

def show_login_page():
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-top: 5rem;
        }
        .login-header {
            text-align: center;
            color: white;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    # Center the login/sign up form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                🏛️ Museum Dashboard
            </div>
            <div class="demo-credentials">
                <strong>🔐 Secure Database Authentication</strong><br>
                Please use your credentials to log in or sign up.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="login-form">', unsafe_allow_html=True)
        with st.form("auth_form"):
            st.markdown("### 🔐 Login or Sign Up")
            email = st.text_input("📧 Email", placeholder="Enter your email")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            action = st.radio("Choose action", ["Login", "Sign Up"])
            col_submit, col_reset = st.columns([2, 1])
            with col_submit:
                submit_button = st.form_submit_button("🚀 Submit", use_container_width=True)
            with col_reset:
                if st.form_submit_button("🔄 Reset", use_container_width=True):
                    st.session_state.login_attempts = 0
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        if submit_button:
            if email and password:
                if st.session_state.login_attempts >= 5:
                    st.error("🚫 Too many failed attempts. Please refresh the page.")
                else:
                    if action == "Sign Up":
                        user = sign_up(email, password)
                        if user:
                            st.success(f"User signed up: {user}")
                            st.balloons()
                        else:
                            st.error("Sign up failed. Please check your credentials.")
                    elif action == "Login":
                        try:
                            if not supabase:
                                st.error("Supabase client not initialized.")
                            else:
                                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                                data = response.get('data', {})
                                error = response.get('error', None)
                                if error:
                                    st.error(f"Login error: {error}")
                                    st.session_state.login_attempts += 1
                                elif data.get('user'):
                                    st.session_state.logged_in = True
                                    st.session_state.username = email
                                    st.session_state.login_attempts = 0
                                    st.success(f"✅ Welcome, {email}!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Login failed. Please check your credentials.")
                                    st.session_state.login_attempts += 1
                        except Exception as e:
                            st.error(f"Login exception: {e}")
                            st.session_state.login_attempts += 1
            else:
                st.warning("⚠️ Please enter both email and password.")
        # Show login attempts warning
        if st.session_state.login_attempts > 0:
            st.info(f"🔢 Login attempts: {st.session_state.login_attempts}/5")
                    st.session_state.login_attempts = 0
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if login_button:
            if username and password:
                if st.session_state.login_attempts >= 5:
                    st.error("🚫 Too many failed attempts. Please refresh the page.")
                else:
                    if authenticate_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.login_attempts = 0
                        st.success(f"✅ Welcome, {username}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        remaining_attempts = 5 - st.session_state.login_attempts
                        st.error(f"❌ Invalid credentials. {remaining_attempts} attempts remaining.")
            else:
                st.warning("⚠️ Please enter both username and password.")
        
        # Show login attempts warning
        if st.session_state.login_attempts > 0:
            st.info(f"🔢 Login attempts: {st.session_state.login_attempts}/5")

# Modern CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: white;
        margin: 0.5rem 0;
    }
    
    .tab-header {
        font-size: 2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1.5rem;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .prediction-form {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Main application logic
if not st.session_state.logged_in:
    show_login_page()
else:
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
            color: white;
        ">
            <h3>👤 {st.session_state.username}</h3>
            <p>Logged in successfully</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.login_attempts = 0
            st.success("👋 Successfully logged out!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Navigation")
        st.markdown("""
        - 🔮 **Predictions**: AI-powered forecasting
        - 📈 **Analytics**: Data visualization dashboard  
        - 🏛️ **Artifacts**: Collection management
        - 👥 **Users**: Account administration
        """)
    
    # Main dashboard header
    st.markdown('<h1 class="main-header">🏛️ Museum Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; color: #7f8c8d; font-size: 1.2rem; margin-bottom: 2rem;">Welcome back, <strong>{st.session_state.username}</strong>! Advanced Analytics & Predictive Intelligence Platform</div>', unsafe_allow_html=True)

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction", "📊 Analytics", "🏛️ Artifacts", "👥 Users"])

    # --- Enhanced Prediction Tab with Real Data ---
    with tab1:
        st.markdown('<div class="tab-header">🔮 AI-Powered Visitor Predictions</div>', unsafe_allow_html=True)
        
        # Real-time data insights section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📊 Current Museum Conditions")
            
            # Fetch latest environment data
            env_df = fetch_environment_conditions(limit=5)
            if not env_df.empty:
                latest_env = env_df.iloc[0]
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    condition = latest_env.get('condition', 'Unknown')
                    st.metric("🌤️ Current Weather", condition)
                
                with col_b:
                    temp = latest_env.get('temperature_c', 0)
                    st.metric("🌡️ Temperature", f"{temp:.1f}°C")
                
                with col_c:
                    humidity = latest_env.get('humidity', 0)
                    st.metric("💧 Humidity", f"{humidity:.1f}%")
            else:
                st.info("🌤️ No environment data available - using default values")
        
        with col2:
            st.markdown("#### 👥 Visitor Insights")
            visitor_profiles = fetch_visitor_profiles()
            if not visitor_profiles.empty:
                total_profiles = len(visitor_profiles)
                most_common_age = visitor_profiles['age_group'].mode().iloc[0] if 'age_group' in visitor_profiles.columns else 'Adult'
                st.metric("📝 Total Profiles", total_profiles)
                st.metric("👤 Common Age Group", most_common_age)
            else:
                st.info("👥 No visitor profiles yet")
        
        # Enhanced prediction interface
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            pipeline_filename = 'full_preprocessing_and_model_pipeline.pkl'
            try:
                loaded_pipeline = joblib.load(pipeline_filename)
                pipeline_loaded = True
                st.success("✅ ML Pipeline Successfully Loaded")
            except FileNotFoundError:
                st.error(f"❌ Pipeline file '{pipeline_filename}' not found.")
                pipeline_loaded = False
            except Exception as e:
                st.error(f"❌ Error loading pipeline: {e}")
                pipeline_loaded = False

            if pipeline_loaded:
                try:
                    feature_names = list(getattr(loaded_pipeline, 'feature_names_in_', []))
                    
                    # Dynamic options from database
                    visitor_profiles = fetch_visitor_profiles()
                    env_conditions = fetch_environment_conditions(limit=20)
                    
                    # Build categorical options from real data where possible
                    categorical_options = {
                        'env_condition': ["☁️ Cloudy", "☀️ Sunny", "🌧️ Rainy", "⛈️ Stormy", "💨 Windy", "🌫️ Clear"],
                        'env_season': ["🌸 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"],
                        'visitor_age_group': ["👶 Child", "👨 Teen", "� Adult", "👴 Senior"],
                        'event_event_type': ["📱 Scan"],
                    }
                    
                    # Add real data options if available
                    if not visitor_profiles.empty:
                        if 'age_group' in visitor_profiles.columns:
                            real_age_groups = visitor_profiles['age_group'].unique()
                            categorical_options['visitor_age_group'] = [f"� {age}" for age in real_age_groups]
                        
                        if 'country' in visitor_profiles.columns:
                            top_countries = visitor_profiles['country'].value_counts().head(5).index.tolist()
                        else:
                            top_countries = ['USA', 'UK', 'Germany', 'France', 'Spain']
                    else:
                        top_countries = ['USA', 'UK', 'Germany', 'France', 'Spain']
                    
                    st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
                    
                    with st.form("enhanced_prediction_form"):
                        st.markdown("### 📊 Prediction Parameters (Enhanced with Real Data)")
                        
                        # Quick presets based on current conditions
                        st.markdown("#### ⚡ Quick Presets")
                        preset_col1, preset_col2, preset_col3 = st.columns(3)
                        
                        with preset_col1:
                            if st.form_submit_button("🌞 Sunny Day Preset"):
                                st.session_state.preset = "sunny"
                        with preset_col2:
                            if st.form_submit_button("🌧️ Rainy Day Preset"):
                                st.session_state.preset = "rainy"
                        with preset_col3:
                            if st.form_submit_button("📊 Current Conditions"):
                                st.session_state.preset = "current"
                        
                        st.markdown("#### 📝 Manual Input")
                        
                        # Organize inputs in columns
                        col_left, col_right = st.columns(2)
                        
                        user_inputs = {}
                        
                        # Set defaults based on real data or presets
                        env_default_condition = env_df.iloc[0]['condition'] if not env_df.empty else 'Sunny'
                        env_default_temp = float(env_df.iloc[0]['temperature_c']) if not env_df.empty else 20.0
                        env_default_humidity = float(env_df.iloc[0]['humidity']) if not env_df.empty else 50.0
                        env_default_season = env_df.iloc[0]['season'] if not env_df.empty else 'Summer'
                        
                        with col_left:
                            st.markdown("**🌍 Environment Conditions**")
                            user_inputs['env_condition'] = st.selectbox(
                                "🌤️ Weather Condition", 
                                [opt.split(' ', 1)[1] for opt in categorical_options['env_condition']],
                                index=0
                            )
                            user_inputs['env_temperature_c'] = st.number_input(
                                "🌡️ Temperature (°C)", 
                                min_value=-10.0, max_value=50.0, 
                                value=env_default_temp,
                                step=0.5
                            )
                            user_inputs['env_humidity'] = st.number_input(
                                "💧 Humidity (%)", 
                                min_value=0.0, max_value=100.0, 
                                value=env_default_humidity,
                                step=1.0
                            )
                            user_inputs['env_season'] = st.selectbox(
                                "🗓️ Season",
                                [opt.split(' ', 1)[1] for opt in categorical_options['env_season']]
                            )
                            # Add missing required fields for prediction
                            user_inputs['daily_peak_hour'] = st.number_input(
                                "⏰ Daily Peak Hour",
                                min_value=0, max_value=23, value=12, step=1,
                                help="Hour of the day with the highest visitor count"
                            )
                            user_inputs['visitor_visit_frequency'] = st.number_input(
                                "🔁 Visitor Visit Frequency",
                                min_value=1, max_value=100, value=1, step=1,
                                help="How often the visitor comes (per month)"
                            )
                            user_inputs['daily_total_scans'] = st.number_input(
                                "📱 Daily Total Scans",
                                min_value=0, max_value=10000, value=100, step=1,
                                help="Total QR code scans for the day"
                            )
                            user_inputs['daily_avg_duration'] = st.number_input(
                                "⏱️ Daily Avg Duration (min)",
                                min_value=0.0, max_value=480.0, value=30.0, step=1.0,
                                help="Average visit duration in minutes"
                            )
                        
                        with col_right:
                            st.markdown("**👤 Visitor Profile**")
                            user_inputs['visitor_age_group'] = st.selectbox(
                                "👥 Target Age Group",
                                [opt.split(' ', 1)[1] for opt in categorical_options['visitor_age_group']]
                            )
                            user_inputs['visitor_country'] = st.selectbox(
                                "🌍 Visitor Country",
                                top_countries
                            )
                            user_inputs['visitor_preferred_language'] = st.selectbox(
                                "🗣️ Preferred Language",
                                ['English', 'Spanish', 'French', 'German', 'Italian', 'Other']
                            )
                            user_inputs['event_event_type'] = 'Scan'  # Default to scan events
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        submit = st.form_submit_button("🚀 Generate Visitor Prediction", use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if submit:
                        with st.spinner("🔄 Processing prediction with real museum data..."):
                            input_data = pd.DataFrame({k: [v] for k, v in user_inputs.items()})
                            try:
                                prediction = loaded_pipeline.predict(input_data)
                                
                                # Enhanced result display
                                predicted_visitors = round(prediction[0])
                                st.balloons()
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    padding: 2rem;
                                    border-radius: 15px;
                                    text-align: center;
                                    color: white;
                                    font-size: 1.5rem;
                                    font-weight: 600;
                                    margin: 1rem 0;
                                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                                ">
                                    🎯 Predicted Visitors: <span style="font-size: 2rem; font-weight: 800;">{predicted_visitors}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Enhanced insights with real data context
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("🧮 Exact Value", f"{prediction[0]:.3f}", help="Raw model output")
                                with col2:
                                    st.metric("👥 Expected Visitors", f"{predicted_visitors}", help="Rounded prediction")
                                with col3:
                                    confidence_level = "High" if abs(prediction[0] - predicted_visitors) < 0.1 else "Medium"
                                    st.metric("📊 Confidence", confidence_level, help="Prediction confidence")
                                with col4:
                                    # Compare with recent averages
                                    daily_metrics = fetch_daily_metrics()
                                    if not daily_metrics.empty and 'total_visitors' in daily_metrics.columns:
                                        avg_visitors = daily_metrics['total_visitors'].mean()
                                        comparison = "Above Average" if predicted_visitors > avg_visitors else "Below Average"
                                        st.metric("📈 vs Historical", comparison, help=f"Historical avg: {avg_visitors:.0f}")
                                    else:
                                        st.metric("📈 Data Status", "First Prediction", help="No historical data yet")
                                
                            except Exception as e:
                                st.error(f"❌ Prediction Error: {e}")
                                st.info("💡 Please verify all input parameters are correctly formatted.")
                except Exception as e:
                    st.error(f"❌ Form Generation Error: {e}")
            else:
                st.warning("⚠️ ML Pipeline not available. Please check system configuration.")
        
        # Real data insights section
        st.markdown("---")
        st.markdown("#### 📈 Historical Performance Insights")
        
        col1, col2 = st.columns(2)
        with col1:
            # Show recent daily metrics if available
            daily_metrics = fetch_daily_metrics()
            if not daily_metrics.empty:
                recent_days = min(7, len(daily_metrics))
                recent_metrics = daily_metrics.head(recent_days)
                
                fig = px.line(
                    x=pd.to_datetime(recent_metrics['date']), 
                    y=recent_metrics['total_visitors'],
                    title="📊 Recent Visitor Trends",
                    labels={'x': 'Date', 'y': 'Visitors'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No historical visitor data available yet")
        
        with col2:
            # Show environment impact on visitors
            env_conditions = fetch_environment_conditions()
            if not env_conditions.empty and not daily_metrics.empty:
                # Try to correlate environment with visitor numbers
                st.markdown("**🌤️ Weather Impact Analysis**")
                if 'condition' in env_conditions.columns:
                    condition_counts = env_conditions['condition'].value_counts()
                    fig = px.bar(
                        x=condition_counts.index,
                        y=condition_counts.values,
                        title="Weather Frequency",
                        labels={'x': 'Condition', 'y': 'Days'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("🌤️ No environment correlation data available yet")

    # --- Real-Time Analytics Tab ---
    with tab2:
        st.markdown('<div class="tab-header">📊 Live Museum Analytics Dashboard</div>', unsafe_allow_html=True)
        
        # Fetch real analytics summary
        analytics_summary = get_analytics_summary()
        
        # Real-time metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_models = analytics_summary.get('total_models', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🏛️ Total Models</h3>
                <h2>{total_models}</h2>
                <p>📊 Active in collection</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            events_today = analytics_summary.get('events_today', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🔍 Scans Today</h3>
                <h2>{events_today}</h2>
                <p>📈 QR code scans</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            sessions_today = analytics_summary.get('sessions_today', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>👀 Sessions Today</h3>
                <h2>{sessions_today}</h2>
                <p>🎯 Active viewing sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_duration = analytics_summary.get('avg_duration', 0)
            duration_minutes = int(avg_duration / 60) if avg_duration else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>⏱️ Avg. Duration</h3>
                <h2>{duration_minutes}m</h2>
                <p>📊 Per viewing session</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Real data visualizations
        st.markdown("#### 📈 Live Analytics from Database")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily metrics from database
            daily_metrics_df = fetch_daily_metrics()
            if not daily_metrics_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(daily_metrics_df['date']),
                    y=daily_metrics_df['total_visitors'],
                    mode='lines+markers',
                    name='Daily Visitors',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=6, color='#764ba2')
                ))
                
                fig.update_layout(
                    title="Daily Visitor Trends (Real Data)",
                    xaxis_title="Date",
                    yaxis_title="Number of Visitors",
                    height=400,
                    template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No daily metrics data available yet. Add some sample data to your database!")
        
        with col2:
            # Visitor age distribution from database
            visitor_profiles_df = fetch_visitor_profiles()
            if not visitor_profiles_df.empty and 'age_group' in visitor_profiles_df.columns:
                age_counts = visitor_profiles_df['age_group'].value_counts()
                
                fig = px.pie(
                    values=age_counts.values, 
                    names=age_counts.index,
                    color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                    title="Visitor Age Distribution (Real Data)"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("👥 No visitor profile data available yet. Visitor demographics will appear here once data is collected!")
        
        # Model activity heatmap
        st.markdown("#### 🔥 Model Interaction Heatmap")
        col1, col2 = st.columns(2)
        
        with col1:
            # Model events analysis
            events_df = fetch_model_events(limit=50)
            if not events_df.empty:
                # Extract model names and count events
                if 'models' in events_df.columns:
                    model_names = []
                    for idx, row in events_df.iterrows():
                        if row['models'] and isinstance(row['models'], dict):
                            model_names.append(row['models'].get('qr_name', 'Unknown'))
                        else:
                            model_names.append('Unknown')
                    
                    events_df['model_name'] = model_names
                    model_events = events_df['model_name'].value_counts()
                    
                    fig = px.bar(
                        x=model_events.index, 
                        y=model_events.values,
                        labels={'x': 'Model Name', 'y': 'Number of Scans'},
                        title="Most Scanned Models",
                        color=model_events.values,
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Model event data structure doesn't match expected format")
            else:
                st.info("🔍 No model scan events recorded yet")
        
        with col2:
            # Environment conditions impact
            env_df = fetch_environment_conditions(limit=30)
            if not env_df.empty and 'condition' in env_df.columns:
                condition_counts = env_df['condition'].value_counts()
                
                fig = px.bar(
                    x=condition_counts.index,
                    y=condition_counts.values,
                    labels={'x': 'Weather Condition', 'y': 'Frequency'},
                    title="Weather Conditions Distribution",
                    color=condition_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("🌤️ No environment data available yet")
        
        # Recent activity timeline
        st.markdown("#### ⏰ Recent Model Activity")
        recent_events = fetch_model_events(limit=10)
        if not recent_events.empty:
            # Display recent events in a nice format
            for idx, event in recent_events.iterrows():
                model_name = "Unknown Model"
                if event.get('models') and isinstance(event['models'], dict):
                    model_name = event['models'].get('qr_name', 'Unknown Model')
                
                admin_name = "System"
                if event.get('admin_users') and isinstance(event['admin_users'], dict):
                    admin_name = event['admin_users'].get('username', 'System')
                
                event_time = pd.to_datetime(event['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                
                st.markdown(f"""
                <div style="padding: 10px; margin: 5px 0; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea;">
                    <strong>🔍 {event['event_type'].title()}</strong> - {model_name}<br>
                    <small>👤 By: {admin_name} | ⏰ {event_time}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📝 No recent model activity to display")

    # --- Digital Model Collection Tab ---
    with tab3:
        st.markdown('<div class="tab-header">🏛️ Digital Model Collection Manager</div>', unsafe_allow_html=True)
        
        # Overview metrics for models
        models_df = fetch_models()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_models = len(models_df) if not models_df.empty else 0
            st.metric("🏛️ Total Models", total_models)
        
        with col2:
            events_df = fetch_model_events(limit=1000)  # Get more events for counting
            total_scans = len(events_df) if not events_df.empty else 0
            st.metric("📱 Total Scans", total_scans)
            
        with col3:
            sessions_df = fetch_view_sessions(limit=1000)
            total_sessions = len(sessions_df) if not sessions_df.empty else 0
            st.metric("👀 Total Sessions", total_sessions)
        
        # Main tabs for model management
        tab_browse, tab_add, tab_analytics, tab_remove = st.tabs(["📋 Browse Models", "➕ Add New Model", "📊 Model Analytics", "🗑️ Remove Model"])
        
        with tab_browse:
            st.markdown("### 📚 Current Model Collection")
            
            if not models_df.empty:
                # Enhanced model display with statistics
                for idx, model in models_df.iterrows():
                    model_id = model['id']
                    model_name = model['qr_name']
                    model_desc = model.get('description', 'No description available')
                    scale_factor = model.get('scale_factor', 1.0)
                    
                    # Get stats for this model
                    model_events = fetch_model_events(model_id=model_id, limit=100)
                    model_sessions = fetch_view_sessions(model_id=model_id, limit=100)
                    
                    scans_count = len(model_events) if not model_events.empty else 0
                    sessions_count = len(model_sessions) if not model_sessions.empty else 0
                    
                    # Calculate average session duration
                    avg_duration = 0
                    if not model_sessions.empty and 'duration_seconds' in model_sessions.columns:
                        valid_durations = model_sessions['duration_seconds'].dropna()
                        avg_duration = valid_durations.mean() if len(valid_durations) > 0 else 0
                    
                    with st.expander(f"🏛️ {model_name}", expanded=False):
                        col_a, col_b = st.columns([2, 1])
                        
                        with col_a:
                            st.write(f"**Description:** {model_desc}")
                            st.write(f"**Scale Factor:** {scale_factor}x")
                            st.write(f"**Model ID:** {model_id}")
                            
                        with col_b:
                            st.metric("📱 Scans", scans_count)
                            st.metric("👀 Sessions", sessions_count)
                            if avg_duration > 0:
                                st.metric("⏱️ Avg Duration", f"{int(avg_duration/60)}m {int(avg_duration%60)}s")
                        
                        # Recent activity for this model
                        if not model_events.empty:
                            st.markdown("**Recent Activity:**")
                            recent_events = model_events.head(3)
                            for _, event in recent_events.iterrows():
                                event_time = pd.to_datetime(event['created_at']).strftime('%Y-%m-%d %H:%M')
                                st.text(f"📱 {event['event_type'].title()} - {event_time}")
            else:
                st.info("🏛️ No models in collection yet. Add your first model below!")
        
        with tab_add:
            st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
            with st.form("add_model_form"):
                st.markdown("### 🏛️ New Digital Model Registration")
                
                col1, col2 = st.columns(2)
                with col1:
                    model_qr_name = st.text_input("🏷️ QR Name/ID", placeholder="Enter unique QR identifier...")
                    model_scale = st.number_input("📏 Scale Factor", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
                
                with col2:
                    model_desc = st.text_area("📝 Description", placeholder="Describe this digital model...", height=100)
                
                add_submit = st.form_submit_button("✨ Register Model", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if add_submit:
                if model_qr_name and model_desc:
                    try:
                        if supabase:
                            result = supabase.table("models").insert({
                                "qr_name": model_qr_name,
                                "description": model_desc,
                                "scale_factor": model_scale
                            }).execute()
                            if result.data:
                                st.success(f"✅ Model '{model_qr_name}' added successfully!")
                                st.balloons()
                                st.rerun()  # Refresh to show new model
                            else:
                                st.error(f"❌ Failed to add model: {result}")
                        else:
                            st.success(f"✅ Model '{model_qr_name}' would be added (Supabase not configured)")
                    except Exception as e:
                        if "duplicate key value violates unique constraint" in str(e):
                            st.error(f"❌ Error: QR Name '{model_qr_name}' already exists. Please choose a unique name.")
                        else:
                            st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ QR Name and Description are required.")
        
        with tab_analytics:
            st.markdown("### � Model Performance Analytics")
            
            if not models_df.empty:
                # Model popularity chart
                events_df = fetch_model_events(limit=500)
                if not events_df.empty:
                    # Extract model names from events
                    model_scan_counts = {}
                    for _, event in events_df.iterrows():
                        if event.get('models') and isinstance(event['models'], dict):
                            model_name = event['models'].get('qr_name', 'Unknown')
                            model_scan_counts[model_name] = model_scan_counts.get(model_name, 0) + 1
                    
                    if model_scan_counts:
                        col_chart1, col_chart2 = st.columns(2)
                        
                        with col_chart1:
                            # Most popular models
                            fig = px.bar(
                                x=list(model_scan_counts.keys()),
                                y=list(model_scan_counts.values()),
                                labels={'x': 'Model QR Name', 'y': 'Number of Scans'},
                                title="📱 Most Scanned Models",
                                color=list(model_scan_counts.values()),
                                color_continuous_scale='Blues'
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_chart2:
                            # Session duration analysis
                            sessions_df = fetch_view_sessions(limit=200)
                            if not sessions_df.empty and 'duration_seconds' in sessions_df.columns:
                                # Filter out null durations
                                valid_sessions = sessions_df.dropna(subset=['duration_seconds'])
                                if not valid_sessions.empty:
                                    fig = px.histogram(
                                        valid_sessions,
                                        x='duration_seconds',
                                        nbins=20,
                                        title="⏱️ Session Duration Distribution",
                                        labels={'duration_seconds': 'Duration (seconds)', 'count': 'Number of Sessions'}
                                    )
                                    fig.update_layout(height=400)
                                    st.plotly_chart(fig, use_container_width=True)
                
                # Time-based analysis
                st.markdown("#### 📅 Activity Over Time")
                if not events_df.empty:
                    # Group events by date
                    events_df['date'] = pd.to_datetime(events_df['created_at']).dt.date
                    daily_scans = events_df.groupby('date').size().reset_index(name='scans')
                    
                    fig = px.line(
                        daily_scans,
                        x='date',
                        y='scans',
                        title="📈 Daily Model Scan Activity",
                        labels={'date': 'Date', 'scans': 'Number of Scans'}
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("📊 No analytics available - add some models and generate activity first!")
        
        with tab_remove:
            st.markdown("### 🗑️ Remove Digital Models")
            if not models_df.empty:
                model_to_remove = st.selectbox(
                    "Select Model to Remove", 
                    models_df["qr_name"].tolist(),
                    help="⚠️ This will also remove all associated events and sessions"
                )
                
                if model_to_remove:
                    # Show details of selected model
                    selected_model = models_df[models_df["qr_name"] == model_to_remove].iloc[0]
                    st.write(f"**Description:** {selected_model.get('description', 'N/A')}")
                    st.write(f"**Scale Factor:** {selected_model.get('scale_factor', 1.0)}x")
                    
                    # Show impact of removal
                    model_id = selected_model['id']
                    model_events_count = len(fetch_model_events(model_id=model_id))
                    model_sessions_count = len(fetch_view_sessions(model_id=model_id))
                    
                    if model_events_count > 0 or model_sessions_count > 0:
                        st.warning(f"⚠️ This model has {model_events_count} scan events and {model_sessions_count} view sessions that will also be removed.")
                    
                    remove_submit = st.button("🗑️ Remove Selected Model", type="primary")
                    
                    if remove_submit:
                        try:
                            if supabase:
                                result = supabase.table("models").delete().eq("qr_name", model_to_remove).execute()
                                if result.data:
                                    st.success(f"✅ Model '{model_to_remove}' and all associated data removed successfully!")
                                    st.rerun()  # Refresh the page
                                else:
                                    st.error(f"❌ Failed to remove model: {result}")
                            else:
                                st.success(f"✅ Model '{model_to_remove}' would be removed (Supabase not configured)")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            else:
                st.info("📋 No models available to remove.")

    # --- User Management Tab ---
    with tab4:
        st.markdown('<div class="tab-header">👨‍💼 User Management Portal</div>', unsafe_allow_html=True)
        
        st.markdown("#### ➕ Create New Admin Account")
        st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
        
        with st.form("add_admin_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_username = st.text_input("👤 Username", placeholder="admin_user")
            with col2:
                new_email = st.text_input("📧 Email Address", placeholder="user@example.com")
            with col3:
                new_password = st.text_input("🔒 Password", type="password", placeholder="Enter secure password")
            
            new_role = st.selectbox("🎭 Role", ["admin", "manager", "analyst"], index=0)
            add_admin_submit = st.form_submit_button("🚀 Create Admin Account", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if add_admin_submit:
            if new_username and new_email and new_password:
                result = create_admin_account(new_username, new_password, new_email, new_role)
                if result.get("success"):
                    st.success(f"✅ Admin account '{new_username}' created successfully!")
                    st.rerun()  # Refresh to show new user in the list
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error occurred')}")
            else:
                st.error("❌ All fields are required.")
        
        st.markdown("---")
        
        # Current admin users from database
        st.markdown("#### 👥 Current Admin Users")
        try:
            if supabase:
                # Fetch all admin users from the database
                response = supabase.table("admin_users").select(
                    "id, username, email, role, created_at, last_login"
                ).execute()
                
                if response.data:
                    users_df = pd.DataFrame(response.data)
                    # Format the datetime columns for better display
                    if 'created_at' in users_df.columns:
                        users_df['created_at'] = pd.to_datetime(users_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                    if 'last_login' in users_df.columns:
                        users_df['last_login'] = pd.to_datetime(users_df['last_login'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
                        users_df['last_login'] = users_df['last_login'].fillna('Never')
                    
                    # Rename columns for display
                    display_columns = {
                        'id': 'ID',
                        'username': 'Username', 
                        'email': 'Email',
                        'role': 'Role',
                        'created_at': 'Created At',
                        'last_login': 'Last Login'
                    }
                    users_df = users_df.rename(columns=display_columns)
                    
                    st.dataframe(users_df, use_container_width=True, hide_index=True)
                    st.success(f"📊 Found {len(users_df)} admin user(s) in the database")
                else:
                    st.info("� No admin users found in the database. Create the first admin account above.")
            else:
                st.warning("⚠️ Database connection not available. Cannot display current users.")
        except Exception as e:
            st.error(f"❌ Error loading users: {str(e)}")
            st.info("💡 Make sure the admin_users table exists in your database.")