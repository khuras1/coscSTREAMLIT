
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
import os

# --- Supabase client initialization (must be before any function that uses it) ---
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
except ImportError:
    st.warning("Supabase client not installed. Data features will not work.")
except Exception as e:
    st.warning(f"Supabase client initialization failed: {e}")

st.set_page_config(layout="wide", page_title="Museum Dashboard")

# --- Admin login system ---
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False



def send_password_reset(email):
    try:
        result = supabase.auth.reset_password_for_email(email)
        return result
    except Exception as e:
        return {"error": str(e)}

def login_form():
    st.markdown("## Admin Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Login")
        register_clicked = st.form_submit_button("Register New Admin")
        forgot_clicked = st.form_submit_button("Forgot Password?")
        if submitted:
            # Check admin credentials from Supabase table
            if not (username and password):
                st.error("Username and password required.")
            else:
                try:
                    # Query admin_users table for username
                    result = supabase.table("admin_users").select("*").eq("username", username).execute()
                    if result.data and len(result.data) > 0:
                        user = result.data[0]
                        import hashlib
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        if user["password_hash"] == password_hash:
                            st.session_state['admin_logged_in'] = True
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")
                    else:
                        st.error("Invalid credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")
        if register_clicked:
            st.session_state['show_register'] = True
        if forgot_clicked:
            st.session_state['show_forgot'] = True



# Show registration form if requested
if 'show_register' not in st.session_state:
    st.session_state['show_register'] = False

if 'show_forgot' not in st.session_state:
    st.session_state['show_forgot'] = False

if not st.session_state['admin_logged_in']:
    login_form()
    if st.session_state['show_register']:
        with st.form("register_admin_from_login"):
            new_username = st.text_input("New Username", key="reg_user_login")
            new_email = st.text_input("Email", key="reg_email_login")
            new_password = st.text_input("Password", type="password", key="reg_pass_login")
            new_role = st.selectbox("Role", ["admin", "superadmin"], key="reg_role_login")
            reg_submit = st.form_submit_button("Register Admin")
            if reg_submit:
                if not (new_username and new_email and new_password):
                    st.error("All fields are required.")
                else:
                    import hashlib
                    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                    try:
                        result = supabase.table("admin_users").insert({
                            "username": new_username,
                            "email": new_email,
                            "password_hash": password_hash,
                            "role": new_role
                        }).execute()
                        if result.data:
                            st.success(f"Admin account '{new_username}' created successfully! You can now log in.")
                            st.session_state['show_register'] = False
                        else:
                            st.error(f"Failed to create admin account: {result}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        st.stop()
    elif st.session_state['show_forgot']:
        with st.form("forgot_password_form"):
            forgot_email = st.text_input("Enter your email for password reset", key="forgot_email")
            forgot_submit = st.form_submit_button("Send Reset Email")
            if forgot_submit:
                if not forgot_email:
                    st.error("Email is required.")
                else:
                    result = send_password_reset(forgot_email)
                    if hasattr(result, 'user') or (hasattr(result, 'data') and result.data):
                        st.success("Password reset email sent! Check your inbox.")
                        st.session_state['show_forgot'] = False
                    elif hasattr(result, 'error') and result.error:
                        st.error(f"Error: {result.error}")
                    elif isinstance(result, dict) and result.get("error"):
                        st.error(f"Error: {result['error']}")
                    else:
                        st.info(f"Result: {result}")
        st.stop()
    else:
        st.stop()
# --- End login system ---

@st.cache_data(show_spinner=False)
def fetch_table(table_name):
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table(table_name).select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # parse dates if present
            for col in df.columns:
                if 'date' in col or 'at' in col or 'time' in col:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except Exception:
                        pass
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching {table_name}: {e}")
        return pd.DataFrame()

models = fetch_table("models")
environment = fetch_table("environment_conditions")
daily = fetch_table("daily_metrics")
visitors = fetch_table("visitor_profiles")
sessions = fetch_table("model_view_sessions")
events = fetch_table("model_events")
context = fetch_table("session_context")


# --- Example dashboard content ---
st.title("Museum Dashboard")
st.write("Welcome, admin!")

# Add a refresh button to reload data
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- Visualizations for each table ---

## 1️⃣ Admin Users
if not fetch_table("admin_users").empty:
    admin_users = fetch_table("admin_users")
    st.subheader("Admin Users")
    st.dataframe(admin_users)
    st.bar_chart(admin_users["role"].value_counts())
else:
    st.info("No admin user data available.")

## 2️⃣ Models
if not models.empty:
    st.subheader("Models Table")
    st.dataframe(models)
    st.bar_chart(models["scale_factor"])
else:
    st.info("No model data available.")

## 3️⃣ Environment Conditions
if not environment.empty:
    st.subheader("Environment Conditions")
    st.dataframe(environment)
    if "temperature_c" in environment.columns:
        st.line_chart(environment.sort_values("recorded_at")["temperature_c"])
else:
    st.info("No environment data available.")

## 4️⃣ Visitor Profiles
if not visitors.empty:
    st.subheader("Visitor Profiles")
    st.dataframe(visitors)
    if "age_group" in visitors.columns:
        st.bar_chart(visitors["age_group"].value_counts())
else:
    st.info("No visitor profile data available.")

## 5️⃣ Model Events
if not events.empty:
    st.subheader("Model Events")
    st.dataframe(events)
    if "event_type" in events.columns:
        st.bar_chart(events["event_type"].value_counts())
else:
    st.info("No model event data available.")

## 6️⃣ Model View Sessions
if not sessions.empty:
    st.subheader("Model View Sessions")
    st.dataframe(sessions)
    if "duration_seconds" in sessions.columns:
        st.line_chart(sessions["duration_seconds"])
else:
    st.info("No model view session data available.")

## 7️⃣ Daily Metrics
if not daily.empty:
    st.subheader("Daily Metrics")
    st.dataframe(daily)
    if "total_visitors" in daily.columns and "date" in daily.columns:
        st.line_chart(daily.set_index("date")["total_visitors"])
else:
    st.info("No daily metrics data available.")

## 8️⃣ Session Context
if not context.empty:
    st.subheader("Session Context")
    st.dataframe(context)
else:
    st.info("No session context data available.")

# --- Admin Registration (Create Account) ---
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()



# --- Artifact Management Interface ---
with st.expander("Manage Artifacts (Add/Remove)"):
    tab_add, tab_remove = st.tabs(["Add Artifact", "Remove Artifact"])

    with tab_add:
        with st.form("add_artifact_form"):
            artifact_name = st.text_input("Artifact Name", key="artifact_name")
            artifact_desc = st.text_area("Description", key="artifact_desc")
            artifact_date = st.date_input("Date Acquired", key="artifact_date")
            artifact_type = st.text_input("Type", key="artifact_type")
            add_submit = st.form_submit_button("Add Artifact")
            if add_submit:
                if not (artifact_name and artifact_desc and artifact_date and artifact_type):
                    st.error("All fields are required.")
                else:
                    try:
                        result = supabase.table("artifacts").insert({
                            "name": artifact_name,
                            "description": artifact_desc,
                            "date_acquired": str(artifact_date),
                            "type": artifact_type
                        }).execute()
                        if result.data:
                            st.success(f"Artifact '{artifact_name}' added successfully!")
                        else:
                            st.error(f"Failed to add artifact: {result}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab_remove:
        artifacts_df = fetch_table("artifacts")
        if not artifacts_df.empty:
            artifact_to_remove = st.selectbox("Select Artifact to Remove", artifacts_df["name"].tolist(), key="remove_artifact")
            remove_submit = st.button("Remove Selected Artifact")
            if remove_submit and artifact_to_remove:
                try:
                    result = supabase.table("artifacts").delete().eq("name", artifact_to_remove).execute()
                    if result.data:
                        st.success(f"Artifact '{artifact_to_remove}' removed successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to remove artifact: {result}")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No artifacts available to remove.")

# --- Supabase User Management (Admin Add & User Login) ---
def add_user(email, password, email_confirm=True):
    """Create a new user using Supabase admin API (backend only)."""
    try:
        result = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": email_confirm
        })
        return result
    except Exception as e:
        return {"error": str(e)}

def login_user(email, password):
    """Login a user using Supabase regular auth (frontend safe)."""
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return result
    except Exception as e:
        return {"error": str(e)}

with st.expander("User Management (Supabase Demo)"):
    st.markdown("#### Add User (Admin Only)")
    with st.form("add_user_form"):
        user_email = st.text_input("User Email", key="add_user_email")
        user_password = st.text_input("User Password", type="password", key="add_user_pass")
        add_user_submit = st.form_submit_button("Add User")
        if add_user_submit:
            if not (user_email and user_password):
                st.error("Email and password required.")
            else:
                result = add_user(user_email, user_password)
                if hasattr(result, 'user') and result.user:
                    st.success(f"User '{user_email}' created successfully!")
                elif hasattr(result, 'error') and result.error:
                    st.error(f"Error: {result.error}")
                elif isinstance(result, dict) and result.get("error"):
                    st.error(f"Error: {result['error']}")
                else:
                    st.info(f"Result: {result}")

    st.markdown("#### User Login (Regular Auth)")
    with st.form("login_user_form"):
        login_email = st.text_input("Login Email", key="login_user_email")
        login_password = st.text_input("Login Password", type="password", key="login_user_pass")
        login_user_submit = st.form_submit_button("Login User")
        if login_user_submit:
            if not (login_email and login_password):
                st.error("Email and password required.")
            else:
                result = login_user(login_email, login_password)
                if hasattr(result, 'session') and result.session:
                    st.success(f"User '{login_email}' logged in successfully!")
                elif hasattr(result, 'error') and result.error:
                    st.error(f"Error: {result.error}")
                elif isinstance(result, dict) and result.get("error"):
                    st.error(f"Error: {result['error']}")
                else:
                    st.info(f"Result: {result}")