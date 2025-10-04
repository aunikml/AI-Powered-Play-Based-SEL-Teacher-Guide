import streamlit as st
import requests
import datetime
import random

# --- CONFIGURATION & STATIC DATA ---
st.set_page_config(page_title="LTP Guide Bot", page_icon="🎓", layout="centered")
BACKEND_URL = "http://127.0.0.1:5001"

QUOTES = [
    ("The goal of early childhood education should be to activate the child's own natural desire to learn.", "Maria Montessori"),
    ("Play is the highest form of research.", "Albert Einstein"),
    ("Children learn as they play. Most importantly, in play children learn how to learn.", "O. Fred Donaldson"),
]

# --- SESSION STATE INITIALIZATION ---
if 'api_session' not in st.session_state: st.session_state.api_session = requests.Session()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'stage' not in st.session_state: st.session_state.stage = 'start'
if 'selections' not in st.session_state: st.session_state.selections = {}
if 'generated_guide' not in st.session_state: st.session_state.generated_guide = None # Will store dict OR edited string
if 'editing_mode' not in st.session_state: st.session_state.editing_mode = False
if 'chatbot_options' not in st.session_state: st.session_state.chatbot_options = None
if 'admin_data' not in st.session_state: st.session_state.admin_data = {}

# --- API HELPER FUNCTIONS ---
def register_user(first_name, last_name, email, city, country):
    payload = {"first_name": first_name, "last_name": last_name, "email": email, "city": city, "country": country}
    return requests.post(f"{BACKEND_URL}/api/register", json=payload)
def login_user(email, password):
    payload = {"email": email, "password": password}
    return st.session_state.api_session.post(f"{BACKEND_URL}/api/login", json=payload)
def change_password(new_password):
    payload = {"new_password": new_password}
    return st.session_state.api_session.post(f"{BACKEND_URL}/api/change-password", json=payload)
def logout_user():
    st.session_state.api_session.post(f"{BACKEND_URL}/api/logout")
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
def get_chatbot_options():
    try:
        response = st.session_state.api_session.get(f"{BACKEND_URL}/api/chatbot/options")
        if response.status_code == 200: return response.json()
        else: return None
    except Exception as e:
        print(f"Error fetching chatbot options: {e}"); return None
def generate_plan(age_cohort, subject, sub_domain, play_type_obj):
    payload = {"age_cohort": age_cohort, "subject": subject, "sub_domain": sub_domain, "play_type": play_type_obj}
    return st.session_state.api_session.post(f"{BACKEND_URL}/api/generate-plan", json=payload)
def save_plan(title, content, age_cohort, subject, play_type_name):
    payload = {"title": title, "content": content, "age_cohort": age_cohort, "subject": subject, "play_type": play_type_name}
    return st.session_state.api_session.post(f"{BACKEND_URL}/api/my-plans", json=payload)
def get_admin_data(endpoint):
    if endpoint not in st.session_state.admin_data:
        try:
            response = st.session_state.api_session.get(f"{BACKEND_URL}/api/admin/{endpoint}")
            st.session_state.admin_data[endpoint] = response.json() if response.status_code == 200 else []
        except: st.session_state.admin_data[endpoint] = []
    return st.session_state.admin_data[endpoint]
def handle_api_error(response, context="An unknown error occurred."):
    st.error(f"{context}: Server returned status {response.status_code}")
def submit_feedback(rating, selections, generated_guide):
    payload = {"rating": rating, "selections": selections, "generated_output": generated_guide}
    try:
        response = st.session_state.api_session.post(f"{BACKEND_URL}/api/feedback", json=payload)
        if response.status_code == 201: st.toast("Thank you for your feedback!", icon="👍")
        else: st.toast("Could not submit feedback.", icon="⚠️")
    except:
        st.toast("Failed to connect for feedback.", icon="🔥")

# --- BOT & RENDER HELPER FUNCTIONS ---
def add_bot_message(message, options=None, is_final_plan=False):
    st.session_state.chat_history.append({"role": "assistant", "content": message, "options": options, "is_final_plan": is_final_plan})
def add_user_message(message):
    st.session_state.chat_history.append({"role": "user", "content": message})
def reset_conversation():
    st.session_state.stage = 'start'; st.session_state.selections = {}; st.session_state.chat_history = []
    st.session_state.generated_guide = None; st.session_state.editing_mode = False
    st.rerun()
def convert_guide_to_markdown(guide_data, selections):
    if not isinstance(guide_data, dict): return "Error: Guide data is not in the correct format."
    s = selections
    parts = [f"### {guide_data.get('guide_title', 'Untitled Plan')}",
        f"**Age Cohort:** {s.get('age')} | **Domain:** {s.get('domain')} | **Component:** {s.get('sub_domain')}",
        f"**Play Type:** {s.get('play_type', {}).get('name')} | **Context:** {s.get('play_type', {}).get('context')}",
        "\n---", "### Learning Outcomes", "**Cognitive:**"]
    parts.extend([f"- {item}" for item in guide_data.get('cognitive_outcomes', [])])
    parts.append("\n**Socio-Emotional:**"); parts.extend([f"- {item}" for item in guide_data.get('socio_emotional_outcomes', [])])
    parts.extend(["\n---", "### Activities", f"**{guide_data.get('activity_name', '')}**", guide_data.get('activity_description', ''), "\n---", "### Recommended Content from Oak API"])
    parts.extend([f"- {item}" for item in guide_data.get('recommended_oak_content', [])])
    parts.extend(["\n---", "### Step-by-Step Facilitation Guidance", f"**Setup:** {guide_data.get('setup_guidance', '')}", f"**Introduction:** {guide_data.get('introduction_guidance', '')}", f"**During Play (Facilitation):** {guide_data.get('during_play_guidance', '')}", f"**Conclusion/Reflection:** {guide_data.get('conclusion_guidance', '')}", "\n---", "### Materials"])
    parts.extend([f"- {item}" for item in guide_data.get('materials', [])])
    parts.extend(["\n---", "### Assessment Matrix and Rubric", guide_data.get('assessment_rubric', 'No rubric generated.')])
    return "\n\n".join(parts)
def render_structured_guide(guide_data):
    if not isinstance(guide_data, dict):
        st.error("Could not render guide. The data is not in the expected format."); return
    st.markdown(f"### {guide_data.get('guide_title', 'Untitled Plan')}"); st.markdown("---")
    st.subheader("Learning Outcomes"); st.markdown("**Cognitive:**")
    for item in guide_data.get('cognitive_outcomes', []): st.markdown(f"- {item}")
    st.markdown("**Socio-Emotional:**");
    for item in guide_data.get('socio_emotional_outcomes', []): st.markdown(f"- {item}")
    st.markdown("---"); st.subheader("Activities"); st.markdown(f"**{guide_data.get('activity_name', 'N/A')}**"); st.write(guide_data.get('activity_description', '')); st.markdown("---")
    st.subheader("Step-by-Step Facilitation Guidance")
    st.markdown(f"**Setup:** {guide_data.get('setup_guidance', '')}"); st.markdown(f"**Introduction:** {guide_data.get('introduction_guidance', '')}")
    st.markdown(f"**During Play (Facilitation):** {guide_data.get('during_play_guidance', '')}"); st.markdown(f"**Conclusion/Reflection:** {guide_data.get('conclusion_guidance', '')}")
    st.markdown("---"); st.subheader("Materials");
    for item in guide_data.get('materials', []): st.markdown(f"- {item}")
    st.markdown("---"); st.subheader("Assessment Matrix and Rubric"); st.markdown(guide_data.get('assessment_rubric', 'No rubric was generated.'))

# ==============================================================================
# ===                      VIEW 1: LOGIN & REGISTRATION                      ===
# ==============================================================================
if not st.session_state.logged_in:
    st.title("Welcome to the Learning Through Play Guide 🍎"); st.markdown("Please log in or register to access your personal learning plan assistant.")
    login_tab, register_tab = st.tabs(["**Login**", "**Register**"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email"); password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if not email or not password: st.error("Please enter both email and password.")
                else:
                    try:
                        response = login_user(email, password)
                        if response.status_code == 200:
                            user_data = response.json().get('user')
                            st.session_state.logged_in = True; st.session_state.user_info = user_data
                            if user_data and user_data.get('role') == 'admin':
                                st.switch_page("pages/1_Admin_Panel.py")
                            else: st.rerun()
                        else: handle_api_error(response, "Login Failed")
                    except requests.exceptions.ConnectionError: st.error("Connection Error: Is the backend running?")
    with register_tab:
        with st.form("register_form"):
            st.subheader("Create a New Account"); col1, col2 = st.columns(2)
            with col1: first_name = st.text_input("First Name"); email = st.text_input("Email"); city = st.text_input("City")
            with col2: last_name = st.text_input("Last Name"); country = st.text_input("Country")
            if st.form_submit_button("Register"):
                if not all([first_name, last_name, email, city, country]): st.error("Please fill out all fields.")
                else:
                    try:
                        response = register_user(first_name, last_name, email, city, country)
                        if response.status_code == 201:
                            temp_pw = response.json().get("temporary_password")
                            st.success(f"Registration successful! Your temporary password is: **{temp_pw}**"); st.info("Please go to the Login tab to continue.")
                        else: handle_api_error(response, "Registration Failed")
                    except requests.exceptions.ConnectionError: st.error("Connection Error: Is the backend running?")

# ==============================================================================
# ===                      VIEW 2: LOGGED-IN USER FLOW                       ===
# ==============================================================================
else:
    if st.session_state.user_info.get('force_password_change', False):
        st.warning("🔒 **Action Required:** Please update your temporary password to secure your account.")
        with st.form("password_change_form"):
            st.subheader("Set Your New Password"); new_password = st.text_input("New Password", type="password"); confirm_password = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Change Password"):
                if not new_password or not confirm_password: st.error("Please fill both password fields.")
                elif len(new_password) < 6: st.error("Password must be at least 6 characters long.")
                elif new_password != confirm_password: st.error("Passwords do not match.")
                else:
                    try:
                        response = change_password(new_password)
                        if response.status_code == 200:
                            st.success("Password updated successfully! Reloading..."); st.session_state.user_info['force_password_change'] = False; st.rerun()
                        else: handle_api_error(response, "Could not update password")
                    except requests.exceptions.ConnectionError: st.error("Connection Error: Is the backend running?")
    else:
        if st.session_state.user_info.get('role') != 'admin':
            st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
        
        if st.session_state.chatbot_options is None:
            with st.spinner("Loading curriculum structure..."):
                st.session_state.chatbot_options = get_chatbot_options()
        if not st.session_state.chatbot_options:
            st.error("Fatal Error: Could not load curriculum structure. Please contact an administrator."); st.stop()
        
        col1, col2 = st.columns([4, 1]); col1.title("🎓 Learning Plan Assistant")
        if col2.button("Logout", use_container_width=True): logout_user()

        if st.session_state.stage == 'start':
            now = datetime.datetime.now(); name = st.session_state.user_info.get('first_name', 'Teacher'); quote, source = random.choice(QUOTES)
            greeting = f"Hello {name}! 👋 Welcome back.\n\nToday is **{now.strftime('%A, %B %d, %Y')}**.\n\n> *“{quote}”*\n> — {source}\n\n"
            add_bot_message(greeting); add_bot_message("What would you like to do today?", options=["Create an Activity Plan", "View My Saved Activities"]); st.session_state.stage = 'awaiting_initial_choice'

        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                if msg.get("is_final_plan"): render_structured_guide(msg["content"])
                else: st.markdown(msg["content"] or "")
                
                if msg.get("options"):
                    is_latest = (i == len(st.session_state.chat_history) - 1)
                    for option in msg["options"]:
                        if st.button(option, key=f"option_{i}_{option}", disabled=not is_latest):
                            add_user_message(option)
                            if st.session_state.stage == 'awaiting_initial_choice':
                                if option == "Create an Activity Plan":
                                    age_cohorts = list(st.session_state.chatbot_options["age_cohorts"].keys()); add_bot_message("Great! First, select an age cohort.", options=age_cohorts); st.session_state.stage = 'awaiting_age'
                                else: st.switch_page("pages/2_My_Saved_Plans.py")
                            elif st.session_state.stage == 'awaiting_age':
                                st.session_state.selections['age'] = option; domains = list(st.session_state.chatbot_options["age_cohorts"][option].keys()); add_bot_message("Now choose a learning domain.", options=domains); st.session_state.stage = 'awaiting_domain'
                            elif st.session_state.stage == 'awaiting_domain':
                                st.session_state.selections['domain'] = option; age = st.session_state.selections['age']; components = st.session_state.chatbot_options["age_cohorts"][age][option]; add_bot_message("Excellent. Which specific component to focus on?", options=components); st.session_state.stage = 'awaiting_sub_domain'
                            elif st.session_state.stage == 'awaiting_sub_domain':
                                st.session_state.selections['sub_domain'] = option; s = st.session_state.selections
                                ac_obj = next((ac for ac in get_admin_data("age-cohorts") if ac['name'] == s['age']), None)
                                d_obj = next((d for d in get_admin_data("domains") if d['name'] == s['domain']), None)
                                if ac_obj and d_obj:
                                    key = f"{ac_obj['id']}-{d_obj['id']}"; valid_play_types = st.session_state.chatbot_options["play_types"].get(key, []); play_type_names = [pt['name'] for pt in valid_play_types]
                                    if play_type_names: add_bot_message("Almost there! Select an available play type.", options=play_type_names); st.session_state.stage = 'awaiting_play_type'
                                    else: add_bot_message("Sorry, no play types are configured for this context. Please contact an admin."); st.session_state.stage = 'error'
                                else: add_bot_message("Error finding play types."); st.session_state.stage = 'error'
                            elif st.session_state.stage == 'awaiting_play_type':
                                s = st.session_state.selections
                                ac_obj = next((ac for ac in get_admin_data("age-cohorts") if ac['name'] == s['age']), None)
                                d_obj = next((d for d in get_admin_data("domains") if d['name'] == s['domain']), None)
                                key = f"{ac_obj['id']}-{d_obj['id']}"; valid_play_types = st.session_state.chatbot_options["play_types"].get(key, [])
                                selected_play_type_obj = next((pt for pt in valid_play_types if pt['name'] == option), None)
                                st.session_state.selections['play_type'] = selected_play_type_obj; add_bot_message("Thank you! Generating your customized plan now..."); st.session_state.stage = 'generating_plan'
                            st.rerun()

                if msg.get("is_final_plan"):
                    guide_dict = msg["content"]; guide_markdown = convert_guide_to_markdown(guide_dict, st.session_state.selections)
                    st.markdown("---")
                    if st.session_state.editing_mode:
                        edited_guide = st.text_area("Editing mode:", value=guide_markdown, height=500)
                        c1, c2, _ = st.columns([1, 1, 5])
                        if c1.button("✅ Save Changes", type="primary"): st.session_state.generated_guide = edited_guide; st.session_state.editing_mode = False; st.success("Changes saved!"); st.rerun()
                        if c2.button("❌ Cancel"): st.session_state.editing_mode = False; st.rerun()
                    else:
                        if st.button("✏️ Edit this plan"): st.session_state.generated_guide = guide_markdown; st.session_state.editing_mode = True; st.rerun()
                    st.markdown("---"); st.subheader("Actions")
                    plan_title = st.text_input("Title to save plan:", value=f"{guide_dict.get('guide_title', 'Plan')}")
                    action_cols = st.columns(3)
                    content_to_save_or_export = st.session_state.generated_guide if isinstance(st.session_state.generated_guide, str) else guide_markdown
                    if action_cols[0].button("💾 Save to My Plans", use_container_width=True, type="primary"):
                        with st.spinner("Saving..."):
                            s = st.session_state.selections; play_type_name = s.get('play_type', {}).get('name', 'N/A')
                            response = save_plan(plan_title, content_to_save_or_export, s['age'], s['domain'], play_type_name)
                            if response.status_code == 201: st.success(f"Plan '{plan_title}' saved!"); st.cache_data.clear()
                            else: handle_api_error(response, "Failed to save plan")
                    action_cols[1].download_button(label="📄 Export as Markdown", data=content_to_save_or_export, file_name=f"{plan_title.replace(' ', '_')}.md", mime="text/markdown", use_container_width=True)
                    if action_cols[2].button("📚 Go to My Saved Plans", use_container_width=True): st.switch_page("pages/2_My_Saved_Plans.py")
                    st.markdown("---")
                    feedback_cols = st.columns(2)
                    if feedback_cols[0].button("👍 Helpful", use_container_width=True): submit_feedback(1, st.session_state.selections, guide_dict)
                    if feedback_cols[1].button("👎 Not Helpful", use_container_width=True): submit_feedback(-1, st.session_state.selections, guide_dict)
                    if st.button("✨ Start New Plan", use_container_width=True, type="secondary"): reset_conversation()

        if st.session_state.stage == 'generating_plan':
            with st.chat_message("assistant"):
                with st.spinner("🧠 Crafting your activity plan..."):
                    s = st.session_state.selections
                    try:
                        response = generate_plan(s['age'], s['domain'], s['sub_domain'], s['play_type'])
                        if response.status_code == 200:
                            plan_json = response.json()
                            if "error" in plan_json: add_bot_message(f"Sorry, an error occurred: {plan_json['error']}")
                            else: st.session_state.generated_guide = plan_json; add_bot_message(plan_json, is_final_plan=True)
                        else: add_bot_message(f"Sorry, the server returned an error (Status: {response.status_code}). Please try again.")
                    except requests.exceptions.ConnectionError:
                        add_bot_message("Sorry, I couldn't connect to the backend server.")
                    st.session_state.stage = 'plan_displayed'
                    st.rerun()