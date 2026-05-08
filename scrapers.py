import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import logging
from config import (
    SEARCH_TERMS_SAM, SEARCH_TERMS_GRANTS, SEARCH_TERMS_NEWS,
    NEGATIVE_TITLE_KEYWORDS, POSITIVE_KEYWORDS,
    ORGANIZATIONS_211,
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


def matches_211_organization(title, description=''):
    """Check if an opportunity mentions a known 211 organization."""
    text = (title + ' ' + description).lower()
    for org in ORGANIZATIONS_211:
        org_lower = org.lower()
        if org_lower in text:
            return org
    return None


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


def search_sam_gov_raw_test(api_key, test_term='211'):
    """Comprehensive SAM.gov API diagnostic â tests multiple URL variants."""
    from datetime import datetime, timedelta
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)',
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

    # Test 1: Connectivity
    try:
        ping = requests.get("https://api.sam.gov/", timeout=10, headers=headers)
        result['connectivity'] = {
            'status_code': ping.status_code,
            'response_length': len(ping.text),
            'reachable': True,
        }
    except Exception as e:
        result['connectivity'] = {'reachable': False, 'error': str(e)}

    # Test 2: URL with /prod/ prefix
    try:
        url1 = "https://api.sam.gov/prod/opportunities/v2/search"
        params = {
            'api_key': api_key,
            'postedFrom': posted_from,
            'postedTo': posted_to,
            'limit': 5,
            'offset': 0,
        }
        resp1 = requests.get(url1, params=params, timeout=30, headers=headers)
        result['with_prod'] = {
            'url': url1,
            'status_code': resp1.status_code,
            'response_length': len(resp1.text),
            'response_headers': dict(resp1.headers),
            'response_preview': resp1.text[:500],
        }
        if resp1.status_code == 200:
            data = resp1.json()
            result['with_prod']['total_records'] = data.get('totalRecords', 0)
            result['with_prod']['num_results'] = len(data.get('opportunitiesData', []))
    except Exception as e:
        result['with_prod'] = {'url': url1, 'error': str(e)}

    # Test 3: URL without /prod/ prefix
    try:
        url2 = "https://api.sam.gov/opportunities/v2/search"
        resp2 = requests.get(url2, params=params, timeout=30, headers=headers)
        result['without_prod'] = {
            'url': url2,
            'status_code': resp2.status_code,
            'response_length': len(resp2.text),
            'response_headers': dict(resp2.headers),
            'response_preview': resp2.text[:500],
        }
        if resp2.status_code == 200:
            data = resp2.json()
            result['without_prod']['total_records'] = data.get('totalRecords', 0)
            result['without_prod']['num_results'] = len(data.get('opportunitiesData', []))
    except Exception as e:
        result['without_prod'] = {'url': url2, 'error': str(e)}

    # Test 4: API key in header instead of query param
    try:
        url3 = "https://api.sam.gov/prod/opportunities/v2/search"
        params_no_key = {
            'postedFrom': posted_from,
            'postedTo': posted_to,
            'limit': 5,
            'offset': 0,
        }
        headers_with_key = {**headers, 'X-Api-Key': api_key}
        resp3 = requests.get(url3, params=params_no_key, timeout=30, headers=headers_with_key)
        result['header_auth'] = {
            'url': url3,
            'method': 'X-Api-Key header',
            'status_code': resp3.status_code,
            'response_length': len(resp3.text),
            'response_preview': resp3.text[:500],
        }
        if resp3.status_code == 200:
            data = resp3.json()
            result['header_auth']['total_records'] = data.get('totalRecords', 0)
            result['header_auth']['num_results'] = len(data.get('opportunitiesData', []))
    except Exception as e:
        result['header_auth'] = {'error': str(e)}

    return result


def _sam_search_request(api_key, params, headers, label):
    """Make a single SAM.gov API request and return parsed opportunities."""
    url = "https://api.sam.gov/prod/opportunities/v2/search"
    full_params = {
        'api_key': api_key,
        'postedFrom': (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y'),
        'postedTo': datetime.now().strftime('%m/%d/%Y'),
        'limit': 25,
        'offset': 0,
        **params,
    }
    logger.info(f"SAM.gov searching [{label}]: params={json.dumps({k:v for k,v in full_params.items() if k != 'api_key'})}")
    resp = requests.get(url, params=full_params, timeout=30, headers=headers)
    logger.info(f"SAM.gov [{label}]: status={resp.status_code}, length={len(resp.text)}")

    if resp.status_code != 200:
        logger.error(f"SAM.gov [{label}] error: HTTP {resp.status_code} - {resp.text[:500]}")
        return [], f"[{label}]: HTTP {resp.status_code}"

    data = resp.json()
    opps = data.get('opportunitiesData', [])
    logger.info(f"SAM.gov [{label}]: {len(opps)} raw results (total: {data.get('totalRecords', '?')})")
    return opps, None


def search_sam_gov(api_key, keywords=None):
    """Search SAM.gov for 211-related procurement opportunities.

    Strategy:
    1. Search by 211-specific title terms (from config)
    2. Search by NAICS codes for call centers / human services
    3. Search by known 211 organization names
    4. Apply strict relevance filtering â ONLY keep results that match
       211 services, known organizations, or positive keywords
    """
    global _last_diagnostics

    if not api_key:
        _last_diagnostics['sam_gov'] = {'status': 'skipped', 'detail': 'No API key configured'}
        logger.warning("No SAM.gov API key configured â skipping SAM.gov")
        return []

    results = []
    search_terms = keywords or SEARCH_TERMS_SAM
    errors = []
    raw_count = 0
    accepted_count = 0
    rejected_count = 0
    sam_headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)',
        'Accept': 'application/json',
    }

    # --- PHASE 1: Search by 211-specific title terms ---
    logger.info("=== PHASE 1: Title search with 211-specific terms ===")
    for term in search_terms:
        try:
            opps, err = _sam_search_request(api_key, {'title': term}, sam_headers, f"title='{term}'")
            if err:
                errors.append(err)
                continue
            raw_count += len(opps)

            for opp in opps:
                title = opp.get('title', '')
                desc = opp.get('description', '') or ''
                desc = desc[:2000]

                if is_false_positive(title):
                    rejected_count += 1
                    logger.debug(f"  REJECTED (false positive): {title[:80]}")
                    continue

                # For title matches on 211-specific terms, accept if not false positive
                accepted_count += 1
                results.append(_build_sam_result(opp, title, desc))

        except Exception as e:
            logger.error(f"SAM.gov title search error for '{term}': {e}")
            errors.append(f"title='{term}': {str(e)[:100]}")

    # --- PHASE 2: Search by NAICS codes for call center / human services ---
    logger.info("=== PHASE 2: NAICS code search ===")
    naics_codes = [
        ('561422', 'Telemarketing Bureaus and Other Contact Centers'),
        ('561421', 'Telephone Answering Services'),
        ('624190', 'Other Individual and Family Services'),
    ]
    for naics, naics_desc in naics_codes:
        try:
            opps, err = _sam_search_request(api_key, {'ncode': naics}, sam_headers, f"NAICS={naics} ({naics_desc})")
            if err:
                errors.append(err)
                continue
            raw_count += len(opps)

            for opp in opps:
                title = opp.get('title', '')
                desc = opp.get('description', '') or ''
                desc = desc[:2000]

                if is_false_positive(title):
                    rejected_count += 1
                    continue

                # For NAICS matches, also require relevance check
                if is_relevant_to_211_services(title, desc) or matches_211_organization(title, desc):
                    accepted_count += 1
                    results.append(_build_sam_result(opp, title, desc))
                else:
                    rejected_count += 1
                    logger.debug(f"  REJECTED (NAICS not relevant): {title[:80]}")

        except Exception as e:
            logger.error(f"SAM.gov NAICS search error for {naics}: {e}")
            errors.append(f"NAICS={naics}: {str(e)[:100]}")

    # --- PHASE 3: Search by known 211 organization names (top orgs) ---
    logger.info("=== PHASE 3: Organization name search ===")
    # Pick a subset of org names to search (to stay within rate limits)
    # Focus on the parent org types that post RFPs
    org_search_terms = [
        'United Way 211',
        'United Way information referral',
        '211 information referral',
    ]
    for term in org_search_terms:
        try:
            opps, err = _sam_search_request(api_key, {'keyword': term}, sam_headers, f"org-keyword='{term}'")
            if err:
                errors.append(err)
                continue
            raw_count += len(opps)

            for opp in opps:
                title = opp.get('title', '')
                desc = opp.get('description', '') or ''
                desc = desc[:2000]

                if is_false_positive(title):
                    rejected_count += 1
                    continue

                # For org keyword matches, require relevance OR org match
                if is_relevant_to_211_services(title, desc) or matches_211_organization(title, desc):
                    accepted_count += 1
                    results.append(_build_sam_result(opp, title, desc))
                else:
                    rejected_count += 1
                    logger.debug(f"  REJECTED (org search not relevant): {title[:80]}")

        except Exception as e:
            logger.error(f"SAM.gov org search error for '{term}': {e}")
            errors.append(f"org='{term}': {str(e)[:100]}")

    # --- Deduplicate by title ---
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['sam_gov'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': (
            f"3-phase search: {len(search_terms)} title terms + {len(naics_codes)} NAICS codes + "
            f"{len(org_search_terms)} org keywords. "
            f"{raw_count} raw, {accepted_count} accepted, {rejected_count} rejected, "
            f"{len(unique)} unique. Errors: {errors}"
        ),
    }

    logger.info(f"SAM.gov TOTAL: {raw_count} raw, {accepted_count} accepted, {rejected_count} rejected, {len(unique)} unique")
    return unique


def _build_sam_result(opp, title, desc):
    """Build a standardized result dict from a SAM.gov opportunity."""
    return {
        'title': title,
        'source': 'SAM.gov',
        'source_url': f"https://sam.gov/opp/{opp.get('noticeId', '')}/view",
        'state': opp.get('placeOfPerformance', {}).get('state', {}).get('code', '') if isinstance(opp.get('placeOfPerformance'), dict) else '',
        'opportunity_type': classify_lead_type(title, desc, 'SAM.gov'),
        'description': desc,
        'deadline': opp.get('responseDeadLine', ''),
        'contact_info': json.dumps(opp.get('pointOfContact', [])),
        'discovered_at': datetime.utcnow(),
    }


def search_google_news(query=None):
    """Search Google News RSS for 211-related procurement signals."""
    global _last_diagnostics
    results = []
    search_queries = SEARCH_TERMS_NEWS
    errors = []
    raw_count = 0

    for q in search_queries:
        try:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
            logger.info(f"Google News '{q}': status={resp.status_code}")

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
            else:
                errors.append(f"'{q}': HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Google News search error for '{q}': {e}")
            errors.append(f"'{q}': {str(e)[:100]}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['google_news'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': f"Searched {len(search_queries)} queries, {raw_count} raw items, {len(unique)} after filtering. Errors: {errors}" if errors else f"Searched {len(search_queries)} queries, {raw_count} raw items, {len(unique)} after filtering",
    }

    logger.info(f"Google News total: {raw_count} raw, {len(results)} passed filters, {len(unique)} unique")
    return unique


def search_grants_gov(keywords=None):
    """Search Grants.gov for 211-related federal grants."""
    global _last_diagnostics
    results = []
    terms = keywords or SEARCH_TERMS_GRANTS
    errors = []
    raw_count = 0

    for term in terms:
        try:
            url = "https://api.grants.gov/v1/opportunities/search"
            payload = {
                'keyword': term,
                'oppStatuses': 'forecasted,posted',
                'sortBy': 'openDate',
                'sortOrder': 'desc',
                'rows': 25,
            }
            logger.info(f"Grants.gov searching: '{term}'")
            resp = requests.post(url, json=payload, timeout=30,
                                 headers={'Content-Type': 'application/json',
                                          'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
            logger.info(f"Grants.gov v1 API for '{term}': status={resp.status_code}")

            if resp.status_code != 200:
                logger.info(f"Trying legacy Grants.gov API for '{term}'...")
                url = "https://www.grants.gov/grantsws/rest/opportunities/search/"
                params = {
                    'keyword': term,
                    'oppStatus': 'forecasted|posted',
                    'sortBy': 'openDate|desc',
                    'rows': 25,
                }
                resp = requests.get(url, params=params, timeout=30,
                                    headers={'User-Agent': 'Mozilla/5.0 (compatible; FrontlineOpportunityFinder/1.0)'})
                logger.info(f"Grants.gov legacy for '{term}': status={resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                opps = data.get('oppHits', data.get('opportunities', []))
                raw_count += len(opps)
                logger.info(f"Grants.gov '{term}': {len(opps)} raw results")

                for opp in opps:
                    title = opp.get('title', opp.get('opportunityTitle', ''))
                    synopsis = (opp.get('synopsis', opp.get('description', '')) or '')[:2000]

                    if is_false_positive(title):
                        continue

                    if not is_relevant_to_211_services(title, synopsis):
                        text = (title + ' ' + synopsis).lower()
                        if not any(kw in text for kw in ['social services', 'community services',
                                                          'human services', 'crisis services',
                                                          'helpline', 'hotline', 'call center']):
                            continue

                    opp_id = opp.get('id', opp.get('opportunityId', ''))
                    results.append({
                        'title': title,
                        'source': 'Grants.gov',
                        'source_url': f"https://www.grants.gov/search-results-detail/{opp_id}",
                        'state': '',
                        'opportunity_type': classify_lead_type(title, synopsis, 'Grants.gov'),
                        'description': synopsis,
                        'deadline': opp.get('closeDate', opp.get('closeDateStr', '')),
                        'contact_info': opp.get('agencyName', opp.get('agency', '')),
                        'discovered_at': datetime.utcnow(),
                    })
            else:
                error_text = resp.text[:300]
                logger.error(f"Grants.gov error for '{term}': HTTP {resp.status_code} - {error_text}")
                errors.append(f"'{term}': HTTP {resp.status_code}")

        except Exception as e:
            logger.error(f"Grants.gov search error for '{term}': {e}")
            errors.append(f"'{term}': {str(e)[:100]}")

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    _last_diagnostics['grants_gov'] = {
        'status': 'error' if errors and not unique else 'ok' if unique else 'empty',
        'detail': f"Searched {len(terms)} terms, {raw_count} raw results, {len(unique)} after filtering. Errors: {errors}" if errors else f"Searched {len(terms)} terms, {raw_count} raw results, {len(unique)} after filtering",
    }

    logger.info(f"Grants.gov total: {raw_count} raw, {len(results)} passed filters, {len(unique)} unique")
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

    logger.info("=" * 60)
    logger.info("STARTING FULL SCAN")
    logger.info(f"SAM API key present: {bool(sam_api_key)} (length: {len(sam_api_key)})")
    logger.info(f"211 organizations loaded: {len(ORGANIZATIONS_211)}")
    logger.info("=" * 60)

    logger.info("Running SAM.gov scraper...")
    sam_results = search_sam_gov(sam_api_key)
    all_results.extend(sam_results)
    logger.info(f"SAM.gov returned {len(sam_results)} leads")

    logger.info("Running Google News scraper...")
    news_results = search_google_news()
    all_results.extend(news_results)
    logger.info(f"Google News returned {len(news_results)} leads")

    logger.info("Running Grants.gov scraper...")
    grants_results = search_grants_gov()
    all_results.extend(grants_results)
    logger.info(f"Grants.gov returned {len(grants_results)} leads")

    logger.info(f"SCAN COMPLETE: Total {len(all_results)} leads (SAM: {len(sam_results)}, News: {len(news_results)}, Grants: {len(grants_results)})")
    return all_results
