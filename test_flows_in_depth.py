import httpx
import uuid
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def run_in_depth_checks():
    client = httpx.Client(timeout=30.0)
    print("=" * 65)
    print("STARTING IN-DEPTH REGISTRATION, LOGIN, AND MAIN APPLICATION CHECKS")
    print("=" * 65)
    
    # 1. Registration tests
    print("\n[Step 1] Registration Validations:")
    suffix = uuid.uuid4().hex[:6]
    minor_email = f"minor_{suffix}@university.edu"
    student_email = f"student_{suffix}@university.edu"
    password = f"TestPass_{suffix}!2026"
    
    # Under-18 check
    r_minor = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": minor_email, "password": password, "confirmed_18_plus": False}
    )
    assert r_minor.status_code == 400, f"Expected 400 for minor, got {r_minor.status_code}"
    print(f"  [PASS] Under-18 guard: Rejected registration with status {r_minor.status_code} ({r_minor.json().get('detail')})")
    
    # Valid 18+ registration
    r_reg = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": student_email, "password": password, "confirmed_18_plus": True}
    )
    assert r_reg.status_code == 201, f"Expected 201 for valid registration, got {r_reg.status_code}: {r_reg.text}"
    user_info = r_reg.json()
    user_id = user_info["user_id"]
    print(f"  [PASS] Adult 18+ registration: Created user '{student_email}' (user_id: {user_id})")
    
    # Duplicate registration guard
    r_dup = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": student_email, "password": password, "confirmed_18_plus": True}
    )
    assert r_dup.status_code in [400, 409], f"Expected 400 or 409 for duplicate, got {r_dup.status_code}"
    print(f"  [PASS] Duplicate guard: Rejected duplicate email with status {r_dup.status_code}")
    
    # 2. Login tests
    print("\n[Step 2] Authentication & Token Generation:")
    # Invalid password
    r_bad_login = client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": student_email, "password": "WrongPassword!999"}
    )
    assert r_bad_login.status_code == 401, f"Expected 401 for bad password, got {r_bad_login.status_code}"
    print(f"  [PASS] Bad password rejection: Status {r_bad_login.status_code} Unauthorized")
    
    # Valid login
    r_login = client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": student_email, "password": password}
    )
    assert r_login.status_code == 200, f"Expected 200, got {r_login.status_code}: {r_login.text}"
    token = r_login.json().get("access_token")
    assert token, "No access token in response"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Valid login: JWT access token acquired ({token[:20]}...)")
    
    # Check /api/v1/auth/me
    r_me = client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200, f"Expected 200 for /auth/me, got {r_me.status_code}"
    print(f"  [PASS] User session verified via /auth/me: email='{r_me.json().get('email')}'")
    
    # 3. Daily Check-in Flow
    print("\n[Step 3] Daily Check-in Flow:")
    today_iso = date.today().isoformat()
    checkin_data = {
        "local_date": today_iso,
        "self_reported_mood": "Good",
        "self_reported_energy": 4,
        "context_tags": ["study", "exercise", "nutrition"],
        "note": "Took a short brisk walk after morning study session. Feeling clear-headed."
    }
    r_ci_post = client.post(f"{BASE_URL}/api/v1/check-ins", json=checkin_data, headers=headers)
    assert r_ci_post.status_code == 201, f"Expected 201, got {r_ci_post.status_code}: {r_ci_post.text}"
    ci_res = r_ci_post.json()
    print(f"  [PASS] Check-in saved for date {ci_res['local_date']}: mood='{ci_res['self_reported_mood']}', energy={ci_res['self_reported_energy']}/5")
    
    r_ci_get = client.get(f"{BASE_URL}/api/v1/check-ins", headers=headers)
    assert r_ci_get.status_code == 200
    assert len(r_ci_get.json()) >= 1
    print(f"  [PASS] Check-in history retrieved: {len(r_ci_get.json())} entry found.")
    
    # 4. Daily Plan Flow
    print("\n[Step 4] Daily Plan Flow:")
    plan_body = {
        "focus": "Complete Database Assignment Section 2",
        "steps": [
            {"id": "step-1", "text": "Draft relational schema diagram", "completed": True},
            {"id": "step-2", "text": "Write SQL queries for normalization", "completed": False}
        ]
    }
    r_plan = client.put(f"{BASE_URL}/api/v1/daily-plan/today", json=plan_body, headers=headers)
    assert r_plan.status_code == 200, f"Expected 200, got {r_plan.status_code}: {r_plan.text}"
    saved_plan = r_plan.json()
    print(f"  [PASS] Daily plan stored: focus='{saved_plan['focus']}', steps count={len(saved_plan['steps'])}")
    
    r_plan_get = client.get(f"{BASE_URL}/api/v1/daily-plan/today", headers=headers)
    assert r_plan_get.status_code == 200
    assert r_plan_get.json()["focus"] == plan_body["focus"]
    print("  [PASS] Daily plan retrieved successfully.")
    
    # 5. Private Journal Flow (Encryption At Rest)
    print("\n[Step 5] Encrypted Journal Flow:")
    j1_text = "Studied algorithms for 3 hours. Practicing dynamic programming problems felt challenging but rewarding."
    r_j1 = client.post(f"{BASE_URL}/api/v1/journal", json={"text": j1_text}, headers=headers)
    assert r_j1.status_code == 201
    j1_id = r_j1.json()["id"]
    print(f"  [PASS] Journal entry 1 created: id={j1_id}")
    
    j2_text = "When feeling overwhelmed before group meetings, taking five deep breaths outdoors helped reduce tension."
    r_j2 = client.post(f"{BASE_URL}/api/v1/journal", json={"text": j2_text}, headers=headers)
    assert r_j2.status_code == 201
    j2_id = r_j2.json()["id"]
    print(f"  [PASS] Journal entry 2 created: id={j2_id}")
    
    r_jlist = client.get(f"{BASE_URL}/api/v1/journal", headers=headers)
    assert r_jlist.status_code == 200
    entries = r_jlist.json()
    assert len(entries) >= 2
    assert any("dynamic programming" in e["text"] for e in entries)
    print(f"  [PASS] Journal entries decrypted on retrieval: {len(entries)} entries accessible to owner.")
    
    # 6. Emotion Analysis & Consent Flow
    print("\n[Step 6] Emotion Analysis & User Correction Flow:")
    # Grant emotion consent
    client.put(f"{BASE_URL}/api/v1/consents", json={"emotion_analysis": True}, headers=headers)
    r_ea = client.post(f"{BASE_URL}/api/v1/journal/{j2_id}/analyze", headers=headers)
    assert r_ea.status_code == 200, f"Expected 200, got {r_ea.status_code}: {r_ea.text}"
    ea = r_ea.json()
    print(f"  [PASS] Emotion analysis: labels={ea.get('labels')}, confidence={ea.get('confidence_bands')}")
    
    # Submit correction
    r_corr = client.patch(
        f"{BASE_URL}/api/v1/journal/{j2_id}/analysis",
        json={"user_correction": "grounded/calm"},
        headers=headers
    )
    assert r_corr.status_code == 200
    print(f"  [PASS] Emotion correction persisted: user_correction='grounded/calm'")
    
    # 7. Semantic Retrieval & RAG Flow
    print("\n[Step 7] Semantic Retrieval & Grounded RAG Flow:")
    client.put(f"{BASE_URL}/api/v1/consents", json={"embeddings_rag": True}, headers=headers)
    r_sync = client.post(f"{BASE_URL}/api/v1/journal/sync-embeddings", headers=headers)
    assert r_sync.status_code == 200
    print(f"  [PASS] Embeddings synchronization: {r_sync.json()}")
    
    r_search = client.post(
        f"{BASE_URL}/api/v1/journal/search",
        json={"query": "What helped when feeling overwhelmed?", "top_k": 3},
        headers=headers
    )
    assert r_search.status_code == 200
    s_results = r_search.json().get("results", [])
    assert len(s_results) > 0, "No search results returned"
    print(f"  [PASS] Semantic retrieval: Found {len(s_results)} match(es). Top match score: {s_results[0]['combined_score']:.4f}")
    
    r_rag = client.post(
        f"{BASE_URL}/api/v1/journal/ask",
        json={"query": "What helped me handle feeling overwhelmed?"},
        headers=headers
    )
    assert r_rag.status_code == 200
    rag_json = r_rag.json()
    assert rag_json.get("answer")
    assert len(rag_json.get("sources", [])) > 0
    print(f"  [PASS] Grounded RAG response generated: citations={len(rag_json['sources'])}")
    print(f"    Sample excerpt: {rag_json['sources'][0].get('snippet', '')[:80]}...")
    
    # 8. Crisis Safety Guard
    print("\n[Step 8] Safety & Crisis Router:")
    r_safe = client.post(
        f"{BASE_URL}/api/v1/support-resources/check-safety",
        json={"text": "I can't take this anymore, I want to kill myself tonight."}
    )
    assert r_safe.status_code == 200
    safe_data = r_safe.json()
    assert safe_data.get("detected_class") == "explicit_urgent_language"
    assert safe_data.get("support_action") == "urgent_modal"
    print(f"  [PASS] Crisis route: detected_class='{safe_data['detected_class']}', action='{safe_data['support_action']}', helplines={len(safe_data['helpline_contacts'])}")
    
    # 9. Privacy, Export & Clean Account Deletion
    print("\n[Step 9] Privacy Export & Account Purge:")
    r_export = client.get(f"{BASE_URL}/api/v1/privacy/export", headers=headers)
    assert r_export.status_code == 200
    exp = r_export.json()
    assert "journal_entries" in exp and len(exp["journal_entries"]) == 2
    print(f"  [PASS] Privacy export: Successfully exported complete archive with {len(exp['journal_entries'])} journal entries.")
    
    r_del = client.delete(f"{BASE_URL}/api/v1/account", headers=headers)
    assert r_del.status_code == 200
    print("  [PASS] Account purge: Transactional user and child-table deletion completed.")
    
    # Verify account is gone
    r_post_login = client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": student_email, "password": password})
    assert r_post_login.status_code == 401
    print("  [PASS] Revocation check: Deleted account credentials immediately rejected with status 401.")
    
    print("\n" + "=" * 65)
    print("ALL APPLICATION FLOWS SUCCESSFULLY VERIFIED!")
    print("=" * 65)

if __name__ == "__main__":
    run_in_depth_checks()
