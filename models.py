from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(5))
    operator_type = db.Column(db.String(50))
    coverage_area = db.Column(db.String(200))
    website = db.Column(db.String(300))
    phone = db.Column(db.String(30))
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(200))
    accredited = db.Column(db.Boolean, default=False)
    funding_source = db.Column(db.String(200))
    contract_status = db.Column(db.String(100))
    contract_expiration = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(200))
    source_url = db.Column(db.String(500))
    state = db.Column(db.String(5))
    category = db.Column(db.String(20), default='211')  # '211', 'bpo', or 'both'
    opportunity_type = db.Column(db.String(50))  # rfp, signal, contract_expiry, news
    description = db.Column(db.Text)
    deadline = db.Column(db.String(100))
    contact_info = db.Column(db.Text)
    relevance_score = db.Column(db.Integer, default=0)  # 1-100
    ai_analysis = db.Column(db.Text)
    status = db.Column(db.String(30), default='new')  # new, reviewing, contacted, applied, won, lost, archived
    assigned_to = db.Column(db.String(100))
    notes = db.Column(db.Text)
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    id = db.Column(db.Integer, primary_key=True)
    search_type = db.Column(db.String(50))  # scheduled, manual
    query = db.Column(db.String(500))
    source = db.Column(db.String(200))
    results_found = db.Column(db.Integer, default=0)
    new_opportunities = db.Column(db.Integer, default=0)
    ran_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default='completed')
    error = db.Column(db.Text)
