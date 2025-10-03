"""
Lease Template Blueprint

Handles lease template management including CRUD operations,
template selection, and contract generation.
"""
from flask import Blueprint

lease_template = Blueprint('lease_template', __name__, template_folder='templates', url_prefix='/lease-templates')

from . import views
