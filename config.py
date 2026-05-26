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

# ============================================================
# SEARCH TERMS — organized by category (211 vs BPO)
# ============================================================

# 211-specific SAM.gov search terms
SEARCH_TERMS_SAM_211 = [
    '211',
    '211 services',
    'information and referral',
    'crisis hotline',
    'helpline services',
    'community resource hotline',
    '2-1-1',
    'United Way call center',
]

# BPO / Contact Center SAM.gov search terms
SEARCH_TERMS_SAM_BPO = [
    'call center services',
    'contact center services',
    'BPO services',
    'customer service center',
    'call center staffing',
    'overflow call center',
    'contact center outsourcing',
    'managed contact center',
    'inbound call center',
    'customer care services',
    'call center operations',
    'telephone answering services',
    'omnichannel contact center',
]

# Combined for backward compat
SEARCH_TERMS_SAM = SEARCH_TERMS_SAM_211 + SEARCH_TERMS_SAM_BPO

# Grants.gov search terms (211 + BPO)
SEARCH_TERMS_GRANTS_211 = [
    'information and referral services',
    'crisis hotline services',
    'community helpline operations',
    '211 contact center technology',
]

SEARCH_TERMS_GRANTS_BPO = [
    'call center services federal',
    'contact center modernization',
    'customer service operations',
]

SEARCH_TERMS_GRANTS = SEARCH_TERMS_GRANTS_211 + SEARCH_TERMS_GRANTS_BPO

# Google News search terms
SEARCH_TERMS_NEWS_211 = [
    '"211" RFP call center',
    '"211 services" contract vendor',
    '"211" procurement "call center"',
    '"211" "request for proposal"',
    '"211" call center transition new vendor',
    '"211 hotline" funding expansion',
    '"211 services" complaints "wait time"',
    '"211" "contract awarded" services',
    '"information and referral" RFP procurement',
    '"211" community services expansion',
    '"United Way" "211" technology',
]

SEARCH_TERMS_NEWS_BPO = [
    '"BPO" "call center" RFP government',
    '"contact center" outsourcing RFP',
    '"contact center" "request for proposal"',
    '"call center" vendor transition government',
    '"managed services" "contact center" government',
    '"BPO" "contract awarded" "call center"',
    '"contact center" modernization government',
    '"customer service" outsourcing government RFP',
]

SEARCH_TERMS_NEWS = SEARCH_TERMS_NEWS_211 + SEARCH_TERMS_NEWS_BPO

# Keywords that indicate FALSE POSITIVES (not about 211 or BPO services)
NEGATIVE_TITLE_KEYWORDS = [
    'highway', 'road', 'widening', 'paving', 'bridge', 'route 211',
    'sr 211', 'sr-211', 'state route', 'interstate',
    'military', 'space command', 'missile', 'defense', 'navy', 'army',
    'air force', 'devsecops', 'weapons', 'ammunition',
    'construction', 'renovation', 'building', 'real estate',
    'guam', 'communications center on guam',
    'janitorial', 'landscaping', 'food service', 'custodial',
    'sewer', 'water treatment', 'electrical grid',
]

# Keywords that indicate TRUE POSITIVES
POSITIVE_KEYWORDS_211 = [
    '211 services', '211 call center', '211 hotline', '211 helpline',
    '211 contact center', '211 information', '211 referral',
    'information and referral', 'crisis hotline', 'crisis line',
    'community resource hotline', 'human services hotline',
    '2-1-1', 'united way 211',
]

POSITIVE_KEYWORDS_BPO = [
    'bpo services', 'bpo rfp', 'bpo contract',
    'call center rfp', 'contact center rfp',
    'call center outsourcing', 'contact center outsourcing',
    'managed contact center', 'customer service rfp',
    'overflow call center', 'surge staffing call center',
    'after-hours call center', 'after hours call center',
    'inbound call center', 'omnichannel contact',
    'telephone answering', 'customer care services',
]

POSITIVE_KEYWORDS = POSITIVE_KEYWORDS_211 + POSITIVE_KEYWORDS_BPO

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
