import httpx

from app.config import settings

community_id = "ff2c0b8e-f964-4d6a-972f-ca6d06027e0b"

response = httpx.patch(
    f"{settings.supabase_url}/rest/v1/communities",
    params={"community_id": f"eq.{community_id}"},
    headers={
        "apikey": settings.supabase_secret_key,
        "Authorization": f"Bearer {settings.supabase_secret_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    },
    json={"description": "raw http test"},
)

print(response.status_code)
print(response.text)