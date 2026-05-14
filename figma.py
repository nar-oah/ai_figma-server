import httpx


def get_file(key: str, token: str) -> dict:
    client = httpx.Client(follow_redirects=True)
    headers = {"X-Figma-Token": token, "Accept": "application/json"}
    url = f"https://api.figma.com/v1/files/{key}?geometry=paths"
    return client.get(url, headers=headers, timeout=30.0).json()
