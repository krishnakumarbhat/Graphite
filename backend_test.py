import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class BackendAPITester:
    def __init__(self, base_url: str = "https://workflow-sync-20.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple[bool, Dict[Any, Any]]:
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    response_data = {"raw_content": response.text[:200]}
                    print(f"   Response (raw): {response.text[:200]}")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                    response_data = error_data
                except:
                    response_data = {"error": response.text[:200]}
                    print(f"   Error (raw): {response.text[:200]}")

            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": response_data
            })

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Network Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "success": False,
                "error": str(e)
            })
            return False, {"error": str(e)}
        except Exception as e:
            print(f"❌ FAILED - Unexpected Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "success": False,
                "error": str(e)
            })
            return False, {"error": str(e)}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "/api/",
            200
        )

    def test_create_status_check(self):
        """Test creating a status check"""
        test_data = {
            "client_name": f"test_client_{datetime.now().strftime('%H%M%S')}"
        }
        return self.run_test(
            "Create Status Check",
            "POST",
            "/api/status",
            200,
            data=test_data
        )

    def test_get_status_checks(self):
        """Test getting all status checks"""
        return self.run_test(
            "Get Status Checks",
            "GET",
            "/api/status",
            200
        )

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚀 Starting Backend API Tests")
        print("=" * 60)
        
        # Test root endpoint
        success1, _ = self.test_root_endpoint()
        
        # Test status check creation
        success2, _ = self.test_create_status_check()
        
        # Test status check retrieval
        success3, _ = self.test_get_status_checks()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Backend Test Summary")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test.get('error', 'Status code mismatch')}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = BackendAPITester()
    all_passed = tester.run_all_tests()
    
    if all_passed:
        print("\n🎉 All backend tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some backend tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())