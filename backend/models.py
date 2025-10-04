from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

# --- Original User, Plan, and Logging Models (Unchanged) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    role = db.Column(db.String(20), default='teacher', nullable=False)
    force_password_change = db.Column(db.Boolean, default=True)
    
    plans = db.relationship('Plan', backref='author', lazy=True)
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    age_cohort = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    play_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ==============================================================================
# ===                  DYNAMIC DOMAIN BUILDER MODELS (V2)                    ===
# ==============================================================================
playtype_agecohort_association = db.Table('playtype_agecohort_association',
    db.Column('play_type_id', db.Integer, db.ForeignKey('play_type.id'), primary_key=True),
    db.Column('age_cohort_id', db.Integer, db.ForeignKey('age_cohort.id'), primary_key=True)
)

playtype_domain_association = db.Table('playtype_domain_association',
    db.Column('play_type_id', db.Integer, db.ForeignKey('play_type.id'), primary_key=True),
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True)
)

class AgeCohort(db.Model):
    __tablename__ = 'age_cohort'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    components = db.relationship('Component', backref='age_cohort', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): return {"id": self.id, "name": self.name}

class Domain(db.Model):
    __tablename__ = 'domain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    components = db.relationship('Component', backref='domain', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): return {"id": self.id, "name": self.name}

class Component(db.Model):
    __tablename__ = 'component'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age_cohort_id = db.Column(db.Integer, db.ForeignKey('age_cohort.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    def to_dict(self):
        return {"id": self.id, "name": self.name, "age_cohort_id": self.age_cohort_id,
            "age_cohort_name": self.age_cohort.name, "domain_id": self.domain_id, "domain_name": self.domain.name}

class PlayType(db.Model):
    __tablename__ = 'play_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    context = db.Column(db.String(50), nullable=False, default="Standard")
    age_cohorts = db.relationship('AgeCohort', secondary=playtype_agecohort_association, backref=db.backref('play_types', lazy='dynamic'))
    domains = db.relationship('Domain', secondary=playtype_domain_association, backref=db.backref('play_types', lazy='dynamic'))
    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description, "context": self.context,
            "age_cohort_ids": [ac.id for ac in self.age_cohorts], "domain_ids": [d.id for d in self.domains]}

# ==============================================================================
# ===            NEW MODELS FOR RAG AND FEEDBACK LOOP (PHASE 1 & 2)          ===
# ==============================================================================

# --- Association tables for the new Resource model ---
resource_domain_association = db.Table('resource_domain_association',
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True)
)
resource_age_cohort_association = db.Table('resource_age_cohort_association',
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
    db.Column('age_cohort_id', db.Integer, db.ForeignKey('age_cohort.id'), primary_key=True)
)

# --- NEW Resource Model (for RAG) ---
class Resource(db.Model):
    """Stores metadata about uploaded organizational resources (PDFs, links, etc.)."""
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., "PDF", "Web Link", "Text"
    content_path = db.Column(db.String(255), nullable=True)  # Path to file or URL
    
    # Many-to-Many relationships for tagging
    domains = db.relationship('Domain', secondary=resource_domain_association, backref=db.backref('resources', lazy='dynamic'))
    age_cohorts = db.relationship('AgeCohort', secondary=resource_age_cohort_association, backref=db.backref('resources', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "resource_type": self.resource_type,
            "content_path": self.content_path,
            "domain_ids": [d.id for d in self.domains],
            "age_cohort_ids": [ac.id for ac in self.age_cohorts]
        }

# --- NEW FeedbackLog Model (for Data Collection) ---
class FeedbackLog(db.Model):
    """Stores teacher feedback on generated plans for future fine-tuning."""
    __tablename__ = 'feedback_log'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1 for good, -1 for bad
    selections = db.Column(db.JSON, nullable=False) # The inputs to the model
    generated_output = db.Column(db.JSON, nullable=False) # The JSON output from the model
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)