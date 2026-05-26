import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import logging
import time
from config import (
    SEARCH_TERMS_SAM_211, SEARCH_TERMS_SAM_BPO,
    SEARCH_TERMS_GRANTS_211, SEARCH_TERMS_GRANTS_BPO,
    SEARCH_TERMS_NEWS_211, SEARCH_TERMS_NEWS_BPO,
    NEGATIVE_TITLE_KEYWORDS, POSITIVE_KEYWORDS_211, POSITIVE_KEYWORDS_BPO,
)

logger = logging.getLogger(__name__)

# Track scraper diagnostics for the /api/diagnostics endpoint
_last_diagnostics = {
    'sam_gov': {'status': 'not_run', 'detail': ''},
    'google_news': {'status': 'not_run', 'detail': ''},
    'grants_gov': {'status': 'not_run', 'detail': ''},
}


def get_diagnostics():
    return _last_diagnostics.copy()


def is_false_positive(title):
    """Check if a result is a false positive."""
    title_lower = title.lower()

    # Check for dollar amounts like "$211 million", "$211M", "$211,000"
    if re.search(r'\$\s*211[\s,.\d]*(?:million|billion|m\b|b\b|k\b|,)', title_lower):
        return True

    # Check for highway/route numbers
    if re.search(r'(?:sr|route|highway|interstate|hwy|rd|road)\s*[-]?\s*211', title_lower):
        return True

    # Check negative keywords
    for neg in NEGATIVE_TITLE_KEYWORDS:
        if neg in title_lower:
            has_positive = any(pos in title_lower for pos in POSITIVE_KEYWORDS_211 + POSITIVE_KEYWORDS_BPO)
            if not has_positive:
                return True

    return False


def classify_category(title, description='', search_term=''):
    """Classify an opportunity as '211', 'bpo', or 'both'."""
    text = (title + ' ' + description + ' ' + search_term).lower()

    is_211 = any(kw in text for kw in [
        '211', '2-1-1', 'united way', 'information and referral',
        'crisis hotline', 'crisis line', 'helpline', 'community resource',
        'human services hotline', 'social services hotline',
    ])

    is_bpo = any(kw in text for kw in [
        'bpo', 'business process outsourc', 'contact center outsourc',
        'call center outsourc', 'managed contact center', 'managed call center',
        'customer service outsourc', 'telephone answering',
        'inbound call center', 'omnichannel',
    ])

    # Also check if search term was BPO-category
    if search_term in [t.lower() for t in SEARCH_TERMS_SAM_BPO]:
        is_bpo = True
    if search_term in [t.lower() for t in SEARCH_TERMS_SAM_211]:
        is_211 = True

    if is_211 and is_bpo:
        return 'both'
    elif is_bpo:
        return 'bpo'
    elif is_211:
        return '211'
    else:
        # Default based on content signals
        if any(kw in text for kw in ['call center', 'contact center', 'customer service']):
            return 'bpo'
        return '211'


def is_relevant(title, description=''):
    """Check if content is relevant to 211 services OR BPO/contact center."""
    text = (title + ' ' + description).lower()

    # 211 signals
    signals_211 = [
        '211 services', '211 call center', '211 hotline', '211 helpline',
        '211 contact center', '211 information and referral',
        'information and referral', 'crisis hotline', 'crisis line',
        'community resource', 'human services call',
        'united way 211', '2-1-1',
    ]

    # BPO / Contact center signals
    signals_bpo = [
        'call center rfp', 'contact center rfp', 'call center bid',
        'contact center procurement', 'bpo services',
        'overflow call center', 'surge staffing',
        'after-hours coverage', 'helpline services',
        'call center outsourcing', 'contact center outsourcing',
        'managed contact center', 'inbound call center',
        'customer service center', 'customer care',
        'call center services', 'contact center services',
        'telephone answering', 'omnichannel contact',
        'call center staffing', 'call center operations',
    ]

    for signal in signals_211 + signals_bpo:
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


def search_sam_gov_raw_test(api_key, test_term='call center'):
    """Comprehensive SAM.gov API diagnostic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityRadar/2.0)',
        'Accept': 'application/json',
    }
    result = {
        'api_key_present': bool(api_key),
        'api_key_length': len(api_key) if api_key else 0,
        'api_key_preview': (api_key[:4] + '...' + api_key[-4:]) if api_key and len(api_key) > 8 else 'too_short',
        'test_term': test_term,
    }

    if not api_key:
        result['error'] = 'No SAM_API_KEY environment variable set'
        return result

    posted_from = (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y')
    posted_to = datetime.now().strftime('%m/%d/%Y')
    result['date_range'] = f"{posted_from} to {posted_to}"

    # Test with /prod/ prefix
    try:
        url = "https://api.sam.gov/prod/opportunities/v2/search"
        params = {
            'api_key': api_key,
            'keyword': test_term,
            'postedFrom': posted_from,
            'postedTo': posted_to,
            'limit': 5,
            'offset': 0,
        }
        resp = requests.get(url, params=params, timeout=30, headers=headers)
        result['test_result'] = {
            'url': url,
            'status_code': resp.status_code,
            'response_length': len(resp.text),
            'response_preview': resp.text[:500],
        }
        if resp.status_code == 200:
            data = resp.json()
            result['test_result']['total_records'] = data.get('totalRecords', 0)
            result['test_result']['num_results'] = len(data.get('opportunitiesData', []))
    except Exception as e:
        result['test_result'] = {'error': str(e)}

    return result


def search_sam_gov(api_key, keywords=None):
    """Search SAM.gov for 211 and BPO procurement opportunities."""
    global _last_diagnostics

    if not api_key:
        _last_diagnostics['sam_gov'] = {'status': 'skipped', 'detail': 'No API key configured'}
        logger.warning("No SAM.gov API key configured - skipping")
        return []

    results = []
    errors = []
    raw_count = 0
    sam_headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityRadar/2.0)',
        'Accept': 'application/json',
    }

    # Search both 211 and BPO terms, tagging each with its category source
    all_terms = [(t, '211') for t in SEARCH_TERMS_SAM_211] + [(t, 'bpo') for t in SEARCH_TERMS_SAM_BPO]

    for term, term_category in all_terms:
        try:
            url = "https://api.sam.gov/prod/opportunities/v2/search"
            posted_from = (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y')
            posted_to = datetime.now().strftime('%m/%d/%Y')
            params = {
                'api_key': api_key,
                'keyword': term,  # Use keyword instead of title for broader results
                'postedFrom': posted_from,
                'postedTo': posted_to,
                'limit': 25,
                'offset': 0,
            }
            logger.info(f"SAM.gov searching [{term_category}]: keyword='{term}'")
            resp = requests.get(url, params=params, timeout=30, headers=sam_headers)
            logger.info(f"SAM.gov '{term}': status={resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                opps = data.get('opportunitiesData', [])
                raw_count += len(opps)

                for opp in opps:
                    title = opp.get('title', '')
                    desc = opp.get('description', '') or ''
                    desc = desc[:2000]

                    if is_false_positive(title):
                        continue

                    category = classify_category(title, desc, term.lower())

                    results.append({
                        'title': title,
                        'source': 'SAM.gov',
                        'source_url': f"https://sam.gov/opp/{opp.get('noticeId', '')}/view",
                        'state': opp.get('placeOfPerformance', {}).get('state', {}).get('code', '') if isinstance(opp.get('placeOfPerformance'), dict) else '',
                        'category': category,
                        'opportunity_type': classify_lead_type(title, desc, 'SAM.gov'),
                        'description': desc,
                        'deadline': opp.get('responseDeadLine', ''),
                        'contact_info': json.dumps(opp.get('pointOfContact', [])),
                        'discovered_at': datetime.utcnow(),
                    })

            elif resp.status_code == 429:
                logger.warning(f"SAM.gov rate limited on '{term}' - waiting 10s then continuing")
                errors.append(f"'{term}': Rate limited (429)")
                time.sleep(10)
            else:
                logger.error(f"SAM.gov error for '{term}': HTTP {resp.status_code}")
                errors.append(f"'{term}': HTTP {resp.status_code}")

            # Rate limiting: pause between requests (SAM allows ~10/min)
            time.sleep(3)

        except Exception as e:
            logger.error(f"SAM.gov search error for '{term}': {e}")
            errors.append(f"'{term}': {str(e)[:100]}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['sam_gov'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': f"Searched {len(all_terms)} terms ({len(SEARCH_TERMS_SAM_211)} 211 + {len(SEARCH_TERMS_SAM_BPO)} BPO), {raw_count} raw, {len(unique)} unique. Errors: {errors}" if errors else f"Searched {len(all_terms)} terms, {raw_count} raw, {len(unique)} unique",
    }

    logger.info(f"SAM.gov total: {raw_count} raw, {len(unique)} unique")
    return unique


def search_google_news(query=None):
    """Search Google News RSS for 211 and BPO signals."""
    global _last_diagnostics
    results = []
    errors = []
    raw_count = 0

    all_queries = [(q, '211') for q in SEARCH_TERMS_NEWS_211] + [(q, 'bpo') for q in SEARCH_TERMS_NEWS_BPO]

    for q, q_category in all_queries:
        try:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityRadar/2.0)'})

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'lxml-xml')
                items = soup.find_all('item')
                raw_count += len(items)

                for item in items[:5]:
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')

                    if title:
                        title_text = title.get_text()

                        if is_false_positive(title_text):
                            continue

                        desc_text = desc.get_text() if desc else ''
                        if not is_relevant(title_text, desc_text):
                            continue

                        category = classify_category(title_text, desc_text, q.lower())

                        results.append({
                            'title': title_text,
                            'source': 'Google News',
                            'source_url': link.get_text() if link else '',
                            'state': extract_state_from_text(title_text),
                            'category': category,
                            'opportunity_type': classify_lead_type(title_text, desc_text, 'Google News'),
                            'description': desc_text,
                            'deadline': '',
                            'contact_info': '',
                            'discovered_at': datetime.utcnow(),
                        })
            else:
                errors.append(f"'{q[:30]}': HTTP {resp.status_code}")

            time.sleep(0.5)  # Be nice to Google

        except Exception as e:
            logger.error(f"Google News error for '{q}': {e}")
            errors.append(f"'{q[:30]}': {str(e)[:100]}")

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['google_news'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': f"Searched {len(all_queries)} queries ({len(SEARCH_TERMS_NEWS_211)} 211 + {len(SEARCH_TERMS_NEWS_BPO)} BPO), {raw_count} raw, {len(unique)} unique",
    }

    logger.info(f"Google News total: {raw_count} raw, {len(unique)} unique")
    return unique


def search_grants_gov(keywords=None):
    """Search Grants.gov for 211 and BPO related grants."""
    global _last_diagnostics
    results = []
    errors = []
    raw_count = 0

    all_terms = [(t, '211') for t in SEARCH_TERMS_GRANTS_211] + [(t, 'bpo') for t in SEARCH_TERMS_GRANTS_BPO]

    for term, t_category in all_terms:
        try:
            url = "https://api.grants.gov/v1/opportunities/search"
            payload = {
                'keyword': term,
                'oppStatuses': 'forecasted,posted',
                'sortBy': 'openDate',
                'sortOrder': 'desc',
                'rows': 25,
            }
            logger.info(f"Grants.gov searching [{t_category}]: '{term}'")
            resp = requests.post(url, json=payload, timeout=30,
                                 headers={'Content-Type': 'application/json',
                                          'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityRadar/2.0)'})

            if resp.status_code != 200:
                # Fallback to legacy API
                url = "https://www.grants.gov/grantsws/rest/opportunities/search/"
                params = {
                    'keyword': term,
                    'oppStatus': 'forecasted|posted',
                    'sortBy': 'openDate|desc',
                    'rows': 25,
                }
                resp = requests.get(url, params=params, timeout=30,
                                    headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityRadar/2.0)'})

            if resp.status_code == 200:
                data = resp.json()
                opps = data.get('oppHits', data.get('opportunities', []))
                raw_count += len(opps)

                for opp in opps:
                    title = opp.get('title', opp.get('opportunityTitle', ''))
                    synopsis = (opp.get('synopsis', opp.get('description', '')) or '')[:2000]

                    if is_false_positive(title):
                        continue

                    if not is_relevant(title, synopsis):
                        text = (title + ' ' + synopsis).lower()
                        if not any(kw in text for kw in ['social services', 'community services',
                                                          'human services', 'crisis services',
                                                          'helpline', 'hotline', 'call center',
                                                          'contact center', 'bpo', 'customer service']):
                            continue

                    category = classify_category(title, synopsis, term.lower())
                    opp_id = opp.get('id', opp.get('opportunityId', ''))

                    results.append({
                        'title': title,
                        'source': 'Grants.gov',
                        'source_url': f"https://www.grants.gov/search-results-detail/{opp_id}",
                        'state': '',
                        'category': category,
                        'opportunity_type': classify_lead_type(title, synopsis, 'Grants.gov'),
                        'description': synopsis,
                        'deadline': opp.get('closeDate', opp.get('closeDateStr', '')),
                        'contact_info': opp.get('agencyName', opp.get('agency', '')),
                        'discovered_at': datetime.utcnow(),
                    })
            else:
                errors.append(f"'{term}': HTTP {resp.status_code}")

            time.sleep(1)

        except Exception as e:
            logger.error(f"Grants.gov error for '{term}': {e}")
            errors.append(f"'{term}': {str(e)[:100]}")

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['grants_gov'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': f"Searched {len(all_terms)} terms, {raw_count} raw, {len(unique)} unique",
    }

    logger.info(f"Grants.gov total: {raw_count} raw, {len(unique)} unique")
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
    """Run all scrapers and return combined results."""
    all_results = []

    logger.info("=" * 60)
    logger.info("STARTING OPPORTUNITY RADAR SCAN")
    logger.info(f"SAM API key present: {bool(sam_api_key)}")
    logger.info("=" * 60)

    logger.info("Running SAM.gov scraper...")
    sam_results = search_sam_gov(sam_api_key)
    all_results.extend(sam_results)
    logger.info(f"SAM.gov: {len(sam_results)} opportunities")

    logger.info("Running Google News scraper...")
    news_results = search_google_news()
    all_results.extend(news_results)
    logger.info(f"Google News: {len(news_results)} opportunities")

    logger.info("Running Grants.gov scraper...")
    grants_results = search_grants_gov()
    all_results.extend(grants_results)
    logger.info(f"Grants.gov: {len(grants_results)} opportunities")

    # Count by category
    cat_211 = sum(1 for r in all_results if r.get('category') == '211')
    cat_bpo = sum(1 for r in all_results if r.get('category') == 'bpo')
    cat_both = sum(1 for r in all_results if r.get('category') == 'both')

    logger.info(f"SCAN COMPLETE: {len(all_results)} total (211: {cat_211}, BPO: {cat_bpo}, Both: {cat_both})")
    return all_results
