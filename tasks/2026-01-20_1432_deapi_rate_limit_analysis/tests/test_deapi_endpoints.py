#!/usr/bin/env python3
"""
Comprehensive DEAPI Endpoint Testing Script

Tests all relevant DEAPI endpoints to verify:
1. Balance checking functionality
2. Error response formats
3. Rate limiting behavior
4. Request status polling
5. Price calculation endpoints

Usage:
    python test_deapi_endpoints.py --api-key YOUR_API_KEY

Requirements:
    pip install requests python-dotenv
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DEAPITester:
    """Comprehensive DEAPI endpoint tester."""

    def __init__(self, api_key: str, base_url: str = "https://api.deapi.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def test_balance_endpoint(self) -> Dict[str, Any]:
        """Test the balance checking endpoint."""
        print("[TEST] Testing balance endpoint...")

        try:
            response = self.session.get(f"{self.base_url}/api/v1/client/balance")
            result = {
                "endpoint": "/api/v1/client/balance",
                "method": "GET",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result["balance_data"] = data
                    print(f"[OK] Balance check successful: {data}")
                except json.JSONDecodeError:
                    result["error"] = "Invalid JSON response"
                    result["raw_response"] = response.text[:500]
                    print(f"[ERROR] Invalid JSON in balance response: {response.text[:200]}")
            else:
                result["error"] = f"HTTP {response.status_code}"
                result["response_text"] = response.text[:500]
                print(f"[ERROR] Balance check failed: {response.status_code} - {response.text[:200]}")

        except requests.RequestException as e:
            result = {
                "endpoint": "/api/v1/client/balance",
                "method": "GET",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"[ERROR] Balance check network error: {e}")

        return result

    def test_invalid_request_status(self) -> Dict[str, Any]:
        """Test request status endpoint with invalid ID."""
        print("[TEST] Testing invalid request status...")

        fake_request_id = "invalid-request-id-12345"

        try:
            response = self.session.get(f"{self.base_url}/api/v1/client/request-status/{fake_request_id}")
            result = {
                "endpoint": f"/api/v1/client/request-status/{fake_request_id}",
                "method": "GET",
                "status_code": response.status_code,
                "success": True,  # We expect this to fail gracefully
                "timestamp": datetime.now().isoformat()
            }

            if response.status_code == 404:
                print("[OK] Invalid request ID handled correctly (404)")
                result["expected_behavior"] = True
            elif response.status_code == 200:
                # Unexpected success - might indicate different error handling
                try:
                    data = response.json()
                    result["response_data"] = data
                    print(f"[WARN] Unexpected success for invalid ID: {data}")
                except:
                    result["raw_response"] = response.text[:500]
                    print(f"[WARN] Unexpected success with non-JSON response: {response.text[:200]}")
            else:
                result["error"] = f"Unexpected status: {response.status_code}"
                result["response_text"] = response.text[:500]
                print(f"[WARN] Unexpected status for invalid ID: {response.status_code}")

        except requests.RequestException as e:
            result = {
                "endpoint": f"/api/v1/client/request-status/{fake_request_id}",
                "method": "GET",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"[ERROR] Invalid request status network error: {e}")

        return result

    def test_price_calculation_video(self) -> Dict[str, Any]:
        """Test price calculation for video transcription."""
        print("[TEST] Testing video transcription price calculation...")

        # Use a real but short YouTube video for testing
        test_payload = {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Short test video
            "language": "en"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/client/vid2txt/price-calculation",
                json=test_payload
            )

            result = {
                "endpoint": "/api/v1/client/vid2txt/price-calculation",
                "method": "POST",
                "payload": test_payload,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result["price_data"] = data
                    result["success"] = True
                    print(f"[OK] Price calculation successful: {data}")
                except json.JSONDecodeError:
                    result["error"] = "Invalid JSON response"
                    result["raw_response"] = response.text[:500]
                    print(f"[ERROR] Invalid JSON in price response: {response.text[:200]}")
            else:
                result["success"] = False
                result["error"] = f"HTTP {response.status_code}"
                result["response_text"] = response.text[:500]
                print(f"[ERROR] Price calculation failed: {response.status_code} - {response.text[:200]}")

        except requests.RequestException as e:
            result = {
                "endpoint": "/api/v1/client/vid2txt/price-calculation",
                "method": "POST",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"[ERROR] Price calculation network error: {e}")

        return result

    def test_rate_limit_simulation(self) -> Dict[str, Any]:
        """Test rapid requests to potentially trigger rate limiting."""
        print("[TEST] Testing rate limit behavior with rapid requests...")

        results = []
        test_payload = {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "language": "en"
        }

        # Make several rapid requests
        for i in range(5):
            print(f"  Request {i+1}/5...")
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/v1/client/vid2txt",
                    json=test_payload,
                    timeout=10
                )
                end_time = time.time()

                result = {
                    "request_number": i + 1,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "timestamp": datetime.now().isoformat()
                }

                if response.status_code == 429:
                    print(f"[OK] Rate limit detected on request {i+1}")
                    result["rate_limited"] = True
                    result["headers"] = dict(response.headers)
                    # Check for rate limit headers
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        result["retry_after"] = retry_after
                        print(f"   Retry-After header: {retry_after}")
                elif response.status_code == 200:
                    result["rate_limited"] = False
                    try:
                        data = response.json()
                        result["request_id"] = data.get("data", {}).get("request_id")
                    except:
                        pass
                else:
                    result["rate_limited"] = False
                    result["error"] = f"HTTP {response.status_code}"
                    result["response_text"] = response.text[:200]

                results.append(result)

                # Small delay between requests
                if i < 4:  # Don't delay after last request
                    time.sleep(0.5)

            except requests.RequestException as e:
                results.append({
                    "request_number": i + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"[ERROR] Request {i+1} network error: {e}")

        return {
            "endpoint": "/api/v1/client/vid2txt",
            "method": "POST",
            "test_type": "rate_limit_simulation",
            "total_requests": len(results),
            "rate_limited_count": sum(1 for r in results if r.get("rate_limited")),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    def test_invalid_auth(self) -> Dict[str, Any]:
        """Test with invalid API key to check auth error handling."""
        print("[TEST] Testing invalid authentication...")

        # Create a session with invalid key
        invalid_session = requests.Session()
        invalid_session.headers.update({
            "Authorization": "Bearer invalid-api-key-12345",
            "Content-Type": "application/json"
        })

        try:
            response = invalid_session.get(f"{self.base_url}/api/v1/client/balance")

            result = {
                "endpoint": "/api/v1/client/balance",
                "method": "GET",
                "test_type": "invalid_auth",
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }

            if response.status_code == 401:
                print("[OK] Authentication error handled correctly (401)")
                result["success"] = True
                result["expected_behavior"] = True
            else:
                result["success"] = False
                result["error"] = f"Unexpected status: {response.status_code}"
                result["response_text"] = response.text[:500]
                print(f"[WARN] Unexpected auth response: {response.status_code}")

        except requests.RequestException as e:
            result = {
                "endpoint": "/api/v1/client/balance",
                "method": "GET",
                "test_type": "invalid_auth",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"[ERROR] Invalid auth network error: {e}")

        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests."""
        print("[START] Starting comprehensive DEAPI endpoint testing...\n")

        test_results = {
            "test_run_timestamp": datetime.now().isoformat(),
            "api_key_provided": bool(self.api_key),
            "base_url": self.base_url,
            "tests": {}
        }

        # Run tests in order of least to most impactful
        test_results["tests"]["balance_check"] = self.test_balance_endpoint()
        time.sleep(1)

        test_results["tests"]["invalid_request_status"] = self.test_invalid_request_status()
        time.sleep(1)

        test_results["tests"]["price_calculation"] = self.test_price_calculation_video()
        time.sleep(1)

        test_results["tests"]["invalid_auth"] = self.test_invalid_auth()
        time.sleep(1)

        test_results["tests"]["rate_limit_simulation"] = self.test_rate_limit_simulation()

        # Summarize results
        successful_tests = sum(1 for test in test_results["tests"].values()
                             if test.get("success", False))

        print(f"\n[SUMMARY] Test Summary:")
        print(f"   Total tests: {len(test_results['tests'])}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {len(test_results['tests']) - successful_tests}")

        test_results["summary"] = {
            "total_tests": len(test_results["tests"]),
            "successful": successful_tests,
            "failed": len(test_results["tests"]) - successful_tests
        }

        return test_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DEAPI Endpoint Testing")
    parser.add_argument("--api-key", help="DEAPI API key (or set DEAPI_API_KEY env var)")
    parser.add_argument("--output", default="deapi_test_results.json",
                       help="Output file for test results")
    parser.add_argument("--base-url", default="https://api.deapi.ai",
                       help="DEAPI base URL")

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.getenv("DEAPI_API_KEY")
    if not api_key:
        print("[ERROR] Error: No API key provided. Use --api-key or set DEAPI_API_KEY environment variable.")
        sys.exit(1)

    # Mask API key in output for security
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"

    print(f"[KEY] Using API key: {masked_key}")
    print(f"[URL] Base URL: {args.base_url}")
    print()

    # Run tests
    tester = DEAPITester(api_key, args.base_url)
    results = tester.run_all_tests()

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[SAVE] Results saved to: {args.output}")

    # Print key findings
    print("\n[ANALYSIS] Key Findings:")
    balance_test = results["tests"].get("balance_check", {})
    if balance_test.get("success"):
        balance_data = balance_test.get("balance_data", {})
        print(f"   [CREDITS] Current balance: {balance_data}")
    else:
        print(f"   [ERROR] Balance check failed: {balance_test.get('error', 'Unknown error')}")

    rate_limit_test = results["tests"].get("rate_limit_simulation", {})
    rate_limited = rate_limit_test.get("rate_limited_count", 0)
    if rate_limited > 0:
        print(f"   [WARN] Rate limiting detected: {rate_limited} requests limited")
    else:
        print("   [OK] No rate limiting detected in test run")

    invalid_auth_test = results["tests"].get("invalid_auth", {})
    if invalid_auth_test.get("success"):
        print("   [OK] Authentication error handling works correctly")
    else:
        print("   [WARN] Authentication error handling may need review")


if __name__ == "__main__":
    main()