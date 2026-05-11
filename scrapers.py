import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import logging
import time
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
    '211_ndp': {'status': 'not_run', 'detail': ''},
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

    Optimized to avoid rate limiting:
    - Reduced from 15 to 5 search terms
    - 8-second delay between API calls
    - Single combined search approach
    """
    global _last_diagnostics

    if not api_key:
        _last_diagnostics['sam_gov'] = {'status': 'skipped', 'detail': 'No API key configured'}
        return []

    _last_diagnostics['sam_gov'] = {'status': 'running', 'detail': ''}

    results = []
    seen_ids = set()
    base_url = 'https://api.sam.gov/opportunities/v2/search'

    # Reduced search terms - 5 high-value queries instead of 15
    search_terms = [
        '211 call center',
        'contact center services',
        'crisis hotline',
        'information referral services',
        'call center outsourcing',
    ]

    if keywords:
        search_terms = keywords if isinstance(keywords, list) else [keywords]

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    total_found = 0
    errors = []
    successful_queries = 0

    for i, term in enumerate(search_terms):
        try:
            # 8-second delay between requests to avoid rate limiting
            if i > 0:
                time.sleep(8)

            params = {
                'api_key': api_key,
                'keyword': term,
                'postedFrom': (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y'),
                'limit': 25,
                'offset': 0,
            }

            logger.info(f"SAM.gov search {i+1}/{len(search_terms)}: '{term}'")
            response = requests.get(base_url, params=params, headers=headers, timeout=30)

            if response.status_code == 429:
                wait_time = 30
                logger.warning(f"SAM.gov rate limited on '{term}', waiting {wait_time}s...")
                errors.append(f"429 on '{term}' - backing off {wait_time}s")
                time.sleep(wait_time)
                # Retry once after waiting
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                if response.status_code == 429:
                    errors.append(f"429 again on '{term}' after retry")
                    continue

            if response.status_code != 200:
                errors.append(f"HTTP {response.status_code} on '{term}'")
                continue

            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            successful_queries += 1

            for opp in opportunities:
                opp_id = opp.get('noticeId', '')
                if opp_id in seen_ids:
                    continue
                seen_ids.add(opp_id)

                title = opp.get('title', '')
                description = opp.get('description', title)

                # Check relevance - must relate to 211, call centers, or contact centers
                text_check = (title + ' ' + description).lower()
                relevant_terms = ['211', 'call center', 'contact center', 'hotline',
                                  'helpline', 'crisis line', 'information referral',
                                  'customer service', 'bpo', 'outsourc']
                if not any(rt in text_check for rt in relevant_terms):
                    continue

                if is_false_positive(title):
                    continue

                result = {
                    'title': title,
                    'description': description[:500],
                    'url': f"https://sam.gov/opp/{opp_id}/view",
                    'source': 'sam_gov',
                    'state': extract_state_from_text(
                        title + ' ' + opp.get('officeAddress', {}).get('state', '')
                    ),
                    'posted_date': opp.get('postedDate', ''),
                    'due_date': opp.get('responseDeadLine', ''),
                    'found_date': datetime.utcnow().isoformat(),
                }
                results.append(result)

            total_found += len(opportunities)

        except requests.exceptions.Timeout:
            errors.append(f"Timeout on '{term}'")
        except Exception as e:
            errors.append(f"Error on '{term}': {str(e)[:100]}")

    # Update diagnostics
    status = 'success' if successful_queries > 0 else 'error'
    if successful_queries > 0 and errors:
        status = 'partial'

    detail = f"{successful_queries}/{len(search_terms)} queries OK, {len(results)} relevant of {total_found} total"
    if errors:
        detail += f" | Errors: {'; '.join(errors[:3])}"

    _last_diagnostics['sam_gov'] = {
        'status': status,
        'detail': detail,
        'total_raw': total_found,
        'total_relevant': len(results),
        'queries_successful': successful_queries,
        'queries_total': len(search_terms),
    }

    logger.info(f"SAM.gov: {detail}")
    return results

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
    """Search Google News via RSS feeds for 211/call center opportunities."""
    results = []
    _last_diagnostics['google_news'] = {'status': 'running', 'detail': ''}

    search_queries = [
        '211 call center contract OR RFP OR award',
        '211 information referral services procurement',
        'call center government contract award',
        'contact center BPO government RFP',
        '211 helpline outsourcing OR vendor OR partner',
        'crisis hotline call center services RFP',
    ]

    if query:
        search_queries = [query]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for q in search_queries:
        try:
            encoded_query = requests.utils.quote(q)
            rss_url = f'https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en'
            resp = requests.get(rss_url, headers=headers, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"Google News RSS returned {resp.status_code} for query: {q}")
                continue

            # Parse RSS XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            channel = root.find('channel')
            if channel is None:
                continue

            items = channel.findall('item')
            logger.info(f"Google News RSS: {len(items)} items for '{q}'")

            for item in items[:10]:
                title_el = item.find('title')
                link_el = item.find('link')
                pub_date_el = item.find('pubDate')
                source_el = item.find('source')

                title = title_el.text if title_el is not None else ''
                link = link_el.text if link_el is not None else ''
                pub_date = pub_date_el.text if pub_date_el is not None else ''
                source_name = source_el.text if source_el is not None else 'Google News'

                if not title:
                    continue

                # Filter for relevance
                title_lower = title.lower()
                relevant_terms = ['211', 'call center', 'contact center', 'rfp',
                                  'contract', 'award', 'procurement', 'helpline',
                                  'crisis line', 'bpo', 'outsourc']
                if not any(term in title_lower for term in relevant_terms):
                    continue

                if is_false_positive(title):
                    continue

                state = extract_state_from_text(title)

                results.append({
                    'title': title,
                    'source': 'google_news',
                    'source_url': link,
                    'state': state,
                    'published_date': pub_date,
                    'description': f"Source: {source_name}. Published: {pub_date}",
                    'relevance_score': 0.6,
                })

            time.sleep(2)  # Rate limiting between queries

        except Exception as e:
            logger.error(f"Google News RSS error for '{q}': {str(e)}")
            continue

    _last_diagnostics['google_news'] = {
        'status': 'success' if results else 'no_results',
        'detail': f'Found {len(results)} news leads via RSS'
    }
    logger.info(f"Google News total: {len(results)} relevant results")
    return results


def search_grants_gov(keywords=None):
    """Search Grants.gov for relevant federal grant opportunities using their public search."""
    results = []
    _last_diagnostics['grants_gov'] = {'status': 'running', 'detail': ''}

    search_keywords = keywords or [
        'call center services',
        '211 information referral',
        'contact center',
        'crisis hotline',
        'telephone assistance',
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html',
    }

    errors = []

    for keyword in search_keywords:
        try:
            # Try the Grants.gov opportunities API (v2 format)
            encoded = requests.utils.quote(keyword)
            search_url = f'https://www.grants.gov/grantsws/rest/opportunities/search/csv.json?keyword={encoded}&oppStatuses=forecasted|posted&sortBy=openDate|desc&rows=10'
            resp = requests.get(search_url, headers=headers, timeout=20)

            if resp.status_code != 200:
                # Try alternate: the XML search
                search_url = f'https://www.grants.gov/grantsws/rest/opportunities/search/xml?keyword={encoded}&oppStatuses=forecasted|posted&sortBy=openDate|desc&rows=10'
                resp = requests.get(search_url, headers=headers, timeout=20)

            if resp.status_code != 200:
                # Try the newer grants API
                api_url = 'https://api.grants.gov/v1/opportunities/search'
                payload = {'keyword': keyword, 'status': 'posted,forecasted', 'limit': 10, 'order': 'desc', 'sort': 'openDate'}
                resp = requests.get(api_url, params=payload, headers=headers, timeout=20)

            if resp.status_code != 200:
                # Last resort: scrape the HTML search page
                html_url = f'https://www.grants.gov/search-grants?keyword={encoded}'
                resp = requests.get(html_url, headers=headers, timeout=20)
                if resp.status_code == 200 and '<' in resp.text[:10]:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # Look for grant listing elements
                    listings = soup.find_all(['div', 'tr', 'a'], class_=lambda c: c and ('grant' in str(c).lower() or 'opportunity' in str(c).lower() or 'result' in str(c).lower()))
                    if not listings:
                        listings = soup.find_all('a', href=lambda h: h and '/search-results-detail/' in str(h))
                    
                    for item in listings[:10]:
                        title = item.get_text(strip=True)[:200]
                        href = item.get('href', '')
                        if href and not href.startswith('http'):
                            href = f'https://www.grants.gov{href}'
                        if title and len(title) > 10:
                            if is_false_positive(title):
                                continue
                            state = extract_state_from_text(title)
                            results.append({
                                'title': title,
                                'source': 'grants_gov',
                                'source_url': href or 'https://www.grants.gov',
                                'state': state,
                                'published_date': '',
                                'description': f'Found via Grants.gov search for: {keyword}',
                                'relevance_score': 0.65,
                            })
                    logger.info(f"Grants.gov HTML: found {len(listings)} items for '{keyword}'")
                    time.sleep(2)
                    continue
                else:
                    errors.append(f'{keyword}: HTTP {resp.status_code}')
                    continue

            # Parse JSON response
            try:
                data = resp.json()
            except Exception:
                # Maybe XML response
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.content)
                    items = root.findall('.//' + '{http://apply.grants.gov/system/OpportunityDetail-V1.0}OpportunityDetail') or root.findall('.//OpportunityDetail') or root.findall('.//opportunity')
                    logger.info(f"Grants.gov XML: {len(items)} items for '{keyword}'")
                    for item in items[:10]:
                        title_el = item.find('.//OpportunityTitle') or item.find('.//title')
                        number_el = item.find('.//OpportunityNumber') or item.find('.//number')
                        agency_el = item.find('.//AgencyName') or item.find('.//agency')
                        title = title_el.text if title_el is not None else ''
                        opp_num = number_el.text if number_el is not None else ''
                        agency = agency_el.text if agency_el is not None else ''
                        if title and not is_false_positive(title):
                            results.append({
                                'title': title,
                                'source': 'grants_gov',
                                'source_url': f'https://www.grants.gov/search-results-detail/{opp_num}' if opp_num else 'https://www.grants.gov',
                                'state': extract_state_from_text(f'{title} {agency}'),
                                'published_date': '',
                                'description': f'Agency: {agency}',
                                'relevance_score': 0.7,
                            })
                except Exception as xml_err:
                    errors.append(f'{keyword}: parse error: {str(xml_err)[:100]}')
                    continue
                time.sleep(2)
                continue

            # Handle JSON response structures
            opps = []
            if isinstance(data, dict):
                opps = data.get('oppHits', data.get('opportunities', data.get('results', [])))
                if not opps and 'response' in data:
                    opps = data.get('response', {}).get('body', {}).get('oppHits', [])

            logger.info(f"Grants.gov JSON: {len(opps)} results for '{keyword}'")

            for opp in opps[:10]:
                title = opp.get('title', opp.get('oppTitle', ''))
                opp_number = opp.get('number', opp.get('oppNumber', opp.get('id', '')))
                agency = opp.get('agency', opp.get('agencyName', ''))
                close_date = opp.get('closeDate', opp.get('closingDate', ''))
                open_date = opp.get('openDate', opp.get('openingDate', ''))
                desc = opp.get('description', opp.get('synopsis', ''))

                if not title or is_false_positive(title):
                    continue

                opp_url = f'https://www.grants.gov/search-results-detail/{opp_number}' if opp_number else 'https://www.grants.gov'
                results.append({
                    'title': title,
                    'source': 'grants_gov',
                    'source_url': opp_url,
                    'state': extract_state_from_text(f'{title} {desc} {agency}'),
                    'published_date': open_date,
                    'description': f'Agency: {agency}. Closes: {close_date}. {desc[:200] if desc else ""}',
                    'relevance_score': 0.7,
                    'opportunity_number': opp_number,
                })

            time.sleep(2)

        except Exception as e:
            errors.append(f'{keyword}: {str(e)[:100]}')
            logger.error(f"Grants.gov error for '{keyword}': {str(e)}")
            continue

    detail = f'Found {len(results)} grant opportunities'
    if errors:
        detail += f'. Errors: {"; ".join(errors[:5])}'
    _last_diagnostics['grants_gov'] = {
        'status': 'success' if results else ('error' if errors else 'no_results'),
        'detail': detail
    }
    logger.info(f"Grants.gov total: {len(results)} results")
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


# --- 211 National Data Platform (NDP) Scraper ---

NDP_BASE_URL = 'https://api.211.org/search/v1/api'

NDP_KEYWORDS = [
    'call center',
    'contact center', 
    'information and referral',
    '211',
    'crisis line',
    'helpline',
    'telephone assistance',
    'BPO',
]


def search_211_ndp(ndp_api_key=''):
    """Search 211 National Data Platform for opportunities related to call center services."""
    results = []
    _last_diagnostics['211_ndp'] = {'status': 'running', 'detail': ''}

    if not ndp_api_key:
        _last_diagnostics['211_ndp'] = {
            'status': 'skipped',
            'detail': 'No NDP API key configured'
        }
        logger.warning("211 NDP: No API key configured, skipping")
        return results

    headers = {
        'Ocp-Apim-Subscription-Key': ndp_api_key,
        'Accept': 'application/json',
    }

    try:
        # Step 1: Get list of 211 data owners (centers) for context
        logger.info("211 NDP: Fetching data owners list...")
        owners_url = f'{NDP_BASE_URL}/Filters/DataOwners'
        owners_resp = requests.get(owners_url, headers=headers, timeout=30)
        owners_resp.raise_for_status()
        data_owners = owners_resp.json()
        logger.info(f"211 NDP: Found {len(data_owners)} data owners/centers")

        # Step 2: Search by each keyword
        seen_titles = set()
        for keyword in NDP_KEYWORDS:
            try:
                logger.info(f"211 NDP: Searching for '{keyword}'...")
                search_url = f'{NDP_BASE_URL}/Search/Keyword'
                params = {
                    'Keyword': keyword,
                    'Top': 25,
                    'OrderBy': 'Relevance',
                }
                resp = requests.get(
                    search_url, headers=headers, params=params, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                # Handle response - may be list or dict with results key
                items = data if isinstance(data, list) else data.get('results', data.get('Items', []))

                for item in items:
                    title = item.get('Name', item.get('name', item.get('ServiceName', '')))
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    # Extract location/state info
                    location = item.get('Location', item.get('location', {}))
                    state = ''
                    if isinstance(location, dict):
                        state = location.get('State', location.get('state', ''))
                    elif isinstance(location, str):
                        state = extract_state_from_text(location)

                    # Build description from available fields
                    desc_parts = []
                    org_name = item.get('OrganizationName', item.get('organizationName', ''))
                    if org_name:
                        desc_parts.append(f"Organization: {org_name}")
                    svc_desc = item.get('Description', item.get('description', ''))
                    if svc_desc:
                        desc_parts.append(svc_desc[:500])
                    taxonomy = item.get('Taxonomy', item.get('taxonomy', ''))
                    if taxonomy:
                        desc_parts.append(f"Category: {taxonomy}")

                    description = ' | '.join(desc_parts) if desc_parts else f'211 service: {keyword}'

                    # Determine if this is a potential opportunity for Frontline
                    source_url = item.get('URL', item.get('url', ''))
                    if not source_url:
                        source_url = f'https://apiportal.211.org'

                    # Check relevance - is this a 211 center that might need call center services?
                    contact = item.get('Phone', item.get('phone', ''))
                    email = item.get('Email', item.get('email', ''))
                    contact_info = f"Phone: {contact}" if contact else ''
                    if email:
                        contact_info += f" | Email: {email}" if contact_info else f"Email: {email}"

                    results.append({
                        'title': f"211 Service: {title}",
                        'source': '211_ndp',
                        'source_url': source_url,
                        'state': state or extract_state_from_text(description),
                        'opportunity_type': '211_service',
                        'description': description,
                        'deadline': '',
                        'contact_info': contact_info,
                    })

                logger.info(f"211 NDP: '{keyword}' returned {len(items)} items")

            except requests.exceptions.RequestException as e:
                logger.warning(f"211 NDP: Error searching '{keyword}': {e}")
                continue

        # Filter out false positives
        filtered = [r for r in results if not is_false_positive(r)]

        _last_diagnostics['211_ndp'] = {
            'status': 'completed',
            'detail': f'Found {len(filtered)} relevant services from {len(seen_titles)} total',
            'data_owners_count': len(data_owners),
            'keywords_searched': len(NDP_KEYWORDS),
        }
        logger.info(f"211 NDP: Complete. {len(filtered)} relevant results (filtered from {len(results)})")
        return filtered

    except requests.exceptions.RequestException as e:
        _last_diagnostics['211_ndp'] = {
            'status': 'error',
            'detail': str(e)
        }
        logger.error(f"211 NDP scraper error: {e}")
        return results



def run_all_scrapers(sam_api_key='', ndp_api_key=''):
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

    logger.info("Running 211 NDP scraper...")
    ndp_results = search_211_ndp(ndp_api_key)
    all_results.extend(ndp_results)
    logger.info(f"211 NDP returned {len(ndp_results)} leads")

    logger.info(f"SCAN COMPLETE: Total {len(all_results)} leads (SAM: {len(sam_results)}, News: {len(news_results)}, Grants: {len(grants_results)}, 211-NDP: {len(ndp_results)})")
    return all_results
