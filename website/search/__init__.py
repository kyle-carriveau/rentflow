"""
Search Module

Provides application-wide search capabilities including:
- Advanced unit search with bedroom/bathroom/rent filtering
- Property search
- Tenant search
- Lease search
- Global search across all resources
"""

from flask import Blueprint

search = Blueprint('search', __name__, template_folder='templates')

from website.search import views
