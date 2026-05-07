import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import logging

logger = logging.getLogger(__name__)


def search_sam_gov(api_key, keywords=None):
    """Search SAM.gov for 211-related opportunities."""
    if not api_key:
        logger.warning("No SAM.gov API key configured")
        return []

    results = []
    search_terms = keywords or ['211 information referral', '211 call center']

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
                    results.append({
                        'title': opp.get('title', ''),
                        'source': 'SAM.gov',
                        'source_url': f"https://sam.gov/opp/{opp.get('noticeId', '')}/view",
                        'state': opp.get('placeOfPerformance', {}).get('state', {}).get('code', ''),
                        'opportunity_type': 'rfp',
                        'description': opp.get('description', '')[:2000],
                        'deadline': opp.get('responseDeadLine', ''),
                        'contact_info': json.dumps(opp.get('pointOfContact', [])),
                        'discovered_at': datetime.utcnow(),
                    })
        except Exception as e:
            logger.error(f"SAM.gov search error for '{term}': {e}")

    return results


def search_google_news(query="211 services RFP"):
    """Search Google News RSS for 211-related news and signals."""
    results = []
    search_queries = [
        '211 services RFP contract',
        '211 call center vendor change',
        '211 information referral bid',
        '211 service complaints issues',
        '211 community services funding',
        '211 contract award',
    ]

    for q in search_queries:
        try:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'lxml-xml')
                items = soup.find_all('item')
                for item in items[:10]:
                    title = item.find('title')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    desc = item.find('description')

                    if title:
                        title_text = title.get_text()
                        if any(kw in title_text.lower() for kw in ['211', 'information and referral', 'call center', 'contact center', 'bpo', 'crisis line']):
                            results.append({
                                'title': title_text,
                                'source': 'Google News',
                                'source_url': link.get_text() if link else '',
                                'state': extract_state_from_text(title_text),
                                'opportunity_type': classify_news_signal(title_text),
                                'description': desc.get_text() if desc else '',
                                'deadline': '',
                                'contact_info': '',
                                'discovered_at': datetime.utcnow(),
                            })
        except Exception as e:
            logger.error(f"Google News search error for '{q}': {e}")

    return results


def search_grants_gov(keywords=None):
    """Search Grants.gov for 211-related federal grants."""
    results = []
    terms = keywords or ['211', 'information referral', 'crisis hotline community']

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
                    results.append({
                        'title': opp.get('title', ''),
                        'source': 'Grants.gov',
                        'source_url': f"https://www.grants.gov/search-results-detail/{opp.get('id', '')}",
                        'state': '',
                        'opportunity_type': 'grant',
                        'description': opp.get('synopsis', '')[:2000],
                        'deadline': opp.get('closeDate', ''),
                        'contact_info': opp.get('agencyName', ''),
                        'discovered_at': datetime.utcnow(),
                    })
        except Exception as e:
            logger.error(f"Grants.gov search error: {e}")

    return results


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


def classify_news_signal(text):
    """Classify a news headline into signal type."""
    text_lower = text.lower()
    if any(w in text_lower for w in ['rfp', 'bid', 'solicitation', 'proposal', 'procurement']):
        return 'rfp'
    if any(w in text_lower for w in ['contract', 'award', 'vendor', 'selected']):
        return 'contract_change'
    if any(w in text_lower for w in ['complaint', 'issue', 'problem', 'failure', 'wait time', 'overwhelmed']):
        return 'service_issue'
    if any(w in text_lower for w in ['funding', 'budget', 'grant', 'appropriation', 'million']):
        return 'funding'
    if any(w in text_lower for w in ['disaster', 'emergency', 'hurricane', 'wildfire', 'flood', 'tornado']):
        return 'disaster'
    return 'news'


def run_all_scrapers(sam_api_key=''):
    """Run all scrapers and return combined results."""
    all_results = []

    logger.info("Running SAM.gov scraper...")
    all_results.extend(search_sam_gov(sam_api_key))

    logger.info("Running Google News scraper...")
    all_results.extend(search_google_news())

    logger.info("Running Grants.gov scraper...")
    all_results.extend(search_grants_gov())

    logger.info(f"Total results found: {len(all_results)}")
    return all_results
