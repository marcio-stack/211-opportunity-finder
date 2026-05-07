import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import logging
from config import (
    SEARCH_TERMS_SAM, SEARCH_TERMS_GRANTS, SEARCH_TERMS_NEWS,
    NEGATIVE_TITLE_KEYWORDS, POSITIVE_KEYWORDS,
)

logger = logging.getLogger(__name__)


def is_false_positive(title):
    """Check if a result is a false positive (not about 211 services)."""
    title_lower = title.lower()

    # Check for dollar amounts like "$211 million", "$211M", "$211,000"
    if re.search(r'\$\s*211[\s,.\d]*(?:million|billion|m\b|b\b|k\b|,)', title_lower):
        return True

    # Check for highway/route numbers: "SR 211", "Route 211", "Highway 211"
    if re.search(r'(?:sr|route|highway|interstate|hwy|rd|road)\s*[-]?\s*211', title_lower):
        return True

    # Check negative keywords
    for neg in NEGATIVE_TITLE_KEYWORDS:
        if neg in title_lower:
            # But if it also has a positive keyword, keep it
            has_positive = any(pos in title_lower for pos in POSITIVE_KEYWORDS)
            if not has_positive:
                return True

    return False


def is_relevant_to_211_services(title, description=''):
    """Check if content is actually relevant to 211/call center services."""
    text = (title + ' ' + description).lower()

    # Strong relevance signals
    strong_signals = [
        '211 services', '211 call center', '211 hotline', '211 helpline',
        '211 contact center', '211 information and referral',
        'information and referral', 'crisis hotline', 'crisis line',
        'community resource', 'human services call',
        'united way 211', '2-1-1',
    ]

    # Moderate signals (need additional context)
    moderate_signals = [
        'call center rfp', 'contact center rfp', 'call center bid',
        'contact center procurement', 'bpo services',
        'overflow call center', 'surge staffing',
        'after-hours coverage', 'helpline services',
    ]

    for signal in strong_signals:
        if signal in text:
            return True

    for signal in moderate_signals:
        if signal in text:
            return True

    return False


def classify_lead_type(title, description='', source=''):
    """Classify a result into lead type for sales pipeline."""
    text = (title + ' ' + description).lower()

    if any(w in text for w in ['rfp', 'request for proposal', 'solicitation', 'bid opportunity', 'invitation to bid']):
        return 'rfp'
    if any(w in text for w in ['procurement', 'seeking vendor', 'vendor selection', 'competitive bid']):
        return 'procurement'
    if any(w in text for w in ['contract awarded', 'contract award', 'selected vendor', 'vendor chosen']):
        return 'contract_award'
    if any(w in text for w in ['contract expir', 'contract end', 'contract renew', 'rebid', 're-bid']):
        return 'contract_expiry'
    if any(w in text for w in ['grant', 'funding', 'appropriation', 'budget allocat']):
        return 'funding'
    if any(w in text for w in ['complaint', 'issue', 'problem', 'failure', 'wait time', 'overwhelmed', 'understaffed']):
        return 'service_gap'
    if any(w in text for w in ['expansion', 'expand', 'new service', 'launch', 'growing']):
        return 'expansion'
    if any(w in text for w in ['disaster', 'emergency', 'hurricane', 'wildfire', 'flood', 'tornado', 'pandemic']):
        return 'disaster_response'
    if source == 'Grants.gov':
        return 'grant'
    if source == 'SAM.gov':
        return 'rfp'
    return 'market_signal'


def search_sam_gov(api_key, keywords=None):
    """Search SAM.gov for 211-related procurement opportunities."""
    if not api_key:
        logger.warning("No SAM.gov API key configured — skipping SAM.gov")
        return []

    results = []
    search_terms = keywords or SEARCH_TERMS_SAM

    for term in search_terms:
        try:
            url = "https://api.sam.gov/opportunities/v2/search"
            params = {
                'api_key': api_key,
                'keywords': term,
                'postedFrom': (datetime.now().replace(day=1)).strftime('%m/%d/%Y'),
                'limit': 25,
                'offset': 0,
            }
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for opp in data.get('opportunitiesData', []):
                    title = opp.get('title', '')
                    desc = opp.get('description', '')[:2000]

                    if is_false_positive(title):
                        continue

                    results.append({
                        'title': title,
                        'source': 'SAM.gov',
                        'source_url': f"https://sam.gov/opp/{opp.get('noticeId', '')}/view",
                        'state': opp.get('placeOfPerformance', {}).get('state', {}).get('code', ''),
                        'opportunity_type': classify_lead_type(title, desc, 'SAM.gov'),
                        'description': desc,
                        'deadline': opp.get('responseDeadLine', ''),
                        'contact_info': json.dumps(opp.get('pointOfContact', [])),
                        'discovered_at': datetime.utcnow(),
                    })
        except Exception as e:
            logger.error(f"SAM.gov search error for '{term}': {e}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    return unique


def search_google_news(query=None):
    """Search Google News RSS for 211-related procurement signals."""
    results = []
    search_queries = SEARCH_TERMS_NEWS

    for q in search_queries:
        try:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'lxml-xml')
                items = soup.find_all('item')
                for item in items[:5]:  # Fewer per query, more queries
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')

                    if title:
                        title_text = title.get_text()

                        # Skip false positives
                        if is_false_positive(title_text):
                            continue

                        # Must be relevant to 211 services
                        desc_text = desc.get_text() if desc else ''
                        if not is_relevant_to_211_services(title_text, desc_text):
                            continue

                        results.append({
                            'title': title_text,
                            'source': 'Google News',
                            'source_url': link.get_text() if link else '',
                            'state': extract_state_from_text(title_text),
                            'opportunity_type': classify_lead_type(title_text, desc_text, 'Google News'),
                            'description': desc_text,
                            'deadline': '',
                            'contact_info': '',
                            'discovered_at': datetime.utcnow(),
                        })
        except Exception as e:
            logger.error(f"Google News search error for '{q}': {e}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    return unique


def search_grants_gov(keywords=None):
    """Search Grants.gov for 211-related federal grants."""
    results = []
    terms = keywords or SEARCH_TERMS_GRANTS

    for term in terms:
        try:
            url = "https://www.grants.gov/grantsws/rest/opportunities/search/"
            params = {
                'keyword': term,
                'oppStatus': 'forecasted|posted',
                'sortBy': 'openDate|desc',
                'rows': 25,
            }
            resp = requests.get(url, params=params, timeout=30,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
            if resp.status_code == 200:
                data = resp.json()
                for opp in data.get('oppHits', []):
                    title = opp.get('title', '')
                    synopsis = opp.get('synopsis', '')[:2000]

                    if is_false_positive(title):
                        continue

                    # For grants, check relevance more loosely (funding = potential client money)
                    if not is_relevant_to_211_services(title, synopsis):
                        # Still include if it mentions social services / community services
                        text = (title + ' ' + synopsis).lower()
                        if not any(kw in text for kw in ['social services', 'community services',
                                                          'human services', 'crisis services',
                                                          'helpline', 'hotline', 'call center']):
                            continue

                    results.append({
                        'title': title,
                        'source': 'Grants.gov',
                        'source_url': f"https://www.grants.gov/search-results-detail/{opp.get('id', '')}",
                        'state': '',
                        'opportunity_type': classify_lead_type(title, synopsis, 'Grants.gov'),
                        'description': synopsis,
                        'deadline': opp.get('closeDate', ''),
                        'contact_info': opp.get('agencyName', ''),
                        'discovered_at': datetime.utcnow(),
                    })
        except Exception as e:
            logger.error(f"Grants.gov search error: {e}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    return unique


def extract_state_from_text(text):
    """Extract US state abbreviation from text."""
    state_patterns = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
        'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
        'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
        'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
        'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
        'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
        'Los Angeles': 'CA', 'Chicago': 'IL', 'Houston': 'TX', 'Phoenix': 'AZ',
        'San Diego': 'CA', 'Dallas': 'TX', 'San Antonio': 'TX',
        'Kansas City': 'MO', 'Louisville': 'KY', 'Portland': 'OR',
    }
    for name, abbr in state_patterns.items():
        if name.lower() in text.lower():
            return abbr
    state_abbr = re.findall(r'\b([A-Z]{2})\b', text)
    valid = set(state_patterns.values())
    for s in state_abbr:
        if s in valid:
            return s
    return ''


def run_all_scrapers(sam_api_key=''):
    """Run all scrapers and return combined, filtered results."""
    all_results = []

    logger.info("Running SAM.gov scraper...")
    all_results.extend(search_sam_gov(sam_api_key))

    logger.info("Running Google News scraper...")
    all_results.extend(search_google_news())

    logger.info("Running Grants.gov scraper...")
    all_results.extend(search_grants_gov())

    logger.info(f"Total results found: {len(all_results)}")
    return all_results
