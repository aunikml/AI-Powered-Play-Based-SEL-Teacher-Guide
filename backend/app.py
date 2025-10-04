import os
from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import dotenv_values
from functools import wraps

# --- Local Module Imports ---
from .models import db, User, Plan, KnowledgeBase, ActivityLog, AgeCohort, Domain, Component, PlayType, Resource, FeedbackLog
from .services import generate_teacher_guide
from .initial_data import AGE_COHORTS, DOMAINS, PLAY_TYPES, COMPONENTS
from .rag_setup import add_resource_to_vectorstore

# --- App Initialization ---
app = Flask(__name__)

# --- Flask-Native Configuration ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')
config = dotenv_values(dotenv_path)

app.config.update(
    SECRET_KEY=config.get('FLASK_SECRET_KEY', 'a-fallback-secret-key'),
    SQLALCHEMY_DATABASE_URI=config.get('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    GOOGLE_API_KEY=config.get("GOOGLE_API_KEY"),
    ADMIN_EMAIL=config.get("ADMIN_EMAIL", "admin@example.com"),
    ADMIN_PASSWORD=config.get("ADMIN_PASSWORD", "supersecret")
)

if not app.config.get("GOOGLE_API_KEY"):
    print("\n\n" + "="*50); print("FATAL ERROR: GOOGLE_API_KEY not found in .env file or not loaded into app.config."); print(f"Attempted to load .env from: {dotenv_path}"); print("="*50 + "\n\n")

CORS(app, supports_credentials=True, origins=["http://localhost:8501"])
db.init_app(app); bcrypt = Bcrypt(app); login_manager = LoginManager(); login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id): return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated: return jsonify({"message": "Authentication required"}), 401
        if current_user.role != 'admin': return jsonify({"message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action):
    if current_user.is_authenticated:
        log_entry = ActivityLog(action=action, user_id=current_user.id); db.session.add(log_entry); db.session.commit()

# ===============================================
# ===         AUTHENTICATION ROUTES           ===
# ===============================================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json; email = data['email']
    if User.query.filter_by(email=email).first(): return jsonify({"message": "Email already registered"}), 409
    email_prefix = email.split('@')[0]; temp_password = f"{data['first_name'].lower()}@{email_prefix[-4:]}"
    new_user = User(first_name=data['first_name'], last_name=data['last_name'], email=email, city=data['city'], country=data['country'], force_password_change=True)
    new_user.set_password(temp_password); db.session.add(new_user); db.session.commit()
    return jsonify({"message": "User registered successfully.", "temporary_password": temp_password}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json; user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user); log_activity("User logged in")
        return jsonify({"message": "Login successful", "user": {"id": user.id, "email": user.email, "first_name": user.first_name, "role": user.role, "force_password_change": user.force_password_change}}), 200
    return jsonify({"message": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    log_activity("User logged out"); logout_user(); return jsonify({"message": "Logout successful"}), 200

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json; new_password = data.get('new_password')
    if not new_password or len(new_password) < 6: return jsonify({"message": "Password must be at least 6 characters long"}), 400
    current_user.set_password(new_password); current_user.force_password_change = False; db.session.commit(); log_activity("User changed password")
    return jsonify({"message": "Password updated successfully"}), 200

# ===============================================
# ===      TEACHER-FACING CHATBOT ROUTES      ===
# ===============================================
@app.route('/api/chatbot/options', methods=['GET'])
@login_required
def get_chatbot_options():
    options = {"age_cohorts": {}, "play_types": {}}
    age_cohorts = AgeCohort.query.order_by(AgeCohort.id).all()
    domains = Domain.query.order_by(Domain.id).all()
    for ac in age_cohorts:
        options["age_cohorts"][ac.name] = {}
        for d in domains:
            components = Component.query.filter_by(age_cohort_id=ac.id, domain_id=d.id).all()
            if components:
                options["age_cohorts"][ac.name][d.name] = [c.name for c in components]
                key = f"{ac.id}-{d.id}"
                valid_play_types = PlayType.query.join(PlayType.age_cohorts).join(PlayType.domains).filter(AgeCohort.id == ac.id, Domain.id == d.id).all()
                options["play_types"][key] = [pt.to_dict() for pt in valid_play_types]
    return jsonify(options)
    
@app.route('/api/generate-plan', methods=['POST'])
@login_required
def generate_plan_endpoint():
    data = request.json; play_type_obj = data.get('play_type', {})
    play_type_name = play_type_obj.get('name', 'Not specified'); play_type_context = play_type_obj.get('context', 'Standard')
    api_key = current_app.config.get('GOOGLE_API_KEY')
    guide_data_dict = generate_teacher_guide(
        data.get('age_cohort'), data.get('subject'), data.get('sub_domain'), play_type_name, play_type_context, api_key=api_key
    )
    if "error" in guide_data_dict or not guide_data_dict.get('guide_title'):
        error_message = guide_data_dict.get("error", "The LLM returned an empty or invalid plan. Please try again.")
        return jsonify({"error": error_message}), 500
    log_activity(f"Generated RAG plan for {data.get('age_cohort')}, '{data.get('sub_domain')}'"); return jsonify(guide_data_dict)

@app.route('/api/my-plans', methods=['GET', 'POST'])
@login_required
def handle_plans():
    if request.method == 'GET':
        plans = Plan.query.filter_by(user_id=current_user.id).order_by(Plan.created_at.desc()).all()
        return jsonify([{"id": p.id, "title": p.title, "content": p.content, "age_cohort": p.age_cohort, "subject": p.subject, "play_type": p.play_type, "created_at": p.created_at.strftime('%Y-%m-%d %H:%M')} for p in plans])
    if request.method == 'POST':
        data = request.json; new_plan = Plan(title=data.get('title', 'Untitled Plan'), content=data['content'], age_cohort=data['age_cohort'], subject=data['subject'], play_type=data['play_type'], user_id=current_user.id)
        db.session.add(new_plan); db.session.commit(); log_activity(f"Saved plan '{new_plan.title}'"); return jsonify({"message": "Plan saved", "plan_id": new_plan.id}), 201

@app.route('/api/plans/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan: return jsonify({"message": "Plan not found"}), 404
    if plan.user_id != current_user.id: return jsonify({"message": "Unauthorized"}), 403
    db.session.delete(plan); db.session.commit(); log_activity(f"Deleted plan ID {plan_id}"); return jsonify({"message": "Plan deleted"}), 200

@app.route('/api/feedback', methods=['POST'])
@login_required
def handle_feedback():
    data = request.json
    if 'rating' not in data or 'selections' not in data or 'generated_output' not in data:
        return jsonify({"message": "Missing required feedback data"}), 400
    new_feedback = FeedbackLog(rating=data['rating'], selections=data['selections'], generated_output=data['generated_output'], user_id=current_user.id)
    db.session.add(new_feedback); db.session.commit()
    log_activity(f"Submitted feedback (Rating: {data['rating']})")
    return jsonify({"message": "Feedback submitted successfully"}), 201

# ===============================================
# ===             ADMIN ROUTES                ===
# ===============================================
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    return jsonify([{"id": u.id, "first_name": u.first_name, "last_name": u.last_name, "email": u.email, "role": u.role} for u in User.query.all()])

@app.route('/api/admin/activity-logs', methods=['GET'])
@admin_required
def get_activity_logs():
    logs = db.session.query(ActivityLog, User.email).join(User, ActivityLog.user_id == User.id).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return jsonify([{"id": log.id, "action": log.action, "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "user_email": email} for log, email in logs])

@app.route('/api/admin/age-cohorts', methods=['GET', 'POST'])
@admin_required
def handle_age_cohorts_collection():
    if request.method == 'GET': return jsonify([ac.to_dict() for ac in AgeCohort.query.order_by(AgeCohort.id).all()])
    if request.method == 'POST':
        data = request.json; name = data.get('name')
        if not name: return jsonify({"message": "Name is required"}), 400
        new_ac = AgeCohort(name=name); db.session.add(new_ac); db.session.commit(); return jsonify(new_ac.to_dict()), 201

@app.route('/api/admin/age-cohorts/<int:ac_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_age_cohort_item(ac_id):
    ac = db.session.get(AgeCohort, ac_id)
    if not ac: return jsonify({"message": "Not Found"}), 404
    if request.method == 'PUT': data = request.json; ac.name = data.get('name', ac.name); db.session.commit(); return jsonify(ac.to_dict())
    if request.method == 'DELETE':
        log_activity(f"Admin deleted Age Cohort: {ac.name}"); db.session.delete(ac); db.session.commit(); return jsonify({"message": "Deleted"}), 200

@app.route('/api/admin/domains', methods=['GET', 'POST'])
@admin_required
def handle_domains_collection():
    if request.method == 'GET': return jsonify([d.to_dict() for d in Domain.query.order_by(Domain.id).all()])
    if request.method == 'POST':
        data = request.json; name = data.get('name')
        if not name: return jsonify({"message": "Name is required"}), 400
        new_d = Domain(name=name); db.session.add(new_d); db.session.commit(); return jsonify(new_d.to_dict()), 201

@app.route('/api/admin/domains/<int:d_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_domain_item(d_id):
    d = db.session.get(Domain, d_id)
    if not d: return jsonify({"message": "Not Found"}), 404
    if request.method == 'PUT': data = request.json; d.name = data.get('name', d.name); db.session.commit(); return jsonify(d.to_dict())
    if request.method == 'DELETE':
        log_activity(f"Admin deleted Domain: {d.name}"); db.session.delete(d); db.session.commit(); return jsonify({"message": "Deleted"}), 200

@app.route('/api/admin/play-types', methods=['GET', 'POST'])
@admin_required
def handle_play_types_collection():
    if request.method == 'GET': return jsonify([pt.to_dict() for pt in PlayType.query.order_by(PlayType.id).all()])
    if request.method == 'POST':
        data = request.json
        if not all([data.get('name'), data.get('context')]): return jsonify({"message": "Name and context are required"}), 400
        new_pt = PlayType(name=data['name'], description=data.get('description',''), context=data['context'])
        age_cohorts = AgeCohort.query.filter(AgeCohort.id.in_(data.get('age_cohort_ids', []))).all()
        domains = Domain.query.filter(Domain.id.in_(data.get('domain_ids', []))).all()
        new_pt.age_cohorts = age_cohorts; new_pt.domains = domains
        db.session.add(new_pt); db.session.commit(); return jsonify(new_pt.to_dict()), 201

@app.route('/api/admin/play-types/<int:pt_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_play_type_item(pt_id):
    pt = db.session.get(PlayType, pt_id)
    if not pt: return jsonify({"message": "Not Found"}), 404
    if request.method == 'PUT':
        data = request.json; pt.name = data.get('name', pt.name); pt.description = data.get('description', pt.description); pt.context = data.get('context', pt.context)
        age_cohorts = AgeCohort.query.filter(AgeCohort.id.in_(data.get('age_cohort_ids', []))).all()
        domains = Domain.query.filter(Domain.id.in_(data.get('domain_ids', []))).all()
        pt.age_cohorts = age_cohorts; pt.domains = domains
        db.session.commit(); return jsonify(pt.to_dict())
    if request.method == 'DELETE':
        log_activity(f"Admin deleted Play Type: {pt.name}"); db.session.delete(pt); db.session.commit(); return jsonify({"message": "Deleted"}), 200
        
@app.route('/api/admin/components', methods=['GET', 'POST'])
@admin_required
def handle_components_collection():
    if request.method == 'GET': return jsonify([c.to_dict() for c in Component.query.order_by(Component.id).all()])
    if request.method == 'POST':
        data = request.json
        if not all([data.get('name'), data.get('age_cohort_id'), data.get('domain_id')]): return jsonify({"message": "All fields are required"}), 400
        new_c = Component(name=data['name'], age_cohort_id=data['age_cohort_id'], domain_id=data['domain_id'])
        db.session.add(new_c); db.session.commit(); return jsonify(new_c.to_dict()), 201

@app.route('/api/admin/components/<int:c_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_component_item(c_id):
    c = db.session.get(Component, c_id)
    if not c: return jsonify({"message": "Not Found"}), 404
    if request.method == 'PUT': data = request.json; c.name = data.get('name', c.name); db.session.commit(); return jsonify(c.to_dict())
    if request.method == 'DELETE':
        log_activity(f"Admin deleted Component: {c.name}"); db.session.delete(c); db.session.commit(); return jsonify({"message": "Deleted"}), 200

@app.route('/api/admin/resources', methods=['GET', 'POST', 'DELETE'])
@admin_required
def handle_resources():
    if request.method == 'GET':
        return jsonify([r.to_dict() for r in Resource.query.order_by(Resource.id).all()])
    if request.method == 'POST':
        title = request.form['title']; resource_type = request.form['resource_type']
        domain_ids = [int(i) for i in request.form.getlist('domain_ids[]')]
        age_cohort_ids = [int(i) for i in request.form.getlist('age_cohort_ids[]')]
        content_path = ""
        if resource_type in ['Web Link', 'Text']: content_path = request.form['content_path']
        elif resource_type == 'PDF':
            file = request.files.get('file')
            if not file or not file.filename: return jsonify({"message": "No file uploaded"}), 400
            upload_folder = 'uploads'; os.makedirs(upload_folder, exist_ok=True)
            content_path = os.path.join(upload_folder, file.filename); file.save(content_path)
        
        domains = Domain.query.filter(Domain.id.in_(domain_ids)).all()
        age_cohorts = AgeCohort.query.filter(AgeCohort.id.in_(age_cohort_ids)).all()
        new_resource = Resource(title=title, resource_type=resource_type, content_path=content_path, domains=domains, age_cohorts=age_cohorts)
        db.session.add(new_resource); db.session.commit()
        add_resource_to_vectorstore(
            resource_id=new_resource.id, title=title, content_path=content_path,
            resource_type=resource_type, domain_names=[d.name for d in domains], age_cohort_names=[ac.name for ac in age_cohorts]
        )
        log_activity(f"Admin uploaded resource: {title}"); return jsonify(new_resource.to_dict()), 201
    if request.method == 'DELETE':
        res_id = request.args.get('id'); resource = db.session.get(Resource, res_id)
        if not resource: return jsonify({"message": "Not Found"}), 404
        db.session.delete(resource); db.session.commit(); log_activity(f"Admin deleted resource: {resource.title}"); return jsonify({"message": "Deleted"}), 200

# ===============================================
# ===         APP STARTUP LOGIC               ===
# ===============================================
def seed_database():
    with app.app_context():
        if AgeCohort.query.first() is None:
            print("Seeding Age Cohorts..."); [db.session.add(AgeCohort(**d)) for d in AGE_COHORTS]; db.session.commit()
        if Domain.query.first() is None:
            print("Seeding Domains..."); [db.session.add(Domain(**d)) for d in DOMAINS]; db.session.commit()
        if PlayType.query.first() is None:
            print("Seeding Play Types...")
            for pt_data in PLAY_TYPES:
                pt = PlayType(name=pt_data["name"], description=pt_data["description"], context=pt_data["context"])
                pt.age_cohorts = AgeCohort.query.all(); pt.domains = Domain.query.all()
                db.session.add(pt)
            db.session.commit()
        if Component.query.first() is None:
            print("Seeding Components...")
            for name, ac_name, d_name in COMPONENTS:
                ac = AgeCohort.query.filter_by(name=ac_name).first(); d = Domain.query.filter_by(name=d_name).first()
                if ac and d: db.session.add(Component(name=name, age_cohort_id=ac.id, domain_id=d.id))
            db.session.commit(); print("Components seeded.")

def create_admin_user_if_not_exists():
    with app.app_context():
        if not User.query.filter_by(role='admin').first():
            print("No admin found. Creating one...")
            admin_email = app.config.get('ADMIN_EMAIL'); admin_password = app.config.get('ADMIN_PASSWORD')
            if User.query.filter_by(email=admin_email).first(): return
            admin = User(first_name='Admin', last_name='User', email=admin_email, role='admin', force_password_change=False); admin.set_password(admin_password); db.session.add(admin); db.session.commit(); print(f"Admin '{admin_email}' created.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    create_admin_user_if_not_exists()
    seed_database()
    app.run(port=5001, debug=True, use_reloader=False)