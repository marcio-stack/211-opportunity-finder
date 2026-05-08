import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///opportunities.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    SAM_API_KEY = os.environ.get('SAM_API_KEY', '')
    NDP_API_KEY = os.environ.get('NDP_API_KEY', '')
    SCHEDULER_API_ENABLED = True

# ── 211-specific SAM.gov title search terms ──
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

# ── Known 211 organizations (from 211 Master Database) ──
# Used to cross-reference SAM.gov results against actual 211 operators
ORGANIZATIONS_211 = [
    'United Way of Central Alabama',
    '211 Connects Alabama',
    'River Region United Way',
    'United Way of Northwest Alabama',
    'Hands On River Region',
    'United Way of Anchorage',
    'Alaska 211',
    'Community Information & Referral',
    'Arizona 211',
    'United Way of Arkansas',
    'Arkansas 211',
    '211 LA County',
    '211 San Diego',
    '211 Orange County',
    'Inland SoCal 211',
    '211 NorCal',
    '211 Sacramento',
    '211 Connecting Point',
    '211 Ventura County',
    '211 Bay Area',
    '211 Monterey Bay',
    'Mile High United Way',
    'Colorado 211',
    '211 Connecticut',
    'United Way of Connecticut',
    'United Way of Delaware',
    'Delaware 211',
    '211 Florida',
    'FLAIRS',
    '211 Broward',
    '211 Tampa Bay Cares',
    'Heart of Florida United Way',
    'United Way of Greater Atlanta',
    'Aloha United Way',
    'Idaho CareLine',
    'Idaho 211',
    '211 Illinois',
    'United Way of Metro Chicago',
    'Indiana 211',
    'United Way of Central Iowa',
    'Iowa 211',
    'United Way of South Central Kansas',
    '211 Kansas',
    'Metro United Way Louisville',
    'United Way of Bowling Green',
    'United Way of Southeast Louisiana',
    'Louisiana 211',
    'The Opportunity Alliance',
    '211 Maine',
    '211 Maryland',
    'United Way of Massachusetts Bay',
    'Mass 211',
    'United Way for Southeastern Michigan',
    'Michigan 211',
    '211 Northeast Michigan',
    'Greater Twin Cities United Way',
    'Mississippi 211',
    'Missouri 211',
    'Montana 211',
    'United Way of the Midlands',
    'Nebraska 211',
    'Nevada 211',
    '211 New Hampshire',
    'NJ 211',
    'United Way of New Jersey',
    'United Way of Central New Mexico',
    'New Mexico 211',
    '211 New York State',
    'United Way of Greater Rochester',
    '211 WNY',
    'NC 211',
    'United Way of North Carolina',
    'FirstLink',
    'North Dakota 211',
    'LSS 211 Central Ohio',
    'United Way of Greater Cincinnati',
    '211 Oklahoma',
    'Heartline',
    '211info',
    'PA 211',
    'United Way of Pennsylvania',
    '211 Rhode Island',
    'United Way of Rhode Island',
    'United Way Association of SC',
    'SC 211',
    '211 Helpline Center',
    'Tennessee 211',
    '211 Texas',
    'United Way of Tarrant County',
    'United Way of San Antonio',
    'United Way of Greater Houston',
    'DETCOG 211',
    'Texoma Council of Governments',
    'United Way of Metropolitan Dallas',
    'United Way of Salt Lake',
    'Utah 211',
    'Vermont 211',
    '211 Virginia',
    'Council of Community Services',
    'Washington 211',
    'WIN 211',
    'West Virginia 211',
    'Wisconsin 211',
    'United Way of Laramie County',
    'Wyoming 211',
    'DC 211',
    'United Way NCA',
]

# ── False positive keywords ──
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
    # Hardware / parts / supplies
    'valve', 'pump', 'manifold', 'actuator', 'circuit card', 'power supply',
    'brake', 'nut,', 'bolt', 'gasket', 'fitting', 'hose', 'cable',
    'display unit', 'test set', 'extension cord', 'tuning unit',
    # Weapons / ships / military equipment
    'uss ', 'shooting range', 'ammunition', 'munitions',
    # Other irrelevant
    'uniforms', 'laundry', 'pest control', 'elevator', 'generator',
    'fire suppression', 'sprinkler', 'asbestos', 'lead abatement',
]

# ── True positive keywords ──
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
