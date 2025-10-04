import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Admin Panel", layout="wide")
BACKEND_URL = "http://127.0.0.1:5001"
if 'api_session' not in st.session_state:
    st.session_state.api_session = requests.Session()
if 'selected_play_type_id' not in st.session_state:
    st.session_state.selected_play_type_id = None

def logout_user():
    st.session_state.api_session.post(f"{BACKEND_URL}/api/logout")
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.switch_page("app.py")

# ==============================================================================
# ===                      SECURITY GUARD                                    ===
# ==============================================================================
if not st.session_state.get('logged_in', False) or st.session_state.user_info.get('role') != 'admin':
    st.warning("Access Denied. Please log in as an administrator."); st.page_link("app.py", label="Go to Login"); st.stop()

# ==============================================================================
# ===                        ADMIN PANEL UI                                  ===
# ==============================================================================
col1, col2 = st.columns([4, 1])
with col1: st.title("👑 Admin Panel")
with col2:
    if st.button("Logout", use_container_width=True): logout_user()
st.markdown("---")

# --- API Functions for Admin Data ---
@st.cache_data(ttl=30)
def get_admin_data(endpoint):
    try:
        response = st.session_state.api_session.get(f"{BACKEND_URL}/api/admin/{endpoint}")
        return response.json() if response.status_code == 200 else []
    except: return []
def add_entry(endpoint, payload):
    res = st.session_state.api_session.post(f"{BACKEND_URL}/api/admin/{endpoint}", json=payload)
    if res.status_code == 201: st.toast("Added!", icon="🎉"); st.cache_data.clear(); st.rerun()
    else: st.error(f"Add failed: {res.text}")
def update_entry(endpoint, entry_id, payload):
    res = st.session_state.api_session.put(f"{BACKEND_URL}/api/admin/{endpoint}/{entry_id}", json=payload)
    if res.status_code == 200: st.toast("Updated!", icon="✅"); st.cache_data.clear(); st.rerun()
    else: st.error(f"Update failed: {res.text}")
def delete_entry(endpoint, entry_id):
    res = st.session_state.api_session.delete(f"{BACKEND_URL}/api/admin/{endpoint}/{entry_id}")
    if res.status_code == 200: st.toast("Deleted!", icon="🗑️"); st.cache_data.clear(); st.rerun()
    else: st.error(f"Delete failed: {res.text}")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 User List", "📊 User Activity", "⚙️ Settings", "🧩 Curriculum Builder", "🧠 Knowledge Base"])

with tab1:
    st.header("User Management")
    st.dataframe(pd.DataFrame(get_admin_data("users")), use_container_width=True, hide_index=True)

with tab2:
    st.header("User Activity Monitor")
    st.dataframe(pd.DataFrame(get_admin_data("activity-logs")), use_container_width=True, hide_index=True)

with tab3:
    st.header("Manage Application Settings")
    st.info("These settings affect the overall application behavior.")

with tab4:
    st.header("Build and Manage Curriculum Structure")
    st.info("This is a top-down curriculum builder. Define the foundational elements first, then link them together.")

    age_cohorts = get_admin_data("age-cohorts"); domains = get_admin_data("domains")
    play_types = get_admin_data("play-types"); components = get_admin_data("components")
    age_cohort_map = {ac['id']: ac['name'] for ac in age_cohorts}
    domain_map = {d['id']: d['name'] for d in domains}

    st.subheader("1. Foundational Elements")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Manage Age Cohorts**"); 
            for ac in age_cohorts:
                c1, c2 = st.columns([4,1]); c1.write(ac['name'])
                if c2.button("🗑️", key=f"del_ac_{ac['id']}", help=f"Delete {ac['name']}"): delete_entry("age-cohorts", ac['id'])
            with st.form("add_ac_form", clear_on_submit=True):
                new_ac_name = st.text_input("New Age Cohort Name"); submitted = st.form_submit_button("Add")
                if submitted and new_ac_name: add_entry("age-cohorts", {"name": new_ac_name})
        with col2:
            st.markdown("**Manage Domains**"); 
            for d in domains:
                c1, c2 = st.columns([4,1]); c1.write(d['name'])
                if c2.button("🗑️", key=f"del_d_{d['id']}", help=f"Delete {d['name']}"): delete_entry("domains", d['id'])
            with st.form("add_d_form", clear_on_submit=True):
                new_d_name = st.text_input("New Domain Name"); submitted = st.form_submit_button("Add")
                if submitted and new_d_name: add_entry("domains", {"name": new_d_name})

    st.subheader("2. Component Matrix")
    with st.container(border=True):
        st.markdown("**Curriculum Overview**")
        if components:
            df_comp = pd.DataFrame(components)
            pivot_df = df_comp.pivot_table(index='domain_name', columns='age_cohort_name', values='name', aggfunc=lambda x: ' • '.join(x)).fillna("")
            st.dataframe(pivot_df, use_container_width=True)
        else: st.info("No components created yet. Add some below!")
        
        st.markdown("---"); st.markdown("**Add Components**")
        with st.form("add_comp_form", clear_on_submit=True):
            new_comp_names = st.text_area("Component Name(s) (one per line)", height=100)
            c1, c2 = st.columns(2)
            selected_d_name = c1.selectbox("Assign to Domain", options=domain_map.values())
            selected_ac_names = c2.multiselect("Assign to Age Cohort(s)", options=age_cohort_map.values())
            if st.form_submit_button("Add Components") and new_comp_names and selected_d_name and selected_ac_names:
                domain_id = next(k for k, v in domain_map.items() if v == selected_d_name)
                age_cohort_ids = [k for k, v in age_cohort_map.items() if v in selected_ac_names]
                for name in new_comp_names.strip().split('\n'):
                    if name:
                        for ac_id in age_cohort_ids:
                            add_entry("components", {"name": name, "age_cohort_id": ac_id, "domain_id": domain_id})

    st.subheader("3. Play Type Studio")
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**Play Types**")
            if st.button("＋ Create New Play Type", use_container_width=True):
                st.session_state.selected_play_type_id = "new"; st.rerun()
            st.markdown("---")
            for pt in play_types:
                if st.button(pt['name'], use_container_width=True, type="primary" if st.session_state.selected_play_type_id == pt['id'] else "secondary"):
                    st.session_state.selected_play_type_id = pt['id']; st.rerun()
        with col2:
            if st.session_state.selected_play_type_id:
                is_new = st.session_state.selected_play_type_id == "new"
                selected_pt = next((pt for pt in play_types if pt['id'] == st.session_state.selected_play_type_id), {}) if not is_new else {}
                
                st.subheader("Editor: " + (selected_pt.get("name") or "New Play Type"))
                with st.form("pt_editor_form"):
                    name = st.text_input("Name", value=selected_pt.get("name", ""))
                    desc = st.text_area("Description", value=selected_pt.get("description", ""))
                    context_options = ["Standard", "Green Play", "Climate Vulnerability"]; current_context_index = context_options.index(selected_pt.get("context", "Standard"))
                    context = st.selectbox("Context", context_options, index=current_context_index)
                    assigned_ac_ids = st.multiselect("Assign to Age Cohorts", options=age_cohort_map.keys(), format_func=lambda id: age_cohort_map.get(id, 'N/A'), default=selected_pt.get("age_cohort_ids", []))
                    assigned_d_ids = st.multiselect("Assign to Domains", options=domain_map.keys(), format_func=lambda id: domain_map.get(id, 'N/A'), default=selected_pt.get("domain_ids", []))
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Save Changes" if not is_new else "Create Play Type", type="primary", use_container_width=True):
                        payload = {"name": name, "description": desc, "context": context, "age_cohort_ids": assigned_ac_ids, "domain_ids": assigned_d_ids}
                        if is_new: add_entry("play-types", payload)
                        else: update_entry("play-types", selected_pt['id'], payload)
                    if not is_new and c2.form_submit_button("🗑️ Delete This Play Type", use_container_width=True):
                        delete_entry("play-types", selected_pt['id'])

with tab5:
    st.header("Manage Resource Library (for RAG)")
    st.info("Upload documents, links, and text. The content will be indexed and used by the AI to generate context-aware plans.")
    
    resources = get_admin_data("resources"); st.subheader("Current Resources")
    st.dataframe(pd.DataFrame(resources), use_container_width=True, hide_index=True)

    st.subheader("Add New Resource")
    with st.form("resource_form", clear_on_submit=False):
        title = st.text_input("Resource Title*")
        resource_type = st.selectbox("Resource Type*", ["Text", "Web Link", "PDF"])
        content_input = None
        if resource_type == "Text": content_input = st.text_area("Paste Text Content*")
        elif resource_type == "Web Link": content_input = st.text_input("Enter URL*")
        elif resource_type == "PDF": content_input = st.file_uploader("Upload PDF File*", type="pdf")
        
        domain_map = {d['name']: d['id'] for d in get_admin_data("domains")}
        age_cohort_map = {ac['name']: ac['id'] for ac in get_admin_data("age-cohorts")}
        selected_domains = st.multiselect("Tag with Domains", options=domain_map.keys())
        selected_age_cohorts = st.multiselect("Tag with Age Cohorts", options=age_cohort_map.keys())

        if st.form_submit_button("Upload and Index Resource", type="primary"):
            if not all([title, resource_type, content_input]):
                st.warning("Please fill all required fields.")
            else:
                with st.spinner("Uploading and indexing... This may take a moment."):
                    form_data = {
                        "title": title, "resource_type": resource_type,
                        "domain_ids[]": [domain_map[name] for name in selected_domains],
                        "age_cohort_ids[]": [age_cohort_map[name] for name in selected_age_cohorts]
                    }
                    files = None
                    if resource_type == 'PDF':
                        files = {'file': (content_input.name, content_input.getvalue())}
                    else:
                        form_data['content_path'] = content_input
                    
                    response = st.session_state.api_session.post(f"{BACKEND_URL}/api/admin/resources", data=form__data, files=files)
                    if response.status_code == 201:
                        st.success(f"Resource '{title}' processed successfully!"); st.cache_data.clear(); st.rerun()
                    else:
                        st.error(f"Upload failed: {response.text}")