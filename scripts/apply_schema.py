"""
apply_schema.py — Aplica el schema SQL a Supabase via Management API.
Uso: python scripts/apply_schema.py
"""
import asyncio
import httpx
import sys
import os

# Supabase project ref extraído de la URL
PROJECT_REF = "dijikyzpdomrcffnhbed"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRpamlreXpwZG9tcmNmZm5oYmVkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTk1OTQ4MCwiZXhwIjoyMDg3NTM1NDgwfQ.z3R8AFuQmLHYjqBbycRV_pY6138CV90dpEC1PSxlh-s"

# Leer el SQL desde el archivo de schema
SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", 
    ".gemini", "antigravity", "brain",
    "a1ed65f5-56e3-45f8-9dfa-42da45a623c3", "db_schema.sql"
)
HOME = os.path.expanduser("~")
SCHEMA_PATH = os.path.join(
    HOME, ".gemini", "antigravity", "brain",
    "a1ed65f5-56e3-45f8-9dfa-42da45a623c3", "db_schema.sql"
)

async def apply_schema():
    print(f"📖 Leyendo schema desde {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    headers = {
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"query": sql}

    print(f"🚀 Enviando schema a Supabase Management API...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            print("✅ Schema aplicado exitosamente!")
            print(resp.json())
        else:
            print(f"❌ Error {resp.status_code}: {resp.text}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(apply_schema())
