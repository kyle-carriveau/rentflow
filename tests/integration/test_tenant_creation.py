#!/usr/bin/env python3
"""
Unit tests for tenant creation functionality
This will help diagnose the spinning form issue
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from website import create_app, db
from website.models import User, Tenant
from werkzeug.security import generate_password_hash
import tempfile
import requests
import json

class TenantCreationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with cls.app.app_context():
            db.create_all()
            
            # Create a test user
            test_user = User(
                email='test@example.com',
                password=generate_password_hash('testpass123'),
                first_name='Test',
                last_name='User'
            )
            db.session.add(test_user)
            db.session.commit()
            cls.test_user_id = test_user.id

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        """Set up for each test"""
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Log in the test user
        with self.client.session_transaction() as sess:
            sess['user_id'] = str(self.test_user_id)
            sess['_fresh'] = True

    def tearDown(self):
        """Clean up after each test"""
        self.app_context.pop()

    def test_tenant_create_page_loads(self):
        """Test that the tenant creation page loads properly"""
        response = self.client.get('/tenant/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Tenant', response.data)
        self.assertIn(b'form', response.data)

    def test_tenant_create_form_has_correct_action(self):
        """Test that the form has the correct action attribute"""
        response = self.client.get('/tenant/create')
        self.assertEqual(response.status_code, 200)
        # Check for the form action
        self.assertIn(b'action="/tenant/create"', response.data)

    def test_tenant_create_post_with_valid_data(self):
        """Test creating a tenant with valid data"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '5551234567',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'NY',
            'zip_code': '12345',
            'property': ''  # Optional field
        }
        
        response = self.client.post('/tenant/create', data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Check if tenant was created
        tenant = Tenant.query.filter_by(email='john.doe@example.com').first()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.first_name, 'John')
        self.assertEqual(tenant.last_name, 'Doe')

    def test_tenant_create_post_missing_required_fields(self):
        """Test creating a tenant with missing required fields"""
        form_data = {
            'first_name': '',  # Missing required field
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '5551234567'
        }
        
        response = self.client.post('/tenant/create', data=form_data)
        self.assertEqual(response.status_code, 200)  # Should return to form with error
        self.assertIn(b'First name is required', response.data)

    def test_tenant_create_with_invalid_email(self):
        """Test creating a tenant with invalid email"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',  # Invalid email
            'phone': '5551234567'
        }
        
        response = self.client.post('/tenant/create', data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'valid email', response.data)

    def test_tenant_create_with_invalid_zip(self):
        """Test creating a tenant with invalid zip code"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '5551234567',
            'zip_code': 'invalid'  # Invalid zip
        }
        
        response = self.client.post('/tenant/create', data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Zip code must contain only numbers', response.data)

    def test_tenant_create_phone_formatting(self):
        """Test that phone numbers are properly processed"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe2@example.com',
            'phone': '(555) 123-4567',  # Formatted phone
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'NY',
            'zip_code': '12345'
        }
        
        response = self.client.post('/tenant/create', data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Check if tenant was created and phone was processed correctly
        tenant = Tenant.query.filter_by(email='john.doe2@example.com').first()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.phone, 5551234567)  # Should be stored as integer

    def test_tenant_create_endpoint_exists(self):
        """Test that the tenant creation endpoint exists and is routed correctly"""
        with self.app.test_request_context():
            from flask import url_for
            create_url = url_for('tenant.create')
            self.assertEqual(create_url, '/tenant/create')

    def test_form_csrf_token_handling(self):
        """Test CSRF token in form (when enabled)"""
        # Temporarily enable CSRF
        self.app.config['WTF_CSRF_ENABLED'] = True
        
        response = self.client.get('/tenant/create')
        self.assertEqual(response.status_code, 200)
        # Should contain CSRF token or hidden field
        self.assertTrue(
            b'csrf_token' in response.data or 
            b'hidden' in response.data
        )
        
        # Reset CSRF setting
        self.app.config['WTF_CSRF_ENABLED'] = False

    def test_database_connection(self):
        """Test that database connection is working"""
        user_count = User.query.count()
        self.assertGreaterEqual(user_count, 1)  # At least our test user

    def test_tenant_view_functions_exist(self):
        """Test that all necessary view functions exist"""
        from website.tenant.views import tenant
        
        # Check that the blueprint exists
        self.assertIsNotNone(tenant)
        
        # Check that routes are registered
        rules = list(self.app.url_map.iter_rules())
        tenant_routes = [rule for rule in rules if rule.endpoint.startswith('tenant.')]
        
        # Should have at least create route
        create_routes = [rule for rule in tenant_routes if 'create' in rule.endpoint]
        self.assertGreater(len(create_routes), 0)

class LiveServerTest(unittest.TestCase):
    """Test against the actual running server"""
    
    def setUp(self):
        self.base_url = 'http://127.0.0.1:5000'
        # Test if server is running
        try:
            response = requests.get(self.base_url, timeout=2)
            self.server_running = True
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            self.server_running = False

    def test_server_is_running(self):
        """Test that the Flask server is running"""
        if not self.server_running:
            self.skipTest("Flask server is not running")
        
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)

    def test_tenant_create_page_accessible(self):
        """Test that tenant create page is accessible via HTTP"""
        if not self.server_running:
            self.skipTest("Flask server is not running")
        
        # This will fail without login, but should not hang
        response = requests.get(f'{self.base_url}/tenant/create', timeout=5)
        # Should redirect to login or show page
        self.assertIn(response.status_code, [200, 302])

    def test_post_to_tenant_create_responds(self):
        """Test that POST to tenant create endpoint responds (doesn't hang)"""
        if not self.server_running:
            self.skipTest("Flask server is not running")
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '5551234567'
        }
        
        try:
            # This should not hang, even if it fails validation
            response = requests.post(
                f'{self.base_url}/tenant/create', 
                data=form_data, 
                timeout=10,
                allow_redirects=False
            )
            # Should get some response, not hang
            self.assertIsNotNone(response.status_code)
        except requests.exceptions.Timeout:
            self.fail("POST request to /tenant/create timed out - server is hanging")

if __name__ == '__main__':
    print("Running Tenant Creation Tests...")
    print("=" * 50)
    
    # Run unit tests first
    print("\n1. Running Unit Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TenantCreationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ Unit tests passed!")
    else:
        print("❌ Unit tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        for failure in result.failures:
            print(f"\nFAILURE: {failure[0]}")
            print(failure[1])
            
        for error in result.errors:
            print(f"\nERROR: {error[0]}")
            print(error[1])
    
    # Run live server tests
    print("\n2. Running Live Server Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(LiveServerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ Live server tests passed!")
    else:
        print("❌ Live server tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    print("\nTest run complete!")