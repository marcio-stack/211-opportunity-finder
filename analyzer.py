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

        prompt = f"""Analyze this opportunity for a BPO company called Frontline Group that specializes in 211 information and referral services. Frontline provides:
- Surge staffing support for 211 call centers
- After-hours and overflow coverage
- Disaster response agent deployment
- Managed workflow solutions (Frontline Connect Workflows)
- Interaction analytics and insights (Frontline Connect Insights)
- External agent monitoring (Ternio)
- Inform USA-compliant operations
- 20+ years of CX experience
- FedRIMP environment, NICE and Zoom certified

Opportunity:
Title: {opportunity.get('title', '')}
Source: {opportunity.get('source', '')}
State: {opportunity.get('state', '')}
Type: {opportunity.get('opportunity_type', '')}
Description: {opportunity.get('description', '')[:1500]}
Deadline: {opportunity.get('deadline', '')}

Respond in JSON format only:
{{
    "relevance_score": <1-100 integer, 100 = perfect fit>,
    "analysis": "<2-3 sentences explaining why this is or isn't relevant to Frontline>",
    "recommended_action": "<specific next step Frontline should take>",
    "urgency": "<immediate|high|medium|low>"
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
    """Rule-based scoring when AI is unavailable."""
    score = 30
    title = (opportunity.get('title', '') + ' ' + opportunity.get('description', '')).lower()

    high_value = ['211', 'information and referral', 'crisis line', 'community resource',
                  'helpline', 'hotline', 'human services call']
    medium_value = ['call center', 'contact center', 'bpo', 'surge', 'overflow',
                    'after hours', 'customer service', 'managed services']
    signal_words = ['rfp', 'bid', 'solicitation', 'proposal', 'contract',
                    'vendor', 'procurement', 'award']
    negative = ['construction', 'janitorial', 'landscaping', 'food service', 'IT hardware']

    for kw in high_value:
        if kw in title:
            score += 15
    for kw in medium_value:
        if kw in title:
            score += 8
    for kw in signal_words:
        if kw in title:
            score += 5
    for kw in negative:
        if kw in title:
            score -= 20

    score = max(1, min(100, score))

    if score >= 70:
        urgency = 'high'
        action = 'Review immediately and prepare response'
    elif score >= 50:
        urgency = 'medium'
        action = 'Review within 48 hours'
    else:
        urgency = 'low'
        action = 'Monitor for relevance'

    return {
        'relevance_score': score,
        'analysis': f'Rule-based scoring. Keywords matched in title/description. Score: {score}/100.',
        'recommended_action': action,
        'urgency': urgency,
    }
