"""Seed the database with the master 211 organization list."""

ORGANIZATIONS = [
    {"name": "United Way of Central Alabama 211", "state": "AL", "operator_type": "United Way", "coverage_area": "Central Alabama / Jefferson County", "website": "uwca.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "211 Connects Alabama", "state": "AL", "operator_type": "United Way", "coverage_area": "River Region / Montgomery", "website": "rruw.org", "accredited": True, "funding_source": "United Way"},
    {"name": "Alaska 211", "state": "AK", "operator_type": "United Way", "coverage_area": "Statewide", "website": "alaska211.org", "contact_email": "sbrogan@ak.org", "funding_source": "United Way / State"},
    {"name": "Arizona 211", "state": "AZ", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "211arizona.org", "accredited": True, "funding_source": "State / United Way"},
    {"name": "Arkansas 211", "state": "AR", "operator_type": "United Way", "coverage_area": "Statewide", "website": "ar211.org", "funding_source": "United Way"},
    {"name": "211 LA County", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "Los Angeles County", "website": "211la.org", "contact_name": "Tyler Hughes", "contact_email": "thughes@211la.org", "accredited": True, "funding_source": "County / State / Private", "notes": "Current Frontline client. Largest 211 in US."},
    {"name": "211 San Diego", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "San Diego County", "website": "211sandiego.org", "contact_email": "wyork@211sandiego.org", "accredited": True, "funding_source": "County / United Way"},
    {"name": "211 Orange County", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "Orange County", "website": "211oc.org", "accredited": True, "funding_source": "County / Private"},
    {"name": "Inland SoCal 211", "state": "CA", "operator_type": "United Way", "coverage_area": "Riverside / San Bernardino", "website": "inlandsocaluw.org", "accredited": True, "funding_source": "United Way"},
    {"name": "211 NorCal", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "Northern California", "website": "211norcal.org", "funding_source": "Mixed"},
    {"name": "211 Sacramento", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "Sacramento County", "website": "211sacramento.org", "funding_source": "County"},
    {"name": "211 Bay Area", "state": "CA", "operator_type": "Nonprofit", "coverage_area": "SF Bay Area", "website": "211bayarea.org", "funding_source": "Mixed"},
    {"name": "Colorado 211", "state": "CO", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211colorado.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "211 Connecticut", "state": "CT", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211ct.org", "contact_email": "211ct.cieetta@ctunitedway.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "Delaware 211", "state": "DE", "operator_type": "United Way", "coverage_area": "Statewide", "website": "delaware211.org", "funding_source": "United Way"},
    {"name": "211 Florida (FLAIRS)", "state": "FL", "operator_type": "Nonprofit", "coverage_area": "Statewide coordination", "website": "flairs211.org", "contact_name": "Tori", "contact_email": "tori@flairs211.org", "funding_source": "State"},
    {"name": "211 Broward", "state": "FL", "operator_type": "United Way", "coverage_area": "Broward County", "website": "211-broward.org", "accredited": True, "funding_source": "United Way"},
    {"name": "Heart of Florida United Way 211", "state": "FL", "operator_type": "United Way", "coverage_area": "Central Florida", "website": "hfuw.org", "accredited": True, "funding_source": "United Way"},
    {"name": "United Way of Greater Atlanta 211", "state": "GA", "operator_type": "United Way", "coverage_area": "Metro Atlanta", "website": "211online.unitedwayatlanta.org", "accredited": True, "funding_source": "United Way"},
    {"name": "Aloha United Way 211", "state": "HI", "operator_type": "United Way", "coverage_area": "Statewide", "website": "auw.org", "contact_email": "kzelee@auw.org", "funding_source": "United Way"},
    {"name": "Idaho CareLine 211", "state": "ID", "operator_type": "State Agency", "coverage_area": "Statewide", "website": "211.idaho.gov", "funding_source": "State"},
    {"name": "211 Illinois", "state": "IL", "operator_type": "Nonprofit", "coverage_area": "Statewide coordination", "website": "211illinois.org", "contact_email": "executivedirector@211illinois.org", "funding_source": "State"},
    {"name": "United Way of Metro Chicago 211", "state": "IL", "operator_type": "United Way", "coverage_area": "Chicago / Cook County", "website": "liveunitedchicago.org", "contact_email": "roy.curiale@liveunitedchiago.org", "funding_source": "United Way"},
    {"name": "Indiana 211 (FSSA)", "state": "IN", "operator_type": "State Agency", "coverage_area": "Statewide", "website": "in211.communityos.org", "contact_name": "Tara Morse", "contact_email": "Tara.Morse@fssa.in.gov", "funding_source": "State (FSSA)"},
    {"name": "Iowa 211", "state": "IA", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211iowa.org", "funding_source": "United Way / State"},
    {"name": "211 Kansas", "state": "KS", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211kansas.org", "contact_email": "mhenness@uwsk.org", "funding_source": "United Way"},
    {"name": "Metro United Way 211 Louisville", "state": "KY", "operator_type": "United Way", "coverage_area": "Louisville Metro", "website": "metrounitedway.org", "contact_name": "Mary Luke Noonan", "contact_email": "maryluke.noonan@metrounitedway.org", "funding_source": "United Way"},
    {"name": "Louisiana 211", "state": "LA", "operator_type": "United Way", "coverage_area": "Statewide", "website": "louisiana211.org", "funding_source": "United Way / State"},
    {"name": "211 Maine", "state": "ME", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "211maine.org", "accredited": True, "funding_source": "Nonprofit / State"},
    {"name": "211 Maryland", "state": "MD", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211md.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "Mass 211", "state": "MA", "operator_type": "United Way", "coverage_area": "Statewide", "website": "mass211.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "Michigan 211", "state": "MI", "operator_type": "United Way", "coverage_area": "Statewide", "website": "mi211.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "Greater Twin Cities United Way 211", "state": "MN", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211unitedway.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "Missouri 211", "state": "MO", "operator_type": "United Way", "coverage_area": "Statewide", "website": "mo211.org", "funding_source": "United Way / State"},
    {"name": "Nebraska 211", "state": "NE", "operator_type": "United Way", "coverage_area": "Statewide", "website": "ne211.org", "funding_source": "United Way"},
    {"name": "NJ 211", "state": "NJ", "operator_type": "United Way", "coverage_area": "Statewide", "website": "nj211.org", "contact_email": "rduncan@nj211.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "211 New York State", "state": "NY", "operator_type": "Nonprofit", "coverage_area": "Statewide coordination", "website": "211newyork.org", "funding_source": "State"},
    {"name": "NC 211", "state": "NC", "operator_type": "United Way", "coverage_area": "Statewide", "website": "nc211.org", "accredited": True, "funding_source": "United Way / State"},
    {"name": "LSS 211 Central Ohio", "state": "OH", "operator_type": "Nonprofit", "coverage_area": "Central Ohio", "website": "211centralohio.org", "accredited": True, "funding_source": "Mixed"},
    {"name": "United Way of Greater Cincinnati 211", "state": "OH", "operator_type": "United Way", "coverage_area": "Cincinnati / Hamilton County", "website": "uwgc.org", "contact_email": "moira.weir@uwgc.org", "accredited": True, "funding_source": "United Way"},
    {"name": "211 Oklahoma (Heartline)", "state": "OK", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "211oklahoma.org", "funding_source": "State ($3M via SB 1290)"},
    {"name": "211info Oregon", "state": "OR", "operator_type": "Nonprofit", "coverage_area": "Oregon / SW Washington", "website": "211info.org", "contact_name": "Kerry Hoeschen", "contact_email": "kerry.hoeschen@211info.org", "accredited": True, "funding_source": "State / Nonprofit"},
    {"name": "PA 211", "state": "PA", "operator_type": "United Way", "coverage_area": "Statewide", "website": "pa211.org", "accredited": True, "funding_source": "United Way / State ($750K/yr)"},
    {"name": "211 Rhode Island", "state": "RI", "operator_type": "United Way", "coverage_area": "Statewide", "website": "unitedwayri.org", "contact_name": "Marleny Perez", "contact_email": "marleny.perez@unitedwayri.org", "funding_source": "United Way"},
    {"name": "SC 211", "state": "SC", "operator_type": "United Way", "coverage_area": "Statewide", "website": "uwasc.org", "contact_email": "elizabeth.houck@uwasc.org", "funding_source": "United Way"},
    {"name": "211 Helpline Center", "state": "SD", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "helplinecenter.org", "contact_email": "jamie.cody@helplinecenter.org", "funding_source": "Nonprofit"},
    {"name": "Tennessee 211", "state": "TN", "operator_type": "United Way", "coverage_area": "Statewide", "website": "tn211.myresourcedirectory.com", "funding_source": "United Way / State"},
    {"name": "211 Texas (HHSC)", "state": "TX", "operator_type": "State Agency", "coverage_area": "Statewide (25 AICs)", "website": "211texas.org", "accredited": True, "funding_source": "State (HHSC)", "notes": "Largest state 211 system. 3.5M calls/year."},
    {"name": "Utah 211", "state": "UT", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211utah.org", "funding_source": "United Way / State"},
    {"name": "211 Virginia", "state": "VA", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "211virginia.org", "accredited": True, "funding_source": "Nonprofit / State"},
    {"name": "Washington 211", "state": "WA", "operator_type": "Nonprofit", "coverage_area": "Statewide", "website": "wa211.org", "funding_source": "State / Nonprofit"},
    {"name": "Wisconsin 211", "state": "WI", "operator_type": "United Way", "coverage_area": "Statewide", "website": "211wisconsin.org", "funding_source": "United Way / State"},
    {"name": "DC 211", "state": "DC", "operator_type": "United Way", "coverage_area": "District of Columbia", "website": "dc211.org", "funding_source": "United Way"},
]


def seed_organizations(db, Organization):
    """Seed the database with known 211 organizations."""
    if Organization.query.count() > 0:
        return 0

    count = 0
    for org_data in ORGANIZATIONS:
        org = Organization(
            name=org_data['name'],
            state=org_data.get('state', ''),
            operator_type=org_data.get('operator_type', ''),
            coverage_area=org_data.get('coverage_area', ''),
            website=org_data.get('website', ''),
            contact_name=org_data.get('contact_name', ''),
            contact_email=org_data.get('contact_email', ''),
            accredited=org_data.get('accredited', False),
            funding_source=org_data.get('funding_source', ''),
            notes=org_data.get('notes', ''),
        )
        db.session.add(org)
        count += 1

    db.session.commit()
    return count
