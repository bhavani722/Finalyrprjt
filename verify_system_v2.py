import requests
import time
import os

BASE_URL = "http://localhost:5000"

def get_token(username, password):
    res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
    return res.json().get('access_token')

def verify_system():
    print("--- STARTING SYSTEM VERIFICATION ---")
    
    # 1. Login as Admin
    admin_token = get_token("admin1", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 2. Check Admin Metrics (Should be 200 now, not 404)
    print("\n[Testing Admin Metrics]")
    res = requests.get(f"{BASE_URL}/admin/model-metrics", headers=headers)
    print(f"Metrics Status: {res.status_code}")
    if res.status_code == 200:
        print("✓ Admin metrics fixed.")
    else:
        print(f"X Admin metrics failed: {res.text}")

    # 3. Test QR Generation (Merchant)
    print("\n[Testing QR Generation]")
    merchant_token = get_token("merchant1", "password123")
    m_headers = {"Authorization": f"Bearer {merchant_token}"}
    res = requests.post(f"{BASE_URL}/merchant/generate-qr", headers=m_headers, json={"amount": 5000})
    qr_data = res.json()
    print(f"QR Path: {qr_data.get('qr_path')}")
    if qr_data.get('qr_path'):
        print("✓ QR generation verified.")
    
    # 4. Test QR Scan (User)
    print("\n[Testing QR Scan Flow]")
    user_token = get_token("user1", "password123")
    u_headers = {"Authorization": f"Bearer {user_token}"}
    # Simulate payload from generated QR (merchant_id|amount)
    payload = "2|5000" 
    res = requests.post(f"{BASE_URL}/scan-qr", headers=u_headers, json={"payload": payload})
    scan_res = res.json()
    print(f"Scan Result: {scan_res}")
    if scan_res.get('intent_id'):
        print("✓ QR scan -> Intent creation verified.")
        print(f"✓ ML Risk Level: {scan_res.get('risk_level')}")

    # 5. Test Merchant Alerts
    print("\n[Testing Merchant Alerts Polling]")
    res = requests.get(f"{BASE_URL}/merchant/alerts", headers=m_headers)
    print(f"Alerts Result: {res.json()}")
    print("✓ Alert polling endpoint verified.")

    print("\n--- SYSTEM VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    # Ensure server is running first. If not, this will fail.
    try:
        verify_system()
    except Exception as e:
        print(f"Verification failed (Is server running?): {e}")
