"""
Search Utilities

Helper functions for building dynamic search queries with multiple filter criteria.
"""

from website.models import Unit, Property, Tenant, Lease
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta


def escape_like_wildcards(text):
    """
    Escape SQL LIKE wildcards (%, _) in user input to prevent wildcard injection attacks.

    Args:
        text (str): User input text to escape

    Returns:
        str: Escaped text safe for LIKE queries
    """
    if not text:
        return text
    # Escape backslash first to prevent double-escaping
    text = text.replace('\\', '\\\\')
    # Escape SQL LIKE wildcards
    text = text.replace('%', '\\%')
    text = text.replace('_', '\\_')
    # Escape bracket wildcards (for some SQL dialects)
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    return text


def build_unit_query(company_id, filters):
    """
    Build a dynamic Unit query based on provided filters.

    Args:
        company_id (int): Current user's company ID for multi-tenant isolation
        filters (dict): Dictionary of filter criteria

    Returns:
        SQLAlchemy Query: Filtered query object
    """
    query = Unit.query.filter_by(company_id=company_id)

    # Text search in unit name and description
    if filters.get('query'):
        # ✅ SECURITY FIX: Escape wildcards to prevent injection
        escaped_query = escape_like_wildcards(filters['query'])
        search_term = f"%{escaped_query}%"
        query = query.filter(
            or_(
                Unit.name.ilike(search_term, escape='\\'),
                Unit.description.ilike(search_term, escape='\\')
            )
        )

    # Bedroom filter
    if filters.get('bedrooms'):
        bedrooms = filters['bedrooms']
        if bedrooms == '4':  # 4+ bedrooms
            query = query.filter(Unit.bedrooms >= 4)
        else:
            query = query.filter(Unit.bedrooms == int(bedrooms))

    # Bathroom filter
    if filters.get('bathrooms'):
        bathrooms = float(filters['bathrooms'])
        if bathrooms == 3.0:  # 3+ bathrooms
            query = query.filter(Unit.bathrooms >= 3.0)
        else:
            query = query.filter(Unit.bathrooms == bathrooms)

    # Occupancy status filter
    if filters.get('occupancy_status'):
        query = query.filter(Unit.occupancy_status == filters['occupancy_status'])

    # Property filter
    if filters.get('property_id'):
        # Convert UUID to database ID
        property_obj = Property.find_by_uuid(filters['property_id'], company_id)
        if property_obj:
            query = query.filter(Unit.property_id == property_obj.id)

    # Rent range filter
    if filters.get('min_rent'):
        query = query.filter(Unit.rent >= filters['min_rent'])

    if filters.get('max_rent'):
        query = query.filter(Unit.rent <= filters['max_rent'])

    # Square footage filter
    if filters.get('min_sqft'):
        query = query.filter(Unit.sqft >= filters['min_sqft'])

    if filters.get('max_sqft'):
        query = query.filter(Unit.sqft <= filters['max_sqft'])

    # Amenity filters
    if filters.get('pets_allowed'):
        query = query.filter(Unit.pets_allowed == True)

    if filters.get('parking_available'):
        query = query.filter(Unit.parking_spaces > 0)

    if filters.get('washer_dryer'):
        query = query.filter(Unit.washer_dryer == True)

    if filters.get('dishwasher'):
        query = query.filter(Unit.dishwasher == True)

    if filters.get('air_conditioning'):
        query = query.filter(Unit.air_conditioning == True)

    return query


def build_property_query(company_id, filters):
    """
    Build a dynamic Property query based on provided filters.

    Args:
        company_id (int): Current user's company ID
        filters (dict): Dictionary of filter criteria

    Returns:
        SQLAlchemy Query: Filtered query object
    """
    query = Property.query.filter_by(company_id=company_id)

    # Text search
    if filters.get('query'):
        # ✅ SECURITY FIX: Escape wildcards to prevent injection
        escaped_query = escape_like_wildcards(filters['query'])
        search_term = f"%{escaped_query}%"
        query = query.filter(
            or_(
                Property.name.ilike(search_term, escape='\\'),
                Property.address.ilike(search_term, escape='\\'),
                Property.description.ilike(search_term, escape='\\')
            )
        )

    # Property type filter
    if filters.get('property_type'):
        query = query.filter(Property.type == filters['property_type'])

    # City filter
    if filters.get('city'):
        # ✅ SECURITY FIX: Escape wildcards to prevent injection
        escaped_city = escape_like_wildcards(filters['city'])
        query = query.filter(Property.city.ilike(f"%{escaped_city}%", escape='\\'))

    # State filter
    if filters.get('state'):
        query = query.filter(Property.state == filters['state'])

    # Occupancy status filter
    if filters.get('occupancy_status'):
        query = query.filter(Property.occupancy_status == filters['occupancy_status'])

    # Portfolio filter
    if filters.get('portfolio_id'):
        from website.models import Portfolio
        portfolio = Portfolio.find_by_uuid(filters['portfolio_id'], company_id)
        if portfolio:
            query = query.filter(Property.portfolio_id == portfolio.id)

    return query


def build_tenant_query(company_id, filters):
    """
    Build a dynamic Tenant query based on provided filters.

    Args:
        company_id (int): Current user's company ID
        filters (dict): Dictionary of filter criteria

    Returns:
        SQLAlchemy Query: Filtered query object
    """
    query = Tenant.query.filter_by(company_id=company_id)

    # Text search in name, email, phone
    if filters.get('query'):
        # ✅ SECURITY FIX: Escape wildcards to prevent injection
        escaped_query = escape_like_wildcards(filters['query'])
        search_term = f"%{escaped_query}%"
        query = query.filter(
            or_(
                Tenant.first_name.ilike(search_term, escape='\\'),
                Tenant.last_name.ilike(search_term, escape='\\'),
                Tenant.email.ilike(search_term, escape='\\'),
                Tenant.phone.ilike(search_term, escape='\\')
            )
        )

    # Lease status filter (requires checking leases)
    if filters.get('lease_status'):
        status = filters['lease_status']
        # This would require joining with Lease table and checking dates
        # For now, we'll skip this complex filter

    # Property filter (tenants in a specific property)
    if filters.get('property_id'):
        property_obj = Property.find_by_uuid(filters['property_id'], company_id)
        if property_obj:
            query = query.filter(Tenant.property_id == property_obj.id)

    return query


def build_lease_query(company_id, filters):
    """
    Build a dynamic Lease query based on provided filters.

    Args:
        company_id (int): Current user's company ID
        filters (dict): Dictionary of filter criteria

    Returns:
        SQLAlchemy Query: Filtered query object
    """
    query = Lease.query.filter_by(company_id=company_id)

    # Text search (in tenant name via relationship)
    if filters.get('query'):
        # ✅ SECURITY FIX: Escape wildcards to prevent injection
        escaped_query = escape_like_wildcards(filters['query'])
        search_term = f"%{escaped_query}%"
        query = query.join(Tenant).filter(
            or_(
                Tenant.first_name.ilike(search_term, escape='\\'),
                Tenant.last_name.ilike(search_term, escape='\\')
            )
        )

    # Lease status filter
    if filters.get('lease_status'):
        query = query.filter(Lease.lease_status == filters['lease_status'])

    # Property filter
    if filters.get('property_id'):
        property_obj = Property.find_by_uuid(filters['property_id'], company_id)
        if property_obj:
            query = query.filter(Lease.property_id == property_obj.id)

    # Date range filters
    if filters.get('start_date_from'):
        query = query.filter(Lease.start >= filters['start_date_from'])

    if filters.get('start_date_to'):
        query = query.filter(Lease.start <= filters['start_date_to'])

    if filters.get('end_date_from'):
        query = query.filter(Lease.end >= filters['end_date_from'])

    if filters.get('end_date_to'):
        query = query.filter(Lease.end <= filters['end_date_to'])

    # Expiring within X days filter
    if filters.get('expiring_within_days'):
        days = int(filters['expiring_within_days'])
        future_date = datetime.now() + timedelta(days=days)
        query = query.filter(
            and_(
                Lease.end >= datetime.now(),
                Lease.end <= future_date
            )
        )

    return query


def global_search(company_id, query_string, resource_type='all'):
    """
    Perform a global search across all resources.

    Args:
        company_id (int): Current user's company ID
        query_string (str): Search query
        resource_type (str): Resource type to search ('all', 'units', 'properties', 'tenants', 'leases')

    Returns:
        dict: Dictionary with results for each resource type
    """
    results = {
        'units': [],
        'properties': [],
        'tenants': [],
        'leases': []
    }

    # ✅ SECURITY FIX: Escape wildcards to prevent injection
    escaped_query = escape_like_wildcards(query_string)
    search_term = f"%{escaped_query}%"

    if resource_type in ['all', 'units']:
        # Search units by name or description
        results['units'] = Unit.query.filter_by(company_id=company_id).filter(
            or_(
                Unit.name.ilike(search_term, escape='\\'),
                Unit.description.ilike(search_term, escape='\\')
            )
        ).limit(10).all()

    if resource_type in ['all', 'properties']:
        # Search properties by name or address
        results['properties'] = Property.query.filter_by(company_id=company_id).filter(
            or_(
                Property.name.ilike(search_term, escape='\\'),
                Property.address.ilike(search_term, escape='\\'),
                Property.description.ilike(search_term, escape='\\')
            )
        ).limit(10).all()

    if resource_type in ['all', 'tenants']:
        # Search tenants by name or email
        results['tenants'] = Tenant.query.filter_by(company_id=company_id).filter(
            or_(
                Tenant.first_name.ilike(search_term, escape='\\'),
                Tenant.last_name.ilike(search_term, escape='\\'),
                Tenant.email.ilike(search_term, escape='\\')
            )
        ).limit(10).all()

    if resource_type in ['all', 'leases']:
        # Search leases by tenant name
        results['leases'] = Lease.query.filter_by(company_id=company_id).join(Tenant).filter(
            or_(
                Tenant.first_name.ilike(search_term, escape='\\'),
                Tenant.last_name.ilike(search_term, escape='\\')
            )
        ).limit(10).all()

    return results


def get_search_summary(results):
    """
    Generate a summary of search results.

    Args:
        results (dict): Dictionary of search results

    Returns:
        dict: Summary with counts for each resource type
    """
    return {
        'total': sum(len(v) if isinstance(v, list) else 0 for v in results.values()),
        'units_count': len(results.get('units', [])),
        'properties_count': len(results.get('properties', [])),
        'tenants_count': len(results.get('tenants', [])),
        'leases_count': len(results.get('leases', []))
    }
