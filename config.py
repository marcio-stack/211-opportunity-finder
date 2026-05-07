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

SEARCH_TERMS = [
    '211 information referral',
    '211 call center services',
    '211 contact center',
    '211 BPO services',
    '211 surge support',
    '211 overflow call center',
    'information and referral services RFP',
    '211 crisis line services',
    '211 community resource hotline',
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
