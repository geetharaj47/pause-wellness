import httpx
import uuid
import sys
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"

def run_tests():
    client = httpx.Client(timeout=30.0)

    print("--- 1. Application Loads ---")
    fe_resp = client.get(FRONTEND_URL)
    assert fe_resp.status_code == 200, f"Frontend failed with {fe_resp.status_code}"
    print("Frontend loaded: Status 200 OK at http://localhost:3000")

    be_resp = client.get(f"{BASE_URL}/health")
    assert be_resp.status_code == 200, f"Backend health failed with {be_resp.status_code}"
    health_data = be_resp.json()
    assert health_data.get("status") == "healthy", f"Health data: {health_data}"
    print(f"Backend loaded: {health_data} at http://127.0.0.1:8000/health")

    print("\n--- 2. Registration Works ---")
    test_id = str(uuid.uuid4())[:8]
    email = f"student_{test_id}@test-university.edu"
    password = f"SecurePass_{test_id}!2026"
    
    # Negative test: under 18 rejection
    underage_resp = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": f"minor_{test_id}@test.edu", "password": password, "confirmed_18_plus": False}
    )
    assert underage_resp.status_code == 400, f"Underage should fail 400, got {underage_resp.status_code}"
    print("Underage registration rejected (400) successfully.")

    # Valid registration
    reg_resp = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "confirmed_18_plus": True}
    )
    assert reg_resp.status_code == 201, f"Registration failed {reg_resp.status_code}: {reg_resp.text}"
    user_data = reg_resp.json()
    print(f"User registered: {user_data['email']} (ID: {user_data['user_id']})")

    print("\n--- 3. Login Works ---")
    login_resp = client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_resp.status_code == 200, f"Login failed {login_resp.status_code}: {login_resp.text}"
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert token, "No access token returned"
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful, JWT token obtained.")

    print("\n--- 4. Daily Check-in Works ---")
    today_str = date.today().isoformat()
    checkin_payload = {
        "local_date": today_str,
        "self_reported_mood": "Uneasy",
        "self_reported_energy": 2,
        "context_tags": ["study", "sleep"],
        "note": "A bit stressed about midterms, but taking things one step at a time."
    }
    ci_post = client.post(f"{BASE_URL}/api/v1/check-ins", json=checkin_payload, headers=headers)
    assert ci_post.status_code == 201, f"Check-in post failed {ci_post.status_code}: {ci_post.text}"
    ci_data = ci_post.json()
    print(f"Check-in saved: Date '{ci_data['local_date']}', Mood '{ci_data['self_reported_mood']}', Energy {ci_data['self_reported_energy']}/5")

    ci_get = client.get(f"{BASE_URL}/api/v1/check-ins", headers=headers)
    assert ci_get.status_code == 200
    assert len(ci_get.json()) >= 1
    print("Check-in history retrieved successfully.")

    print("\n--- 5. Daily Planning Works ---")
    plan_payload = {
        "focus": "Review Operating Systems Chapter 3 slides calmly",
        "steps": [
            {"id": "1", "text": "Open lecture slides for 10 minutes", "completed": False},
            {"id": "2", "text": "Draft notes on memory paging", "completed": False}
        ]
    }
    plan_put = client.put(f"{BASE_URL}/api/v1/daily-plan/today", json=plan_payload, headers=headers)
    assert plan_put.status_code == 200, f"Plan save failed {plan_put.status_code}: {plan_put.text}"
    plan_data = plan_put.json()
    print(f"Daily plan saved: Focus '{plan_data['focus']}' with {len(plan_data['steps'])} steps.")

    print("\n--- 6. Journal Entries Can Be Created and Retrieved ---")
    journal_text_1 = "Before my operating systems exam, doing box breathing helped steady my racing pulse."
    j_post = client.post(f"{BASE_URL}/api/v1/journal", json={"text": journal_text_1}, headers=headers)
    assert j_post.status_code == 201, f"Journal post failed {j_post.status_code}: {j_post.text}"
    j_entry = j_post.json()
    entry_id = j_entry["id"]
    print(f"Journal entry created (ID: {entry_id}).")

    # Second entry for retrieval
    journal_text_2 = "Went for a 15-minute evening walk around campus pond. Fresh air made it easier to focus afterward."
    client.post(f"{BASE_URL}/api/v1/journal", json={"text": journal_text_2}, headers=headers)

    j_list = client.get(f"{BASE_URL}/api/v1/journal", headers=headers)
    assert j_list.status_code == 200
    entries = j_list.json()
    assert len(entries) >= 2
    assert any("box breathing" in e["text"] for e in entries)
    print("Journal entries retrieved and decrypted successfully.")

    print("\n--- 7. Emotion Analysis Works ---")
    # Grant consent for emotion analysis first
    client.put(f"{BASE_URL}/api/v1/consents", json={"emotion_analysis": True}, headers=headers)
    
    ea_resp = client.post(f"{BASE_URL}/api/v1/journal/{entry_id}/analyze", headers=headers)
    assert ea_resp.status_code == 200, f"Emotion analysis failed {ea_resp.status_code}: {ea_resp.text}"
    ea_data = ea_resp.json()
    print(f"Emotion analysis generated: Labels: {ea_data.get('labels')}, Confidence: {ea_data.get('confidence_bands')}")

    # Test user correction
    corr_resp = client.patch(
        f"{BASE_URL}/api/v1/journal/{entry_id}/analysis",
        json={"user_correction": "calm/relieved"},
        headers=headers
    )
    assert corr_resp.status_code == 200
    print("Emotion analysis user correction saved.")

    print("\n--- 8. Semantic Retrieval Works ---")
    # Grant consent for embeddings_rag
    client.put(f"{BASE_URL}/api/v1/consents", json={"embeddings_rag": True}, headers=headers)

    # Sync embeddings for past entries
    sync_resp = client.post(f"{BASE_URL}/api/v1/journal/sync-embeddings", headers=headers)
    assert sync_resp.status_code == 200, f"Sync embeddings failed: {sync_resp.text}"
    print(f"Embeddings synced: {sync_resp.json()}")

    # Search for exam
    search_resp = client.post(
        f"{BASE_URL}/api/v1/journal/search",
        json={"query": "What helped for exam?", "top_k": 3},
        headers=headers
    )
    assert search_resp.status_code == 200, f"Search failed {search_resp.status_code}: {search_resp.text}"
    search_data = search_resp.json()
    results = search_data.get("results", [])
    assert len(results) > 0, f"Expected search results, got: {search_data}"
    print(f"Semantic search returned {len(results)} matches. Top match score: {results[0]['combined_score']}")

    print("\n--- 9. RAG Works ---")
    rag_resp = client.post(
        f"{BASE_URL}/api/v1/journal/ask",
        json={"query": "What helped when I felt exam anxiety?"},
        headers=headers
    )
    assert rag_resp.status_code == 200, f"RAG query failed {rag_resp.status_code}: {rag_resp.text}"
    rag_data = rag_resp.json()
    assert rag_data.get("answer"), f"No answer returned: {rag_data}"
    assert len(rag_data.get("sources", [])) > 0, f"No sources returned: {rag_data}"
    print(f"RAG Grounded Answer: {rag_data['answer']}")
    print(f"Citations: {len(rag_data['sources'])} cited entries.")

    print("\n--- 10. Crisis Detection Works ---")
    # Urgent crisis check
    crisis_resp = client.post(
        f"{BASE_URL}/api/v1/support-resources/check-safety",
        json={"text": "I can't go on anymore, I want to end my life."}
    )
    assert crisis_resp.status_code == 200, f"Crisis check failed {crisis_resp.status_code}"
    c_data = crisis_resp.json()
    assert c_data.get("detected_class") == "explicit_urgent_language", f"Expected explicit_urgent_language, got {c_data}"
    assert c_data.get("support_action") == "urgent_modal"
    print(f"Crisis detector correctly routed: detected_class='{c_data['detected_class']}', action='{c_data['support_action']}', contacts={len(c_data['helpline_contacts'])}")

    print("\n--- 11. Privacy and Consent Controls Work ---")
    # Consent list
    consent_resp = client.get(f"{BASE_URL}/api/v1/consents", headers=headers)
    assert consent_resp.status_code == 200
    print(f"Consent records verified: {len(consent_resp.json())} consent purposes.")

    # Data export
    export_resp = client.get(f"{BASE_URL}/api/v1/privacy/export", headers=headers)
    assert export_resp.status_code == 200
    export_json = export_resp.json()
    assert "journal_entries" in export_json
    print(f"Data export verified: Downloaded {len(export_json['journal_entries'])} entries.")

    # Account deletion
    del_resp = client.delete(f"{BASE_URL}/api/v1/account", headers=headers)
    assert del_resp.status_code == 200
    print("Permanent account deletion executed successfully.")

    # Verify user can no longer log in
    post_del_login = client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    assert post_del_login.status_code == 401
    print("Post-deletion authentication rejected (401) as expected.")

    print("\n=====================================================================")
    print("SUCCESS: ALL 11 APPLICATION CAPABILITIES FULLY TESTED AND VERIFIED!")
    print("=====================================================================")

if __name__ == "__main__":
    run_tests()
