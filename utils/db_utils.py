import asyncpg
import asyncio

DATABASE_URL = "postgresql://postgres:WsfXwDYSYnHIPWeGCfwJKSBCgEqALqqQ@postgres-jv4l.railway.internal:5432/railway"

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_tables()

    async def init_tables(self):
        async with self.pool.acquire() as conn:
            # Kino, Kanallar, Users
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS movies(
                    code TEXT PRIMARY KEY,
                    file_id TEXT,
                    name TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS channels(
                    channel TEXT PRIMARY KEY
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users(
                    user_id BIGINT PRIMARY KEY,
                    username TEXT
                )
            """)

    async def add_movie(self, code, file_id, name):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO movies(code, file_id, name) VALUES($1,$2,$3) ON CONFLICT(code) DO UPDATE SET file_id=$2, name=$3",
                code, file_id, name
            )

    async def del_movie(self, code):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM movies WHERE code=$1", code)

    async def get_movie(self, code):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT file_id,name FROM movies WHERE code=$1", code)

    async def add_channel(self, channel):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO channels(channel) VALUES($1) ON CONFLICT DO NOTHING", channel)

    async def del_channel(self, channel):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM channels WHERE channel=$1", channel)

    async def get_all_channels(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT channel FROM channels")
            return [r['channel'] for r in rows]

    async def add_user(self, user_id, username):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users(user_id, username) VALUES($1,$2) ON CONFLICT DO NOTHING",
                user_id, username
            )

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT user_id, username FROM users")
