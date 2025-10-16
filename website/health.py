"""
Health check endpoint for monitoring and load balancers.
"""
from flask import Blueprint, jsonify
from website import db
from sqlalchemy import text

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint that verifies:
    - Application is running
    - Database connection is working
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }

    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'unhealthy: {str(e)}'

    # Determine HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503

    return jsonify(health_status), status_code


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes/orchestration systems.
    Checks if the application is ready to accept traffic.
    """
    return jsonify({'status': 'ready'}), 200


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes/orchestration systems.
    Checks if the application is alive and not deadlocked.
    """
    return jsonify({'status': 'alive'}), 200
