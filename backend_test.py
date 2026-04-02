import requests
import sys
import json
import time
from datetime import datetime

class CivicAssistAPITester:
    def __init__(self, base_url="https://civic-assist-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            headers.pop('Content-Type', None)  # Remove for multipart

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f", Error: {error_detail}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_register_new_user(self):
        """Test user registration with new account"""
        timestamp = int(time.time())
        test_data = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@civicassist.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User Registration", "POST", "auth/register", 200, test_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_login_existing_user(self):
        """Test login with existing demo account"""
        login_data = {
            "email": "demo@civicassist.com",
            "password": "demo123"
        }
        
        success, response = self.run_test(
            "User Login (Demo Account)", "POST", "auth/login", 200, login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_update_profile(self):
        """Test profile update with location"""
        profile_data = {
            "name": "Updated Test User",
            "state": "Maharashtra",
            "city": "Mumbai",
            "pincode": "400001"
        }
        
        return self.run_test(
            "Update Profile", "PUT", "auth/profile", 200, profile_data
        )

    def test_get_states(self):
        """Test getting list of states"""
        return self.run_test("Get States", "GET", "locations/states", 200)

    def test_get_cities(self):
        """Test getting cities for a state"""
        return self.run_test("Get Cities", "GET", "locations/cities/Maharashtra", 200)

    def test_simplify_complaint(self):
        """Test AI complaint simplification"""
        complaint_data = {
            "text": "The street lights on MG Road have not been working for the past two weeks, causing safety issues at night. People are afraid to walk and there have been some incidents."
        }
        
        success, response = self.run_test(
            "AI Complaint Simplification", "POST", "complaint/simplify", 200, complaint_data
        )
        
        if success:
            if 'simplified' in response and 'category' in response:
                print(f"   Simplified: {response.get('simplified', '')[:100]}...")
                print(f"   Category: {response.get('category', '')}")
                return True
            else:
                self.log_test("AI Response Format", False, "Missing simplified or category fields")
        return False

    def test_portal_suggestion(self):
        """Test portal suggestion based on category and location"""
        portal_data = {
            "category": "Road Maintenance",
            "state": "Maharashtra",
            "city": "Mumbai"
        }
        
        success, response = self.run_test(
            "Portal Suggestion", "POST", "portal/suggest", 200, portal_data
        )
        
        if success and 'name' in response:
            print(f"   Portal: {response.get('name', '')}")
            return True
        return False

    def test_submit_complaint(self):
        """Test complaint submission"""
        complaint_data = {
            "original_input": "Street lights not working on MG Road",
            "simplified_input": "Non-functional street lighting on MG Road causing safety concerns",
            "category": "Road Maintenance",
            "confirmed": True
        }
        
        return self.run_test(
            "Submit Complaint", "POST", "complaint/submit", 200, complaint_data
        )

    def test_complaint_history(self):
        """Test getting complaint history"""
        return self.run_test("Get Complaint History", "GET", "complaint/history", 200)

    def test_contact_form(self):
        """Test contact form submission"""
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test contact message"
        }
        
        return self.run_test(
            "Contact Form Submission", "POST", "contact", 200, contact_data
        )

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        original_token = self.token
        self.token = None  # Remove token
        
        success, _ = self.run_test(
            "Unauthorized Access (Should Fail)", "GET", "auth/me", 401
        )
        
        self.token = original_token  # Restore token
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Civic Assist API Tests")
        print("=" * 50)
        
        # Basic API test
        self.test_root_endpoint()
        
        # Test registration flow
        if not self.test_register_new_user():
            print("⚠️  Registration failed, trying demo login...")
            if not self.test_login_existing_user():
                print("❌ Both registration and login failed. Stopping tests.")
                return False
        
        # Test authenticated endpoints
        self.test_get_current_user()
        self.test_update_profile()
        
        # Test location endpoints
        self.test_get_states()
        self.test_get_cities()
        
        # Test complaint flow
        print("\n🤖 Testing AI Integration...")
        self.test_simplify_complaint()
        self.test_portal_suggestion()
        self.test_submit_complaint()
        self.test_complaint_history()
        
        # Test other features
        self.test_contact_form()
        self.test_unauthorized_access()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            return False

def main():
    tester = CivicAssistAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())