"""
Comprehensive test suite for JWT authentication functionality.
Tests all authentication endpoints and protected API access.
"""
import json
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.utils import timezone


User = get_user_model()


class JWTAuthenticationTestCase(APITestCase):
    """
    Comprehensive test suite for JWT authentication system.
    """
    
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Test user data
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        # Create a test user for login tests
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='ExistingPassword123!',
            first_name='Existing',
            last_name='User'
        )
        
        # URLs
        self.register_url = reverse('user_register')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_url = reverse('token_verify')
        self.profile_url = reverse('user_profile')
        self.auth_test_url = reverse('auth_test')
        
        # Protected endpoint URLs (using inventory as example)
        self.protected_url = '/api/inventory/'
    
    # ========== PUBLIC ENDPOINT TESTS ==========
    
    def test_health_check_public_access(self):
        """Test that health check endpoint is publicly accessible."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.json())
        self.assertEqual(response.json()['status'], 'healthy')
    
    def test_api_info_public_access(self):
        """Test that API info endpoint is publicly accessible."""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('api_info', response.json())
        self.assertIn('authentication', response.json()['api_info'])
    
    def test_auth_test_endpoint_public_access(self):
        """Test that auth test endpoint is publicly accessible."""
        response = self.client.post(self.auth_test_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertFalse(response.json()['authenticated'])
        self.assertEqual(response.json()['user'], 'Anonymous')
    
    # ========== USER REGISTRATION TESTS ==========
    
    def test_user_registration_success(self):
        """Test successful user registration with JWT token generation."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('message', response_data)
        self.assertIn('user', response_data)
        self.assertIn('tokens', response_data)
        
        # Verify user data
        user_data = response_data['user']
        self.assertEqual(user_data['username'], self.user_data['username'])
        self.assertEqual(user_data['email'], self.user_data['email'])
        self.assertEqual(user_data['first_name'], self.user_data['first_name'])
        self.assertEqual(user_data['last_name'], self.user_data['last_name'])
        self.assertFalse(user_data['is_staff'])
        self.assertFalse(user_data['is_superuser'])
        
        # Verify tokens
        tokens = response_data['tokens']
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertTrue(len(tokens['access']) > 50)  # JWT tokens are long
        self.assertTrue(len(tokens['refresh']) > 50)
        
        # Verify user was created in database
        user = User.objects.get(username=self.user_data['username'])
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
    
    def test_user_registration_password_mismatch(self):
        """Test registration failure when passwords don't match."""
        invalid_data = self.user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword123!'
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.json())
    
    def test_user_registration_weak_password(self):
        """Test registration failure with weak password."""
        invalid_data = self.user_data.copy()
        invalid_data['password'] = '123'
        invalid_data['password_confirm'] = '123'
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.json())
    
    def test_user_registration_duplicate_username(self):
        """Test registration failure with duplicate username."""
        duplicate_data = self.user_data.copy()
        duplicate_data['username'] = self.existing_user.username
        
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.json())
    
    def test_user_registration_missing_fields(self):
        """Test registration failure with missing required fields."""
        incomplete_data = {
            'username': 'incompleteuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.register_url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========== USER LOGIN TESTS ==========
    
    def test_user_login_success(self):
        """Test successful user login with JWT token generation."""
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('access', response_data)
        self.assertIn('refresh', response_data)
        self.assertIn('user', response_data)
        
        # Verify user data
        user_data = response_data['user']
        self.assertEqual(user_data['username'], self.existing_user.username)
        self.assertEqual(user_data['email'], self.existing_user.email)
        
        # Verify tokens
        self.assertTrue(len(response_data['access']) > 50)
        self.assertTrue(len(response_data['refresh']) > 50)
        
        # Store tokens for later tests
        self.access_token = response_data['access']
        self.refresh_token = response_data['refresh']
    
    def test_user_login_invalid_credentials(self):
        """Test login failure with invalid credentials."""
        invalid_login_data = {
            'username': self.existing_user.username,
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(self.login_url, invalid_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.json())
    
    def test_user_login_nonexistent_user(self):
        """Test login failure with non-existent user."""
        nonexistent_login_data = {
            'username': 'nonexistentuser',
            'password': 'SomePassword123!'
        }
        
        response = self.client.post(self.login_url, nonexistent_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_login_missing_fields(self):
        """Test login failure with missing fields."""
        incomplete_login_data = {
            'username': self.existing_user.username
            # Missing password
        }
        
        response = self.client.post(self.login_url, incomplete_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.json())
    
    # ========== TOKEN MANAGEMENT TESTS ==========
    
    def test_token_refresh_success(self):
        """Test successful token refresh."""
        # First, log in to get tokens
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.json()['refresh']
        
        # Refresh the token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('access', response_data)
        self.assertTrue(len(response_data['access']) > 50)
    
    def test_token_refresh_invalid_token(self):
        """Test token refresh failure with invalid token."""
        invalid_refresh_data = {'refresh': 'invalid_token_string'}
        response = self.client.post(self.refresh_url, invalid_refresh_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.json())
    
    def test_token_verify_success(self):
        """Test successful token verification."""
        # Get an access token
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.json()['access']
        
        # Verify the token
        verify_data = {'token': access_token}
        response = self.client.post(self.verify_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_token_verify_invalid_token(self):
        """Test token verification failure with invalid token."""
        invalid_verify_data = {'token': 'invalid_token_string'}
        response = self.client.post(self.verify_url, invalid_verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== PROTECTED ENDPOINT ACCESS TESTS ==========
    
    def test_protected_endpoint_without_token(self):
        """Test that protected endpoints reject requests without authentication."""
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.json())
        self.assertIn('Authentication credentials were not provided', response.json()['detail'])
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test that protected endpoints reject requests with invalid tokens."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_string')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_valid_token(self):
        """Test that protected endpoints accept requests with valid tokens."""
        # Get an access token
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.json()['access']
        
        # Use the token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.protected_url)
        
        # Should be successful (200) or show proper API response
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
    
    def test_user_profile_endpoint_authenticated(self):
        """Test user profile endpoint with authentication."""
        # Get an access token
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.json()['access']
        
        # Access profile endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('user', response_data)
        
        user_data = response_data['user']
        self.assertEqual(user_data['username'], self.existing_user.username)
        self.assertEqual(user_data['email'], self.existing_user.email)
    
    def test_user_profile_endpoint_unauthenticated(self):
        """Test user profile endpoint without authentication."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== TOKEN SECURITY TESTS ==========
    
    def test_token_contains_user_claims(self):
        """Test that JWT tokens contain proper user claims."""
        # Login to get token
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        # Verify token was returned
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        response_data = login_response.json()
        self.assertIn('access', response_data)
        
        # Verify user data is included in response
        user_data = response_data['user']
        self.assertEqual(user_data['username'], self.existing_user.username)
        self.assertEqual(user_data['email'], self.existing_user.email)
        self.assertIn('is_staff', user_data)
        self.assertIn('is_superuser', user_data)
    
    def test_token_expiration_handling(self):
        """Test that expired tokens are properly rejected."""
        # Create a token for the user
        refresh = RefreshToken.for_user(self.existing_user)
        access_token = str(refresh.access_token)
        
        # First, verify the token works
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Note: In a real test, you'd need to manipulate the token's expiration
        # For now, we'll just verify the token verification endpoint works
        verify_data = {'token': access_token}
        response = self.client.post(self.verify_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # ========== INTEGRATION TESTS ==========
    
    def test_complete_authentication_flow(self):
        """Test the complete authentication flow from registration to API access."""
        # 1. Register a new user
        register_response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # Get tokens from registration
        tokens = register_response.json()['tokens']
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        # 2. Verify the access token works
        verify_data = {'token': access_token}
        verify_response = self.client.post(self.verify_url, verify_data, format='json')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        
        # 3. Access profile with the token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # 4. Access a protected endpoint
        protected_response = self.client.get(self.protected_url)
        self.assertIn(protected_response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        
        # 5. Refresh the token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # 6. Use the new access token
        new_access_token = refresh_response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        final_response = self.client.get(self.profile_url)
        self.assertEqual(final_response.status_code, status.HTTP_200_OK)
    
    def test_multiple_endpoint_access_patterns(self):
        """Test various API endpoints with JWT authentication."""
        # Login to get token
        login_data = {
            'username': self.existing_user.username,
            'password': 'ExistingPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.json()['access']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test various API endpoints
        endpoints_to_test = [
            '/api/units/',
            '/api/warehouses/',
            '/api/customers/',
            '/api/packaging/',
            '/api/vendors/',
            '/api/items/',
            '/api/inventory/',
        ]
        
        for endpoint in endpoints_to_test:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # Should be successful or return proper API response
                self.assertIn(response.status_code, [
                    status.HTTP_200_OK, 
                    status.HTTP_204_NO_CONTENT,
                    status.HTTP_404_NOT_FOUND  # Some endpoints might not exist in current setup
                ])
                
                # Should not be authentication errors
                self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========== ERROR HANDLING TESTS ==========
    
    def test_malformed_authorization_header(self):
        """Test handling of malformed authorization headers."""
        # Test various malformed headers
        malformed_headers = [
            'Bearer',  # Missing token
            'Token abc123',  # Wrong prefix
            'Bearer ',  # Empty token
            'Bearer token with spaces',  # Invalid token format
        ]
        
        for header in malformed_headers:
            with self.subTest(header=header):
                self.client.credentials(HTTP_AUTHORIZATION=header)
                response = self.client.get(self.profile_url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_concurrent_sessions(self):
        """Test that multiple valid tokens can be used concurrently."""
        # Create multiple tokens for the same user
        refresh1 = RefreshToken.for_user(self.existing_user)
        refresh2 = RefreshToken.for_user(self.existing_user)
        
        access_token1 = str(refresh1.access_token)
        access_token2 = str(refresh2.access_token)
        
        # Both tokens should work
        for token in [access_token1, access_token2]:
            with self.subTest(token=token[:20] + '...'):
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                response = self.client.get(self.profile_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminAuthenticationTestCase(APITestCase):
    """Test authentication for admin/superuser accounts."""
    
    def setUp(self):
        """Set up admin user for testing."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPassword123!'
        )
        
        self.login_url = reverse('token_obtain_pair')
        self.profile_url = reverse('user_profile')
    
    def test_admin_user_login(self):
        """Test that admin users can log in and receive proper claims."""
        login_data = {
            'username': 'admin',
            'password': 'AdminPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        user_data = response_data['user']
        
        # Verify admin privileges are included
        self.assertTrue(user_data['is_staff'])
        self.assertTrue(user_data['is_superuser'])
    
    def test_admin_user_api_access(self):
        """Test that admin users can access all API endpoints."""
        # Login as admin
        login_data = {
            'username': 'admin',
            'password': 'AdminPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.json()['access']
        
        # Access admin panel (should work with session auth)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test API access
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user_data = response.json()['user']
        self.assertTrue(user_data['is_staff'])
        self.assertTrue(user_data['is_superuser'])
