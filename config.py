import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///opportunities.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    SAM_API_KEY = os.environ.get('SAM_API_KEY', '')
    SCHEDULER_API_ENABLED = True

# Focused search terms for 211 procurement / lead gen
# NARROWED: Only 211-specific terms to avoid HVAC, IT, and other irrelevant RFPs
SEARCH_TERMS_SAM = [
    '211 services',
    '211 call center',
    '211 hotline',
    '211 contact center',
    '2-1-1 services',
    'information and referral services',
    'crisis hotline services',
    'community helpline',
    'human services hotline',
]

SEARCH_TERMS_GRANTS = [
    'information and referral services',
    'crisis hotline services',
    'community helpline operations',
    '211 contact center technology',
]

SEARCH_TERMS_NEWS = [
    '"211" RFP call center',
    '"211 services" contract vendor',
    '"211" procurement "call center"',
    '"211" "request for proposal"',
    '"211" call center transition new vendor',
    '"211 hotline" funding expansion',
    '"211 services" complaints "wait time"',
    '"211" "contract awarded" services',
    '"information and referral" RFP procurement',
]

# Keywords that indicate FALSE POSITIVES (not about 211 services)
NEGATIVE_TITLE_KEYWORDS = [
    # Roads / infrastructure
    'highway', 'road', 'widening', 'paving', 'bridge', 'route 211',
    'sr 211', 'sr-211', 'state route', 'interstate',
    # Military / defense
    'military', 'space command', 'missile', 'defense', 'navy', 'army',
    'air force', 'devSecOps', 'weapons', 'ammunition',
    # Construction / real estate
    'construction', 'renovation', 'building', 'real estate',
    # Guam false positive
    'guam', 'communications center on guam',
    # Facilities / maintenance
    'janitorial', 'landscaping', 'food service', 'custodial',
    'sewer', 'water treatment', 'electrical grid',
    # HVAC / mechanical / trades
    'hvac', 'plumbing', 'heating', 'cooling', 'air conditioning',
    'mechanical', 'electrical contractor', 'roofing', 'painting',
    'carpentry', 'welding', 'boiler', 'furnace', 'ductwork',
    # Medical / pharma / lab
    'medical equipment', 'pharmaceutical', 'laboratory', 'surgical',
    'radiology', 'dental', 'prosthetics', 'biomedical',
    # IT / software / cyber
    'IT services', 'software development', 'cybersecurity', 'cloud services',
    'network infrastructure', 'data center', 'server',
    # Telecom (non-211)
    'telecommunications', 'fiber optic', 'broadband', 'cellular tower',
    # Fleet / vehicles
    'fleet', 'vehicle maintenance', 'automotive', 'tire', 'fuel',
    # Waste / sanitation
    'trash', 'waste management', 'recycling', 'hazardous waste', 'debris',
    # Security (physical)
    'security guard', 'patrol', 'surveillance', 'alarm system',
    # Other irrelevant
    'uniforms', 'laundry', 'pest control', 'elevator', 'generator',
    'fire suppression', 'sprinkler', 'asbestos', 'lead abatement',
]

# Keywords that indicate TRUE POSITIVES (actually about 211/call center services)
POSITIVE_KEYWORDS = [
    '211 services', '211 call center', '211 hotline', '211 helpline',
    '211 contact center', '211 information', '211 referral',
    'information and referral', 'crisis hotline', 'crisis line',
    'community resource hotline', 'human services hotline',
    'call center RFP', 'contact center RFP', 'BPO services RFP',
    'overflow call center', 'surge staffing call center',
    'after-hours call center', 'after hours call center',
]

MONITORED_STATES = [
    'TX', 'CA', 'NY', 'FL', 'PA', 'OH', 'OK', 'IL',
    'NJ', 'MI', 'GA', 'NC', 'VA', 'WA', 'AZ', 'CO',
    'IN', 'MO', 'TN', 'SC', 'AL', 'KY', 'OR', 'CT',
    'KS', 'RI', 'NE', 'NM', 'SD', 'IA', 'ME', 'ID',
]

STATE_PROCUREMENT_URLS = {
    'TX': 'https://www.hhs.texas.gov/business/contracting-hhs',
    'CA': 'https://caleprocure.ca.gov/pages/index.aspx',
    'NY': 'https://www.ogs.ny.gov/procurement',
    'FL': 'https://vendor.myfloridamarketplace.com',
    'PA': 'https://www.emarketplace.state.pa.us/Search.aspx',
    'OH': 'https://procure.ohio.gov/proc/index.asp',
    'OK': 'https://oklahoma.gov/omes/services/purchasing.html',
    'IL': 'https://www.bidbuy.illinois.gov',
    'NJ': 'https://www.njstart.gov',
    'MI': 'https://sigma.michigan.gov',
}
