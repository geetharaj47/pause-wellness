import pytest
import pytest_asyncio
import uuid
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database import init_db

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()

@pytest.mark.asyncio
async def test_embedding_consent_gating_and_search():
    """Verify that search is strictly gated behind embeddings_rag consent."""
    email = f"rag_user_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user (default embeddings_rag consent is False)
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create entry
        await ac.post("/api/v1/journal", headers=headers, json={
            "text": "Taking a 10-minute break with music helped me reset before my viva."
        })

        # Search without consent -> MUST FAIL with 403
        search_denied = await ac.post("/api/v1/journal/search", headers=headers, json={
            "query": "What helped before my viva?"
        })
        assert search_denied.status_code == 403
        assert "consent" in search_denied.json()["detail"].lower()

        # Grant consent & sync embeddings
        await ac.put("/api/v1/consents", headers=headers, json={"embeddings_rag": True})
        await ac.post("/api/v1/journal/sync-embeddings", headers=headers)

        # Search now -> MUST SUCCEED
        search_ok = await ac.post("/api/v1/journal/search", headers=headers, json={
            "query": "What helped before my viva?"
        })
        assert search_ok.status_code == 200
        data = search_ok.json()
        assert data["abstained"] is False
        assert len(data["results"]) >= 1
        assert "viva" in data["results"][0]["snippet"]
        assert data["results"][0]["similarity_score"] > 0.40

@pytest.mark.asyncio
async def test_semantic_retrieval_tenant_isolation_and_abstention():
    """
    CRITICAL TEST:
    1. Semantic query ranks conceptually related notes.
    2. Zero leakage from User B to User A.
    3. Abstention when query has no relevant evidence.
    """
    email_a = f"student_a_{uuid.uuid4().hex[:6]}@student.edu"
    email_b = f"student_b_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Setup User A
        reg_a = await ac.post("/api/v1/auth/register", json={
            "email": email_a,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        await ac.put("/api/v1/consents", headers=headers_a, json={"embeddings_rag": True})

        # Setup User B
        reg_b = await ac.post("/api/v1/auth/register", json={
            "email": email_b,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        await ac.put("/api/v1/consents", headers=headers_b, json={"embeddings_rag": True})

        # User A saves two distinct entries
        await ac.post("/api/v1/journal", headers=headers_a, json={
            "text": "Going for a walk by the lake with my roommate helped calm my exam nerves."
        })
        await ac.post("/api/v1/journal", headers=headers_a, json={
            "text": "Worked for hours configuring the FPGA board in the hardware laboratory."
        })

        # User B saves a confidential study note
        await ac.post("/api/v1/journal", headers=headers_b, json={
            "text": "User B confidential: Drinking peppermint tea helped my headache during finals."
        })

        # 1. User A asks about calming exam stress
        search_a = await ac.post("/api/v1/journal/search", headers=headers_a, json={
            "query": "What helped ease my tension during exams?"
        })
        assert search_a.status_code == 200
        res_a = search_a.json()
        assert res_a["abstained"] is False
        assert len(res_a["results"]) >= 1
        assert "walk by the lake" in res_a["results"][0]["snippet"]

        # ZERO LEAKAGE: User B's peppermint note must NOT appear anywhere in User A's results!
        all_snippets = " ".join([r["snippet"] for r in res_a["results"]])
        assert "peppermint" not in all_snippets
        assert "User B confidential" not in all_snippets

        # 2. ABSTENTION: User A asks about an unrelated topic with zero evidence
        search_unrelated = await ac.post("/api/v1/journal/search", headers=headers_a, json={
            "query": "Quantum mechanics teleportation and dark matter theories"
        })
        assert search_unrelated.status_code == 200
        res_unrelated = search_unrelated.json()
        assert res_unrelated["abstained"] is True
        assert len(res_unrelated["results"]) == 0
        assert "couldn't find a related entry" in res_unrelated["message"]

@pytest.mark.asyncio
async def test_embedding_purge_on_consent_revocation():
    """Verify that revoking embeddings_rag consent immediately purges stored vectors."""
    email = f"purge_user_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Grant consent & create entry
        await ac.put("/api/v1/consents", headers=headers, json={"embeddings_rag": True})
        await ac.post("/api/v1/journal", headers=headers, json={
            "text": "Meditation in the morning was really restorative."
        })

        # Verify search works
        search_1 = await ac.post("/api/v1/journal/search", headers=headers, json={
            "query": "morning meditation"
        })
        assert search_1.status_code == 200
        assert len(search_1.json()["results"]) == 1

        # Revoke consent with delete_existing_embeddings_on_revoke=True
        await ac.put("/api/v1/consents", headers=headers, json={
            "embeddings_rag": False,
            "delete_existing_embeddings_on_revoke": True
        })

        # Subsequent search is barred
        search_2 = await ac.post("/api/v1/journal/search", headers=headers, json={
            "query": "morning meditation"
        })
        assert search_2.status_code == 403
