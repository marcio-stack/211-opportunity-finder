import json
import logging

logger = logging.getLogger(__name__)


def analyze_opportunity(opportunity, api_key=''):
    """Use Claude to analyze and score an opportunity for Frontline relevance."""
    if not api_key:
        return score_without_ai(opportunity)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a lead qualification analyst for Frontline Group, a BPO company specializing in 211 information and referral services. Score this lead for sales potential.

Frontline provides:
- Surge staffing support for 211 call centers
- After-hours and overflow coverage
- Disaster response agent deployment
- Managed workflow solutions (Frontline Connect Workflows)
- Interaction analytics and insights (Frontline Connect Insights)
- External agent monitoring (Ternio)
- Inform USA-compliant operations
- 20+ years of CX experience
- FedRAMP environment, NICE and Zoom certified

Lead:
Title: {opportunity.get('title', '')}
Source: {opportunity.get('source', '')}
State: {opportunity.get('state', '')}
Type: {opportunity.get('opportunity_type', '')}
Description: {opportunity.get('description', '')[:1500]}
Deadline: {opportunity.get('deadline', '')}

SCORING RULES:
- 80-100: Direct RFP/procurement for 211, call center, or I&R services where Frontline can bid
- 60-79: Strong signal — funding for 211 expansion, contract expiry, or service gap Frontline could fill
- 40-59: Moderate signal — related grant/funding, vendor transition, or adjacent opportunity
- 20-39: Weak signal — tangentially related, worth monitoring
- 1-19: Not relevant — false positive, wrong industry, or no actionable lead

Respond in JSON format only:
{{
    "relevance_score": <1-100 integer>,
    "lead_quality": "<hot|warm|cool|cold>",
    "analysis": "<2-3 sentences: why this is/isn't a good lead for Frontline's sales team>",
    "recommended_action": "<specific next step for Frontline's BD team>",
    "urgency": "<immediate|this_week|this_month|monitor>"
}}"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0]

        result = json.loads(text)
        return result

    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return score_without_ai(opportunity)


def score_without_ai(opportunity):
    """Rule-based lead scoring when AI is unavailable."""
    score = 20  # Start low — must earn points
    title = (opportunity.get('title', '') + ' ' + opportunity.get('description', '')).lower()
    opp_type = opportunity.get('opportunity_type', '')
    source = opportunity.get('source', '')

    # === STRONG LEAD SIGNALS (high score) ===
    hot_keywords = [
        '211 rfp', '211 request for proposal', '211 solicitation',
        '211 call center rfp', '211 contact center rfp',
        'information and referral rfp', 'crisis hotline rfp',
        '211 procurement', '211 bid opportunity',
    ]
    for kw in hot_keywords:
        if kw in title:
            score += 30

    # Direct 211 service keywords
    direct_211 = [
        '211 services', '211 call center', '211 contact center',
        '211 hotline', '211 helpline', '2-1-1 services',
        '211 information and referral', '211 crisis',
    ]
    for kw in direct_211:
        if kw in title:
            score += 15

    # Procurement/RFP signals
    procurement_words = [
        'rfp', 'request for proposal', 'bid', 'solicitation',
        'procurement', 'vendor selection', 'competitive',
        'invitation to bid', 'request for quote',
    ]
    for kw in procurement_words:
        if kw in title:
            score += 10

    # Service type alignment
    service_alignment = [
        'call center', 'contact center', 'bpo', 'surge',
        'overflow', 'after hours', 'after-hours',
        'managed services', 'outsource', 'staffing',
    ]
    for kw in service_alignment:
        if kw in title:
            score += 8

    # === MODERATE SIGNALS ===
    moderate_signals = [
        'information and referral', 'crisis line', 'crisis hotline',
        'community resource', 'human services',
        'helpline', 'united way',
    ]
    for kw in moderate_signals:
        if kw in title:
            score += 6

    # Opportunity type bonuses
    type_bonuses = {
        'rfp': 15,
        'procurement': 12,
        'contract_expiry': 10,
        'service_gap': 8,
        'expansion': 6,
        'funding': 5,
        'grant': 4,
        'disaster_response': 5,
        'contract_award': 3,  # Lower — already awarded, but useful intel
        'market_signal': 2,
    }
    score += type_bonuses.get(opp_type, 0)

    # Source bonuses (SAM.gov = real procurement)
    source_bonuses = {'SAM.gov': 10, 'Grants.gov': 5, 'Google News': 0}
    score += source_bonuses.get(source, 0)

    # === NEGATIVE SIGNALS ===
    noise_keywords = [
        'construction', 'janitorial', 'landscaping', 'food service',
        'it hardware', 'software license', 'real estate',
        'military', 'defense', 'weapons',
    ]
    for kw in noise_keywords:
        if kw in title:
            score -= 25

    # Cap the score
    score = max(1, min(100, score))

    # Determine lead quality and urgency
    if score >= 70:
        quality = 'hot'
        urgency = 'immediate'
        action = 'Review immediately — prepare bid response or reach out to contracting officer'
    elif score >= 50:
        quality = 'warm'
        urgency = 'this_week'
        action = 'Review this week — research the organization and prepare outreach'
    elif score >= 30:
        quality = 'cool'
        urgency = 'this_month'
        action = 'Add to pipeline — monitor for developments and find the right contact'
    else:
        quality = 'cold'
        urgency = 'monitor'
        action = 'Low priority — monitor only, may become relevant later'

    return {
        'relevance_score': score,
        'lead_quality': quality,
        'analysis': f'Lead scored {score}/100 based on keyword matching. '
                     f'Type: {opp_type}. Source: {source}. '
                     f'{"Strong procurement signal detected." if score >= 60 else "Moderate or weak signal — review for relevance."}',
        'recommended_action': action,
        'urgency': urgency,
    }
