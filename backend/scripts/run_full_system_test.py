"""
SmartCart AI — End-to-End API & Security Verification Runner
"""
import time
import uuid
import requests

BASE_URL = "http://localhost:8000"

results = []

def record(test_name, passed, detail=""):
    results.append({"name": test_name, "passed": passed, "detail": detail})
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{status}] {test_name}: {detail}")

print("=== Starting SmartCart AI Full System & Security Test Suite ===\n")

# 1. Health & Readiness
try:
    r = requests.get(f"{BASE_URL}/healthz", timeout=5)
    record("Health Check (/healthz)", r.status_code == 200 and r.json().get("status") == "ok", f"Status {r.status_code}")
except Exception as e:
    record("Health Check (/healthz)", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/readyz", timeout=5)
    record("Readiness Check (/readyz)", r.status_code == 200, f"Status {r.status_code}")
except Exception as e:
    record("Readiness Check (/readyz)", False, str(e))

# 2. Security Headers
try:
    r = requests.get(f"{BASE_URL}/healthz", timeout=5)
    h = r.headers
    has_nosniff = h.get("x-content-type-options") == "nosniff"
    has_frame_deny = h.get("x-frame-options") in ["DENY", "SAMEORIGIN"]
    has_csp = "default-src" in h.get("content-security-policy", "")
    passed = has_nosniff and has_frame_deny and has_csp
    record("Security Headers (nosniff, frame-options, CSP)", passed, f"nosniff={has_nosniff}, frame={has_frame_deny}, csp={has_csp}")
except Exception as e:
    record("Security Headers", False, str(e))

# 3. Unauthenticated Protection (RBAC / Auth Boundary)
try:
    r = requests.get(f"{BASE_URL}/cart", timeout=5)
    record("Cart Auth Protection (Unauthenticated 401)", r.status_code in [401, 403], f"Status {r.status_code}")
except Exception as e:
    record("Cart Auth Protection", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/orders", timeout=5)
    record("Orders Auth Protection (Unauthenticated 401)", r.status_code in [401, 403], f"Status {r.status_code}")
except Exception as e:
    record("Orders Auth Protection", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/inventory", timeout=5)
    record("Inventory Admin Protection (Unauthenticated 401)", r.status_code in [401, 403], f"Status {r.status_code}")
except Exception as e:
    record("Inventory Admin Protection", False, str(e))

# 4. User Registration & Authentication Flow
user_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
user_password = "SecurePassword123!"
user_token = None
user_id = None

try:
    reg_payload = {"email": user_email, "password": user_password, "username": f"user_{uuid.uuid4().hex[:6]}"}
    r = requests.post(f"{BASE_URL}/auth/register", json=reg_payload, timeout=5)
    if r.status_code == 201:
        data = r.json()
        user_id = data.get("id")
        record("User Registration (/auth/register)", True, f"Created {user_email}")
    else:
        record("User Registration (/auth/register)", False, f"Status {r.status_code}: {r.text}")
except Exception as e:
    record("User Registration", False, str(e))

try:
    login_payload = {"email": user_email, "password": user_password}
    r = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=5)
    if r.status_code == 200:
        data = r.json()
        user_token = data.get("access_token")
        record("User Login (/auth/login)", True, f"Got JWT token (length {len(user_token)})")
    else:
        record("User Login (/auth/login)", False, f"Status {r.status_code}: {r.text}")
except Exception as e:
    record("User Login", False, str(e))

user_headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}

# 5. Auth /me verification
if user_token:
    try:
        r = requests.get(f"{BASE_URL}/auth/me", headers=user_headers, timeout=5)
        record("Current User Profile (/auth/me)", r.status_code == 200 and r.json().get("email") == user_email, f"User {user_email}")
    except Exception as e:
        record("Current User Profile", False, str(e))

# 6. Normal User RBAC check on Admin Endpoints
if user_token:
    try:
        r = requests.get(f"{BASE_URL}/orders/admin", headers=user_headers, timeout=5)
        record("Normal User Blocked from Admin Orders", r.status_code in [401, 403], f"Status {r.status_code}")
    except Exception as e:
        record("Normal User Blocked from Admin Orders", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/inventory", headers=user_headers, timeout=5)
        record("Normal User Blocked from Admin Inventory", r.status_code in [401, 403], f"Status {r.status_code}")
    except Exception as e:
        record("Normal User Blocked from Admin Inventory", False, str(e))

# 7. Admin Login & RBAC Access
admin_token = None
try:
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@smartcart.ai", "password": "SmartCart@123"}, timeout=5)
    if r.status_code == 200:
        admin_token = r.json().get("access_token")
        record("Admin Login (/auth/login)", True, "Admin JWT obtained")
    else:
        record("Admin Login (/auth/login)", False, f"Status {r.status_code}: {r.text}")
except Exception as e:
    record("Admin Login", False, str(e))

admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

if admin_token:
    try:
        r = requests.get(f"{BASE_URL}/orders/admin", headers=admin_headers, timeout=5)
        record("Admin Access to /orders/admin", r.status_code == 200, f"Status {r.status_code}")
    except Exception as e:
        record("Admin Access to /orders/admin", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/inventory", headers=admin_headers, timeout=5)
        record("Admin Access to /inventory", r.status_code == 200, f"Status {r.status_code}")
    except Exception as e:
        record("Admin Access to /inventory", False, str(e))

# 8. Brute-Force Lockout Test
try:
    fake_email = f"brute_{uuid.uuid4().hex[:6]}@example.com"
    locked = False
    for i in range(7):
        r = requests.post(f"{BASE_URL}/auth/login", json={"email": fake_email, "password": "badpassword123"}, timeout=5)
        if r.status_code == 429:
            locked = True
            break
    record("Brute-Force Login Lockout (429)", locked, "Rate-limited / locked out after repeated attempts")
except Exception as e:
    record("Brute-Force Login Lockout", False, str(e))

# 9. Catalog & Injection Resistance
sample_product_id = None
try:
    r = requests.get(f"{BASE_URL}/products?limit=5", timeout=5)
    products = r.json()
    if r.status_code == 200 and isinstance(products, list) and len(products) > 0:
        sample_product_id = products[0]["id"]
        record("Product Catalog Listing (/products)", True, f"Retrieved {len(products)} products, sample ID={sample_product_id}")
    else:
        record("Product Catalog Listing (/products)", False, f"Status {r.status_code}")
except Exception as e:
    record("Product Catalog Listing", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/products/categories", timeout=5)
    cats = r.json()
    record("Product Categories (/products/categories)", r.status_code == 200 and isinstance(cats, list), f"{len(cats)} categories")
except Exception as e:
    record("Product Categories", False, str(e))

try:
    r = requests.get(f"{BASE_URL}/products/autocomplete?q=butter", timeout=5)
    suggestions = r.json()
    record("Product Autocomplete (/products/autocomplete)", r.status_code == 200 and isinstance(suggestions, list), f"Suggestions: {suggestions}")
except Exception as e:
    record("Product Autocomplete", False, str(e))

# SQL Injection Probe
try:
    sqli_probe = "butter' UNION SELECT 1, 'admin', 'pass', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1--"
    r = requests.get(f"{BASE_URL}/products?search={sqli_probe}", timeout=5)
    record("SQL Injection Parameter Probe", r.status_code == 200 and isinstance(r.json(), list), "Safely handled parameterized query without SQL error")
except Exception as e:
    record("SQL Injection Parameter Probe", False, str(e))

# 10. Commerce Flow: Cart, Coupon, Checkout, Payment, Invoice Slip
if user_token and sample_product_id:
    # Get Cart
    try:
        r = requests.get(f"{BASE_URL}/cart", headers=user_headers, timeout=5)
        record("Cart Retrieval (/cart)", r.status_code == 200, f"Cart items: {len(r.json().get('items', []))}")
    except Exception as e:
        record("Cart Retrieval", False, str(e))

    # Add to Cart
    cart_item_id = None
    try:
        r = requests.post(f"{BASE_URL}/cart/items", headers=user_headers, json={"product_id": sample_product_id, "quantity": 2}, timeout=5)
        if r.status_code in [200, 201]:
            items = r.json().get("items", [])
            for item in items:
                if item.get("product_id") == sample_product_id:
                    cart_item_id = item.get("id")
            record("Add Item to Cart (/cart/items)", True, f"Cart item ID: {cart_item_id}")
        else:
            record("Add Item to Cart (/cart/items)", False, f"Status {r.status_code}: {r.text}")
    except Exception as e:
        record("Add Item to Cart", False, str(e))

    # Coupon Validation
    try:
        r = requests.post(f"{BASE_URL}/coupons/validate", json={"code": "WELCOME50", "order_amount": 500.0}, headers=user_headers, timeout=5)
        record("Coupon Validation: WELCOME50", r.status_code == 200 and r.json().get("discount_amount") == 250.0, f"Discount: ₹{r.json().get('discount_amount')}")
    except Exception as e:
        record("Coupon Validation: WELCOME50", False, str(e))

    try:
        r = requests.post(f"{BASE_URL}/coupons/validate", json={"code": "INVALID_COUPON_CODE", "order_amount": 500.0}, headers=user_headers, timeout=5)
        record("Coupon Validation: Invalid Code Rejected", r.status_code in [400, 404], f"Rejected with HTTP {r.status_code}: {r.json().get('detail')}")
    except Exception as e:
        record("Coupon Validation: Invalid Code", False, str(e))

    # Checkout
    order_id = None
    try:
        r = requests.post(f"{BASE_URL}/orders/checkout", headers=user_headers, timeout=5)
        if r.status_code in [200, 201]:
            order_data = r.json().get("order", {})
            order_id = order_data.get("id")
            record("Checkout & Order Creation (/orders/checkout)", True, f"Order ID: {order_id}, Total: ₹{order_data.get('total_amount')}")
        else:
            record("Checkout & Order Creation (/orders/checkout)", False, f"Status {r.status_code}: {r.text}")
    except Exception as e:
        record("Checkout & Order Creation", False, str(e))

    # Payment Initiation & Verification
    if order_id:
        try:
            r = requests.post(f"{BASE_URL}/payments", headers=user_headers, json={"order_id": order_id, "payment_method": "upi"}, timeout=5)
            if r.status_code in [200, 201]:
                payment = r.json()
                tx_id = payment.get("transaction_id")
                record("Payment Initiation (/payments)", True, f"Transaction: {tx_id}")

                # Verify Payment
                r_v = requests.post(f"{BASE_URL}/payments/verify", headers=user_headers, json={"transaction_id": tx_id}, timeout=5)
                record("Payment Verification (/payments/verify)", r_v.status_code == 200 and r_v.json().get("status") == "paid", f"Status: {r_v.json().get('status')}")
            else:
                record("Payment Initiation (/payments)", False, f"Status {r.status_code}: {r.text}")
        except Exception as e:
            record("Payment Processing", False, str(e))

        # Invoice Slip PDF (Admin only endpoint)
        try:
            r = requests.get(f"{BASE_URL}/orders/{order_id}/slip", headers=admin_headers, timeout=5)
            record("Invoice Slip PDF Generation (/orders/{id}/slip)", r.status_code == 200 and r.headers.get("content-type") == "application/pdf", f"Size: {len(r.content)} bytes")
        except Exception as e:
            record("Invoice Slip PDF Generation", False, str(e))

# 11. Wishlist & Address Book
if user_token and sample_product_id:
    try:
        r = requests.post(f"{BASE_URL}/wishlist/{sample_product_id}", headers=user_headers, timeout=5)
        record("Add to Wishlist", r.status_code in [200, 201], f"Status {r.status_code}")
        r_list = requests.get(f"{BASE_URL}/wishlist", headers=user_headers, timeout=5)
        record("Get Wishlist", r_list.status_code == 200, f"Items: {len(r_list.json())}")
    except Exception as e:
        record("Wishlist", False, str(e))

    try:
        addr_payload = {
            "address_type": "home",
            "line1": "42 Outer Ring Road",
            "line2": "Apt 4B",
            "city": "Bengaluru",
            "state": "KA",
            "postal_code": "560100"
        }
        r = requests.post(f"{BASE_URL}/addresses", headers=user_headers, json=addr_payload, timeout=5)
        record("Create Address (/addresses)", r.status_code in [200, 201], f"Status {r.status_code}")
        r_get = requests.get(f"{BASE_URL}/addresses", headers=user_headers, timeout=5)
        record("List Addresses (/addresses)", r_get.status_code == 200, f"Total: {len(r_get.json())}")
    except Exception as e:
        record("Address Book", False, str(e))

# 12. AI Recipe Copilot
try:
    r = requests.post(f"{BASE_URL}/ai/recipe", json={"prompt": "healthy paneer dish"}, timeout=10)
    record("AI Recipe Copilot (/ai/recipe)", r.status_code == 200, f"Returned recipe: {r.json().get('title') if r.status_code == 200 else r.status_code}")
except Exception as e:
    record("AI Recipe Copilot", False, str(e))

# Summary
total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed

print(f"\n==========================================")
print(f"Test Summary: {passed}/{total} Passed ({failed} Failed)")
print(f"==========================================")
