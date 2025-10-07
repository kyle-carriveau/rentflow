"""
Search Views

Routes and handlers for application-wide search functionality.
"""

from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website.search import search
from website.search.forms import (
    UnitSearchForm, PropertySearchForm, TenantSearchForm,
    LeaseSearchForm, GlobalSearchForm
)
from website.search.utils import (
    build_unit_query, build_property_query, build_tenant_query,
    build_lease_query, global_search, get_search_summary
)
from website.models import Property, Portfolio, Unit


@search.route('/')
@login_required
def index():
    """Main search page with global search functionality."""
    form = GlobalSearchForm(request.args)
    company_id = current_user.get_company_id()

    query_string = request.args.get('query', '').strip()
    resource_type = request.args.get('resource_type', 'all')

    results = {'units': [], 'properties': [], 'tenants': [], 'leases': []}
    summary = {'total': 0, 'units_count': 0, 'properties_count': 0, 'tenants_count': 0, 'leases_count': 0}

    if query_string:
        results = global_search(company_id, query_string, resource_type)
        summary = get_search_summary(results)

    return render_template(
        'search/search_results.html',
        form=form,
        query=query_string,
        results=results,
        summary=summary,
        resource_type=resource_type
    )


@search.route('/api/autocomplete')
@login_required
def autocomplete_api():
    """
    JSON API endpoint for search autocomplete.

    Returns quick results for navbar autocomplete dropdown.
    """
    company_id = current_user.get_company_id()
    query_string = request.args.get('q', '').strip()

    if not query_string or len(query_string) < 2:
        return jsonify({'results': []})

    # Perform global search with limited results
    results = global_search(company_id, query_string, 'all')

    # Format results for autocomplete
    autocomplete_results = []

    # Add unit results
    for unit in results.get('units', [])[:5]:
        autocomplete_results.append({
            'type': 'unit',
            'id': unit.uuid,
            'title': unit.name,
            'subtitle': f"{unit.property_ref.name if unit.property_ref else 'Unknown Property'}",
            'icon': 'fa-home',
            'url': url_for('unit.show', uuid=unit.uuid)
        })

    # Add property results
    for prop in results.get('properties', [])[:5]:
        autocomplete_results.append({
            'type': 'property',
            'id': prop.uuid,
            'title': prop.name,
            'subtitle': prop.address or 'No address',
            'icon': 'fa-building',
            'url': url_for('property.home', uuid=prop.uuid)
        })

    # Add tenant results
    for tenant in results.get('tenants', [])[:5]:
        autocomplete_results.append({
            'type': 'tenant',
            'id': tenant.uuid,
            'title': f"{tenant.first_name} {tenant.last_name}",
            'subtitle': tenant.email or tenant.phone or '',
            'icon': 'fa-user',
            'url': url_for('tenant.home', uuid=tenant.uuid)
        })

    return jsonify({'results': autocomplete_results})


@search.route('/units')
@login_required
def units():
    """
    Advanced unit search page.

    This is a dedicated search interface for finding units with multiple filters.
    """
    company_id = current_user.get_company_id()
    form = UnitSearchForm(request.args)

    # Populate property choices
    properties = Property.query.filter_by(company_id=company_id).order_by(Property.name.asc()).all()
    form.property_id.choices = [('', 'All Properties')] + [(p.uuid, p.name) for p in properties]

    # Build filter dictionary from form data
    filters = {}
    if form.query.data:
        filters['query'] = form.query.data
    if form.bedrooms.data:
        filters['bedrooms'] = form.bedrooms.data
    if form.bathrooms.data:
        filters['bathrooms'] = form.bathrooms.data
    if form.occupancy_status.data:
        filters['occupancy_status'] = form.occupancy_status.data
    if form.property_id.data:
        filters['property_id'] = form.property_id.data
    if form.min_rent.data:
        filters['min_rent'] = form.min_rent.data
    if form.max_rent.data:
        filters['max_rent'] = form.max_rent.data
    if form.min_sqft.data:
        filters['min_sqft'] = form.min_sqft.data
    if form.max_sqft.data:
        filters['max_sqft'] = form.max_sqft.data
    if form.pets_allowed.data:
        filters['pets_allowed'] = True
    if form.parking_available.data:
        filters['parking_available'] = True
    if form.washer_dryer.data:
        filters['washer_dryer'] = True
    if form.dishwasher.data:
        filters['dishwasher'] = True
    if form.air_conditioning.data:
        filters['air_conditioning'] = True

    # Execute search
    query = build_unit_query(company_id, filters)
    units_results = query.order_by('name').all()
    total_units = query.count()

    # Get total available units count
    all_units_count = Unit.query.filter_by(company_id=company_id).count()

    return render_template(
        'search/unit_search.html',
        form=form,
        units=units_results,
        total_results=total_units,
        total_units=all_units_count,
        filters=filters
    )


@search.route('/api/units')
@login_required
def units_api():
    """
    JSON API endpoint for unit search.

    Useful for AJAX requests and frontend applications.
    """
    company_id = current_user.get_company_id()

    # Build filters from query parameters
    filters = {}
    if request.args.get('query'):
        filters['query'] = request.args.get('query')
    if request.args.get('bedrooms'):
        filters['bedrooms'] = request.args.get('bedrooms')
    if request.args.get('bathrooms'):
        filters['bathrooms'] = request.args.get('bathrooms')
    if request.args.get('occupancy_status'):
        filters['occupancy_status'] = request.args.get('occupancy_status')
    if request.args.get('property_id'):
        filters['property_id'] = request.args.get('property_id')
    if request.args.get('min_rent'):
        filters['min_rent'] = float(request.args.get('min_rent'))
    if request.args.get('max_rent'):
        filters['max_rent'] = float(request.args.get('max_rent'))

    # Execute search
    query = build_unit_query(company_id, filters)
    units_results = query.limit(50).all()

    # Format results as JSON
    results = []
    for unit in units_results:
        results.append({
            'id': unit.uuid,
            'name': unit.name,
            'bedrooms': unit.bedrooms,
            'bathrooms': unit.bathrooms,
            'sqft': unit.sqft,
            'rent': float(unit.rent) if unit.rent else None,
            'occupancy_status': unit.occupancy_status,
            'property': {
                'id': unit.property_ref.uuid if unit.property_ref else None,
                'name': unit.property_ref.name if unit.property_ref else None
            }
        })

    return jsonify({
        'results': results,
        'count': len(results),
        'filters': filters
    })
