#!/usr/bin/env python3
"""
Simple DEAPI Rate Limit Test

Tests DEAPI API key validity and rate limiting without full dependencies.
"""

import os
import time
import requests
from datetime import datetime


def test_deapi_limits():
    """Test DEAPI rate limits and account status."""
    print("🔍 DEAPI Rate Limit Diagnostic")
    print("=" * 50)

    # Load API key
    api_key = os.getenv("DEAPI_API_KEY", "")
    if not api_key:
        print("❌ DEAPI_API_KEY environment variable not set!")
        return

    print(f"API Key loaded: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")

    base_url = "https://api.deapi.ai"
    endpoint = f"{base_url}/api/v1/client/vid2txt"

    # Test with a very short YouTube video
    test_video = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Very short test video

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "video_url": test_video,
        "include_ts": False,
        "model": "WhisperLargeV3",
    }

    print("\n📊 Testing API Key Validity...")
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"Response Status: {response.status_code}")

        if response.status_code == 401:
            print("❌ INVALID API KEY (401 Unauthorized)")
            print("💡 Check your API key in DEAPI dashboard")
            return
        elif response.status_code == 402:
            print("❌ INSUFFICIENT CREDITS (402 Payment Required)")
            print("💡 Add credits to your DEAPI account")
            return
        elif response.status_code == 429:
            print("⚠️  RATE LIMITED (429 Too Many Requests)")
            print("💡 You're hitting rate limits - likely Basic account")
        elif response.status_code == 200:
            print("✅ API Key Valid")
            # Cancel the request to avoid wasting credits
            try:
                request_id = response.json().get("data", {}).get("request_id")
                if request_id:
                    cancel_url = f"{base_url}/api/v1/client/request-status/{request_id}"
                    requests.delete(cancel_url, headers=headers, timeout=5)
                    print("✅ Test request cancelled (no credits used)")
            except:
                pass
        else:
            print(f"❓ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out - check internet connection")
        return
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check DEAPI service status")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return

    print("\n⏱️  Testing Rate Limits...")
    print("Making 3 rapid requests to test rate limiting...")

    results = []
    for i in range(3):
        print(f"  Request {i+1}/3...")
        try:
            start_time = time.time()
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            elapsed = time.time() - start_time

            status = response.status_code
            results.append(status)

            if status == 429:
                print(f"    ❌ Request {i+1}: RATE LIMITED (429)")
            elif status == 200:
                print(".2f")
                # Cancel request
                try:
                    request_id = response.json().get("data", {}).get("request_id")
                    if request_id:
                        cancel_url = f"{base_url}/api/v1/client/request-status/{request_id}"
                        requests.delete(cancel_url, headers=headers, timeout=5)
                except:
                    pass
            else:
                print(f"    ❓ Request {i+1}: Status {status}")

            # Small delay between requests
            if i < 2:
                time.sleep(0.5)

        except Exception as e:
            print(f"    ❌ Request {i+1}: Error - {str(e)}")
            results.append("error")

    # Analyze results
    rate_limited_count = sum(1 for r in results if r == 429)
    success_count = sum(1 for r in results if r == 200)
    error_count = len(results) - rate_limited_count - success_count

    print("\n📋 RATE LIMIT ANALYSIS")
    print(f"Successful requests: {success_count}/3")
    print(f"Rate limited requests: {rate_limited_count}/3")
    print(f"Error requests: {error_count}/3")

    if rate_limited_count > 0:
        print("\n🚨 DIAGNOSIS: You are being RATE LIMITED!")
        print("\n📖 DEAPI Rate Limits (from docs):")
        print("• Basic Account: 1 RPM, 10 RPD for transcription")
        print("• Premium Account: 300 RPM, unlimited daily")
        print("\n💡 SOLUTION:")
        print("1. Check your DEAPI account type in dashboard")
        print("2. If Basic: Upgrade by adding ANY amount of credits")
        print("3. Your $20 credits should qualify you for Premium (300 RPM)")
        print("4. If already Premium: Contact DEAPI support")
    else:
        print("\n✅ No rate limiting detected in test")
        print("💡 Issue might be video-specific or account status")

    print("\n🔍 ACCOUNT STATUS CHECK")
    print("Checking your DEAPI account balance...")

    try:
        balance_response = requests.get(
            f"{base_url}/api/v1/client/balance",
            headers=headers,
            timeout=10
        )

        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            balance = balance_data.get("data", {}).get("balance", "Unknown")
            print(f"💰 Account Balance: ${balance}")

            if isinstance(balance, (int, float)) and balance > 0:
                print("✅ Credits available")
            elif balance == 0:
                print("❌ Zero balance - add credits to continue")
            else:
                print("❓ Could not determine balance")
        else:
            print(f"❌ Could not check balance (Status: {balance_response.status_code})")

    except Exception as e:
        print(f"❌ Balance check failed: {str(e)}")

    # Final recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 30)

    if rate_limited_count > 0:
        print("1. 🚨 PRIORITY: Upgrade to Premium account")
        print("   → Go to DEAPI dashboard → Billing → Add any amount")
        print("   → Even $1 should unlock Premium limits")

        print("2. 🔧 Immediate fix: Increase delays in bulk processing")
        print("   → Change 5-second delay to 60+ seconds between requests")

    print("3. 🐛 Test with single video first")
    print("   → Verify the fix works before processing full batch")

    print("4. 📊 Monitor progress")
    print("   → Check manifest.json for status updates")

    print("\n📅 Rate Limit Reset:")
    print("• RPM limits reset every minute")
    print("• RPD limits reset at midnight UTC daily")

if __name__ == "__main__":
    test_deapi_limits()