import uuid

def test_redirect_to_original_url(client):
    """Test that visiting a short code successfully redirects to the original URL."""
    # 1. Register and login
    email = f"redir_{uuid.uuid4()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "pass"})
    login_res = client.post("/auth/login", data={"username": email, "password": "pass"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    
    # 2. Create a short URL
    create_res = client.post("/api/v1/urls", json={"original_url": "https://www.example.com"}, headers=headers)
    short_code = create_res.json()["short_code"]
    
    # 3. Request the short code (we tell the test client NOT to auto-follow the redirect)
    # We expect a 307 Temporary Redirect HTTP status code.
    response = client.get(f"/{short_code}", follow_redirects=False)
    
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.example.com/"
    
    # 4. Request it again to ensure the Redis cache-hit logic doesn't crash
    response_cache = client.get(f"/{short_code}", follow_redirects=False)
    assert response_cache.status_code == 307

def test_redirect_not_found(client):
    """Test that visiting a fake short code returns a 404 error."""
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404
