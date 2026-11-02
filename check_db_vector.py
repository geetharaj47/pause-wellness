import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sys.path.insert(0, "backend")
from app.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT current_database(), current_user, inet_server_port();"))
        db, user, port = res.fetchone()
        print(f"Connected to Database: {db}")
        print(f"User: {user}")
        print(f"Server Port: {port}")
        
        ext = await conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"))
        row = ext.fetchone()
        assert row is not None, "pgvector extension not found in pause_wellness"
        print(f"pgvector Extension: {row[0]} (version {row[1]})")
        
        vec_test = await conn.execute(text("SELECT ('[1,2,3]'::vector <=> '[1,2,3]'::vector) as zero_dist, ('[1,0,0]'::vector <=> '[0,1,0]'::vector) as ortho_dist;"))
        z, o = vec_test.fetchone()
        print(f"Vector cosine distance calculation: identical vectors = {z}, orthogonal vectors = {o}")
        assert z == 0.0, f"Expected 0.0, got {z}"
        assert abs(o - 1.0) < 1e-5, f"Expected 1.0, got {o}"
        
        tables = await conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"))
        tbl_count = tables.scalar()
        print(f"Public tables count: {tbl_count}")
        
        users = await conn.execute(text("SELECT count(*) FROM users;"))
        u_count = users.scalar()
        print(f"Existing user records preserved: {u_count}")
        print("DATABASE & PGVECTOR VERIFICATION PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(check())
