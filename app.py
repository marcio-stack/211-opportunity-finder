import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler
from models import db, Organization, Opportunity, SearchLog
from scrapers import run_all_scrapers
from analyzer import analyze_opportunity
from seed_data import seed_organizations
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
scheduler = APScheduler()


def run_scheduled_scan():
    """Run all scrapers and process results."""
    with app.app_context():
        logger.info("Starting scheduled scan...")
        log = SearchLog(search_type='scheduled', query='all', source='all_scrapers')

        try:
            results = run_all_scrapers(sam_api_key=app.config.get('SAM_API_KEY', ''))
            log.results_found = len(results)
            new_count = 0

            for r in results:
                existing = Opportunity.query.filter_by(
                    title=r['title'], source=r['source']
                ).first()

                if not existing:
                    analysis = analyze_opportunity(r, app.config.get('ANTHROPIC_API_KEY', ''))

                    opp = Opportunity(
                        title=r['title'],
                        source=r['source'],
                        source_url=r.get('source_url', ''),
                        state=r.get('state', ''),
                        opportunity_type=r.get('opportunity_type', 'unknown'),
                        description=r.get('description', ''),
                        deadline=r.get('deadline', ''),
                        contact_info=r.get('contact_info', ''),
                        relevance_score=analysis.get('relevance_score', 0),
                        ai_analysis=analysis.get('analysis', ''),
                        status='new',
                    )
                    db.session.add(opp)
                    new_count += 1

            log.new_opportunities = new_count
            log.status = 'completed'

        except Exception as e:
            logger.error(f"Scheduled scan error: {e}")
            log.status = 'error'
            log.error = str(e)

        db.session.add(log)
        db.session.commit()
        logger.info(f"Scan complete. Found {log.results_found} results, {log.new_opportunities} new.")


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/stats')
def api_stats():
    total_orgs = Organization.query.count()
    total_opps = Opportunity.query.count()
    new_opps = Opportunity.query.filter_by(status='new').count()
    high_score = Opportunity.query.filter(Opportunity.relevance_score >= 70).count()
    last_scan = SearchLog.query.order_by(SearchLog.ran_at.desc()).first()

    return jsonify({
        'total_organizations': total_orgs,
        'total_opportunities': total_opps,
        'new_opportunities': new_opps,
        'high_relevance': high_score,
        'last_scan': last_scan.ran_at.isoformat() if last_scan else None,
        'last_scan_results': last_scan.results_found if last_scan else 0,
    })


@app.route('/api/opportunities')
def api_opportunities():
    status = request.args.get('status', '')
    state = request.args.get('state', '')
    opp_type = request.args.get('type', '')
    min_score = request.args.get('min_score', 0, type=int)
    sort = request.args.get('sort', 'relevance_score')
    order = request.args.get('order', 'desc')

    query = Opportunity.query
    if status:
        query = query.filter_by(status=status)
    if state:
        query = query.filter_by(state=state)
    if opp_type:
        query = query.filter_by(opportunity_type=opp_type)
    if min_score:
        query = query.filter(Opportunity.relevance_score >= min_score)

    if order == 'desc':
        query = query.order_by(db.desc(getattr(Opportunity, sort, Opportunity.relevance_score)))
    else:
        query = query.order_by(getattr(Opportunity, sort, Opportunity.relevance_score))

    opps = query.limit(100).all()
    return jsonify([{
        'id': o.id,
        'title': o.title,
        'source': o.source,
        'source_url': o.source_url,
        'state': o.state,
        'opportunity_type': o.opportunity_type,
        'description': o.description[:300] if o.description else '',
        'deadline': o.deadline,
        'relevance_score': o.relevance_score,
        'ai_analysis': o.ai_analysis,
        'status': o.status,
        'assigned_to': o.assigned_to,
        'notes': o.notes,
        'discovered_at': o.discovered_at.isoformat() if o.discovered_at else '',
    } for o in opps])


@app.route('/api/opportunities/<int:opp_id>', methods=['PATCH'])
def update_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    data = request.json
    if 'status' in data:
        opp.status = data['status']
    if 'assigned_to' in data:
        opp.assigned_to = data['assigned_to']
    if 'notes' in data:
        opp.notes = data['notes']
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/organizations')
def api_organizations():
    state = request.args.get('state', '')
    op_type = request.args.get('type', '')

    query = Organization.query
    if state:
        query = query.filter_by(state=state)
    if op_type:
        query = query.filter_by(operator_type=op_type)

    orgs = query.order_by(Organization.state).all()
    return jsonify([{
        'id': o.id,
        'name': o.name,
        'state': o.state,
        'operator_type': o.operator_type,
        'coverage_area': o.coverage_area,
        'website': o.website,
        'contact_name': o.contact_name,
        'contact_email': o.contact_email,
        'accredited': o.accredited,
        'funding_source': o.funding_source,
        'notes': o.notes,
    } for o in orgs])


@app.route('/api/search', methods=['POST'])
def manual_search():
    """Run a manual search with custom query."""
    data = request.json
    query_text = data.get('query', '')

    if not query_text:
        return jsonify({'error': 'Query required'}), 400

    log = SearchLog(search_type='manual', query=query_text, source='manual_search')
    results = run_all_scrapers(sam_api_key=app.config.get('SAM_API_KEY', ''))

    filtered = [r for r in results if query_text.lower() in
                (r.get('title', '') + r.get('description', '')).lower()]

    new_count = 0
    for r in filtered:
        existing = Opportunity.query.filter_by(title=r['title'], source=r['source']).first()
        if not existing:
            analysis = analyze_opportunity(r, app.config.get('ANTHROPIC_API_KEY', ''))
            opp = Opportunity(
                title=r['title'], source=r['source'],
                source_url=r.get('source_url', ''),
                state=r.get('state', ''),
                opportunity_type=r.get('opportunity_type', 'unknown'),
                description=r.get('description', ''),
                deadline=r.get('deadline', ''),
                relevance_score=analysis.get('relevance_score', 0),
                ai_analysis=analysis.get('analysis', ''),
                status='new',
            )
            db.session.add(opp)
            new_count += 1

    log.results_found = len(filtered)
    log.new_opportunities = new_count
    log.status = 'completed'
    db.session.add(log)
    db.session.commit()

    return jsonify({'results_found': len(filtered), 'new_added': new_count})


@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Manually trigger a full scan."""
    run_scheduled_scan()
    return jsonify({'success': True, 'message': 'Scan completed'})


with app.app_context():
    db.create_all()
    count = seed_organizations(db, Organization)
    if count:
        logger.info(f"Seeded {count} organizations")

scheduler.init_app(app)
scheduler.add_job(
    id='daily_scan',
    func=run_scheduled_scan,
    trigger='interval',
    hours=12,
    next_run_time=datetime.utcnow(),
)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
