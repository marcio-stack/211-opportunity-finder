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
SEARCH_TERMS_SAM = [
    '211',
    'call center services',
    'contact center services',
    'information and referral',
    'crisis hotline',
    'helpline services',
    'BPO services',
    'customer service center',
    'call center staffing',
    'overflow call center',
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
    'highway', 'road', 'widening', 'paving', 'bridge', 'route 211',
    'sr 211', 'sr-211', 'state route', 'interstate',
    'military', 'space command', 'missile', 'defense', 'navy', 'army',
    'air force', 'devSecOps', 'weapons', 'ammunition',
    'construction', 'renovation', 'building', 'real estate',
    'guam', 'communications center on guam',
    'janitorial', 'landscaping', 'food service', 'custodial',
    'sewer', 'water treatment', 'electrical grid',
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
