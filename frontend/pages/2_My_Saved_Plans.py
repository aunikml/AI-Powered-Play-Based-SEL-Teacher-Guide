import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="My Saved Plans")
BACKEND_URL = "http://127.0.0.1:5001"

# --- SESSION STATE & API SESSION ---
# Ensure the authenticated session object is available.
if 'api_session' not in st.session_state:
    st.session_state.api_session = requests.Session()

def logout_user():
    st.session_state.api_session.post(f"{BACKEND_URL}/api/logout")
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.switch_page("app.py")

# ==============================================================================
# ===                      SECURITY GUARD                                    ===
# ==============================================================================
if not st.session_state.get('logged_in', False):
    st.warning("Please log in to access this page.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

# ==============================================================================
# ===                        SAVED PLANS UI                                  ===
# ==============================================================================

# --- Top Bar with Title and Logout Button ---
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    st.page_link("app.py", label="⬅️ Back to Chatbot", icon="💬")
with col2:
    st.title("📚 My Saved Plans")
with col3:
    if st.button("Logout", use_container_width=True):
        logout_user()
st.markdown("---")

# --- Function to fetch plans from the backend (CORRECTED) ---
@st.cache_data(ttl=60) # Cache the results for 60 seconds
def fetch_plans():
    """
    Makes a GET request to the /api/my-plans endpoint.
    It no longer needs a user_id argument. The backend identifies the user
    from the session cookie sent automatically by st.session_state.api_session.
    """
    try:
        # The URL is now correct and does not include a user ID.
        response = st.session_state.api_session.get(f"{BACKEND_URL}/api/my-plans")
        if response.status_code == 200:
            return response.json()
        else:
            # This is the error you were seeing.
            st.error(f"Failed to fetch plans. Server responded with {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the backend server.")
        return []

# --- Main Page Logic ---
# The call to fetch_plans is now simpler.
saved_plans = fetch_plans()

if not saved_plans:
    st.info("You haven't saved any plans yet. Go back to the chatbot to create one!")
else:
    st.subheader(f"You have {len(saved_plans)} saved plans.")

    # Loop through each plan and display it in an expander
    for plan in saved_plans:
        try:
            plan_date = datetime.strptime(plan['created_at'], '%Y-%m-%d %H:%M').strftime('%B %d, %Y')
            expander_title = f"**{plan['title']}** (Age: {plan['age_cohort']}, Subject: {plan['subject']}) - Saved on {plan_date}"
        except:
            expander_title = plan.get('title', 'Untitled Plan')


        with st.expander(expander_title):
            # Display the content as Markdown, which is how it's saved
            st.markdown(plan['content'])
            
            st.markdown("---")
            
            # --- Action Buttons ---
            if st.button("🗑️ Delete Plan", key=f"delete_{plan['id']}", type="primary"):
                try:
                    delete_response = st.session_state.api_session.delete(f"{BACKEND_URL}/api/plans/{plan['id']}")
                    if delete_response.status_code == 200:
                        st.toast(f"Plan '{plan['title']}' was deleted.")
                        st.cache_data.clear() # Clear the cache
                        st.rerun() # Rerun the script to refresh the list
                    else:
                        st.error(f"Failed to delete plan: {delete_response.json().get('message')}")
                except requests.exceptions.ConnectionError:
                    st.error("Connection error while trying to delete.")