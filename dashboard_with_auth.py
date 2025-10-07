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

# Authentication functions
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    # Demo credentials - in production, use database
    demo_users = {
        "admin": hash_password("admin123"),
        "manager": hash_password("manager123"),
        "analyst": hash_password("analyst123")
    }
    
    if username in demo_users:
        return demo_users[username] == hash_password(password)
    return False

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

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
        .login-form {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .demo-credentials {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            color: white;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                🏛️ Museum Dashboard
            </div>
            <div class="demo-credentials">
                <strong>📋 Demo Credentials:</strong><br>
                👤 admin / admin123<br>
                👤 manager / manager123<br>
                👤 analyst / analyst123
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="login-form">', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### 🔐 Please Login to Continue")
            
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col_login, col_reset = st.columns([2, 1])
            
            with col_login:
                login_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            with col_reset:
                if st.form_submit_button("🔄 Reset", use_container_width=True):
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

    # --- Prediction Tab ---
    with tab1:
        st.markdown('<div class="tab-header">🔮 AI-Powered Predictions</div>', unsafe_allow_html=True)
        
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
                    categorical_options = {
                        'env_condition': ["☁️ Cloudy", "☀️ Sunny", "🌧️ Rainy", "💨 Windy", "🌫️ Other"],
                        'env_season': ["🌸 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"],
                        'visitor_age_group': ["👶 Teen", "👨 Adult", "👴 Senior", "🧒 Child"],
                        'event_event_type': ["📱 Scan", "🔄 Other"],
                    }
                    
                    st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
                    
                    with st.form("prediction_form"):
                        st.markdown("### 📊 Input Parameters")
                        
                        # Organize inputs in columns
                        col_left, col_right = st.columns(2)
                        
                        user_inputs = {}
                        left_features = feature_names[:len(feature_names)//2]
                        right_features = feature_names[len(feature_names)//2:]
                        
                        with col_left:
                            for feature in left_features:
                                label = "🏷️ " + feature.replace('_', ' ').title()
                                if feature in categorical_options:
                                    user_inputs[feature] = st.selectbox(label, categorical_options[feature], key=f"left_{feature}")
                                    user_inputs[feature] = user_inputs[feature].split(' ', 1)[1] if ' ' in user_inputs[feature] else user_inputs[feature]
                                elif feature in ['visitor_preferred_language', 'visitor_country']:
                                    user_inputs[feature] = st.text_input(label, placeholder=f"Enter {feature.replace('_', ' ')}...", key=f"left_{feature}")
                                else:
                                    user_inputs[feature] = st.number_input(label, min_value=0.0, key=f"left_{feature}")
                        
                        with col_right:
                            for feature in right_features:
                                label = "🏷️ " + feature.replace('_', ' ').title()
                                if feature in categorical_options:
                                    user_inputs[feature] = st.selectbox(label, categorical_options[feature], key=f"right_{feature}")
                                    user_inputs[feature] = user_inputs[feature].split(' ', 1)[1] if ' ' in user_inputs[feature] else user_inputs[feature]
                                elif feature in ['visitor_preferred_language', 'visitor_country']:
                                    user_inputs[feature] = st.text_input(label, placeholder=f"Enter {feature.replace('_', ' ')}...", key=f"right_{feature}")
                                else:
                                    user_inputs[feature] = st.number_input(label, min_value=0.0, key=f"right_{feature}")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        submit = st.form_submit_button("🚀 Generate Prediction", use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if submit:
                        with st.spinner("🔄 Processing prediction..."):
                            input_data = pd.DataFrame({k: [v] for k, v in user_inputs.items()})
                            try:
                                prediction = loaded_pipeline.predict(input_data)
                                
                                # Modern result display with rounded customer count
                                predicted_customers = round(prediction[0])
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
                                    🎯 Predicted Customers: <span style="font-size: 2rem; font-weight: 800;">{predicted_customers}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Additional insights
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("🧮 Exact Value", f"{prediction[0]:.3f}", help="Raw model output before rounding")
                                with col2:
                                    st.metric("👥 Expected Visitors", f"{predicted_customers}", help="Rounded to whole number")
                                with col3:
                                    confidence_level = "High" if abs(prediction[0] - predicted_customers) < 0.1 else "Medium"
                                    st.metric("📊 Confidence", confidence_level, help="Based on rounding difference")
                                
                            except Exception as e:
                                st.error(f"❌ Prediction Error: {e}")
                                st.info("💡 Please verify all input parameters are correctly formatted.")
                except Exception as e:
                    st.error(f"❌ Form Generation Error: {e}")
            else:
                st.warning("⚠️ ML Pipeline not available. Please check system configuration.")

    # --- Admin Visualization Tab ---
    with tab2:
        st.markdown('<div class="tab-header">📊 Advanced Analytics Dashboard</div>', unsafe_allow_html=True)
        
        # Modern metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>👥 Total Visitors</h3>
                <h2>12,458</h2>
                <p>↗️ +23% from last month</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 Engagement Rate</h3>
                <h2>87.3%</h2>
                <p>↗️ +5.2% from last week</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>⏱️ Avg. Duration</h3>
                <h2>45m</h2>
                <p>↘️ -2m from last month</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>🏆 Satisfaction</h3>
                <h2>4.8/5</h2>
                <p>↗️ +0.3 from last quarter</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Sample interactive charts
        st.markdown("#### 📈 Sample Analytics (Demo Data)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample visitor trends
            dates = pd.date_range('2024-01-01', periods=30, freq='D')
            visitors = [100 + i*2 + (i%7)*10 for i in range(30)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=visitors,
                mode='lines+markers',
                name='Daily Visitors',
                line=dict(color='#667eea', width=3),
                marker=dict(size=6, color='#764ba2')
            ))
            
            fig.update_layout(
                title="Daily Visitor Trends",
                xaxis_title="Date",
                yaxis_title="Number of Visitors",
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sample age distribution
            age_data = pd.DataFrame({
                'Age Group': ['Child', 'Teen', 'Adult', 'Senior'],
                'Count': [150, 280, 450, 120]
            })
            
            fig = px.pie(age_data, values='Count', names='Age Group',
                        color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                        title="Visitor Age Distribution")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # --- Artifact Management Tab ---
    with tab3:
        st.markdown('<div class="tab-header">🏛️ Artifact Collection Manager</div>', unsafe_allow_html=True)
        
        tab_add, tab_remove = st.tabs(["➕ Add New Artifact", "🗑️ Remove Artifact"])
        
        with tab_add:
            st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
            with st.form("add_artifact_form"):
                st.markdown("### 🏛️ New Artifact Registration")
                
                col1, col2 = st.columns(2)
                with col1:
                    artifact_name = st.text_input("🏷️ Artifact Name", placeholder="Enter artifact name...")
                    artifact_type = st.text_input("📋 Artifact Type", placeholder="e.g., Painting, Sculpture, Manuscript...")
                
                with col2:
                    artifact_date = st.date_input("📅 Date Acquired")
                
                artifact_desc = st.text_area("📝 Description", placeholder="Provide detailed description of the artifact...", height=100)
                
                add_submit = st.form_submit_button("✨ Register Artifact", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if add_submit:
                if artifact_name and artifact_desc and artifact_date and artifact_type:
                    try:
                        if supabase:
                            result = supabase.table("artifacts").insert({
                                "name": artifact_name,
                                "description": artifact_desc,
                                "date_acquired": str(artifact_date),
                                "type": artifact_type
                            }).execute()
                            if result.data:
                                st.success(f"✅ Artifact '{artifact_name}' added successfully!")
                            else:
                                st.error(f"❌ Failed to add artifact: {result}")
                        else:
                            st.success(f"✅ Artifact '{artifact_name}' would be added (Supabase not configured)")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ All fields are required.")
        
        with tab_remove:
            st.markdown("### 🗑️ Remove Existing Artifacts")
            if supabase:
                try:
                    artifacts_data = supabase.table("artifacts").select('*').execute().data
                    if artifacts_data:
                        artifacts_df = pd.DataFrame(artifacts_data)
                        artifact_to_remove = st.selectbox("Select Artifact to Remove", artifacts_df["name"].tolist())
                        remove_submit = st.button("🗑️ Remove Selected Artifact", type="primary")
                        
                        if remove_submit and artifact_to_remove:
                            try:
                                result = supabase.table("artifacts").delete().eq("name", artifact_to_remove).execute()
                                if result.data:
                                    st.success(f"✅ Artifact '{artifact_to_remove}' removed successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to remove artifact: {result}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    else:
                        st.info("📋 No artifacts available to remove.")
                except Exception as e:
                    st.error(f"❌ Error fetching artifacts: {e}")
            else:
                st.info("⚠️ Supabase not configured. Cannot manage artifacts.")

    # --- User Management Tab ---
    with tab4:
        st.markdown('<div class="tab-header">👨‍💼 User Management Portal</div>', unsafe_allow_html=True)
        
        def add_user_supabase(email, password, email_confirm=True):
            try:
                if supabase:
                    result = supabase.auth.admin.create_user({
                        "email": email,
                        "password": password,
                        "email_confirm": email_confirm
                    })
                    return result
                else:
                    return {"success": f"User {email} would be created (Supabase not configured)"}
            except Exception as e:
                return {"error": str(e)}

        st.markdown("#### ➕ Create New User Account")
        st.markdown('<div class="prediction-form">', unsafe_allow_html=True)
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                user_email = st.text_input("📧 Email Address", placeholder="user@example.com")
            with col2:
                user_password = st.text_input("🔒 Password", type="password", placeholder="Enter secure password")
            add_user_submit = st.form_submit_button("🚀 Create User Account", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if add_user_submit:
            if user_email and user_password:
                result = add_user_supabase(user_email, user_password)
                if hasattr(result, 'user') and result.user:
                    st.success(f"✅ User '{user_email}' created successfully!")
                elif hasattr(result, 'error') and result.error:
                    st.error(f"❌ Error: {result.error}")
                elif isinstance(result, dict) and result.get("error"):
                    st.error(f"❌ Error: {result['error']}")
                elif isinstance(result, dict) and result.get("success"):
                    st.success(result["success"])
                else:
                    st.info(f"ℹ️ Result: {result}")
            else:
                st.error("❌ Email and password are required.")
        
        st.markdown("---")
        
        # Demo user list
        st.markdown("#### 👥 Current Demo Users")
        demo_users_df = pd.DataFrame({
            'Username': ['admin', 'manager', 'analyst'],
            'Password': ['admin123', 'manager123', 'analyst123'],
            'Role': ['Administrator', 'Manager', 'Data Analyst'],
            'Status': ['Active', 'Active', 'Active']
        })
        
        st.dataframe(demo_users_df, use_container_width=True, hide_index=True)
        st.info("💡 These are demo credentials for testing the authentication system.")