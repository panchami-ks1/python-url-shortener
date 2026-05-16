import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    """Helper fixture to register a random user and return their auth headers."""
    unique_email = f"urltest_{uuid.uuid4()}@example.com"
    
    client.post("/auth/register", json={
        "email": unique_email,
        "password": "strongpassword"
    })
    
    response = client.post("/auth/login", data={
        "username": unique_email,
        "password": "strongpassword"
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_short_url(client, auth_headers):
    """Test generating a random short code for a valid URL."""
    response = client.post("/api/v1/urls", json={
        "original_url": "https://www.google.com"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    assert "short_code" in response.json()

def test_create_custom_alias(client, auth_headers):
    """Test providing a specific 6-character custom alias."""
    # Ensure custom alias is unique to avoid conflicts across test runs
    unique_alias = str(uuid.uuid4())[:6] 
    
    response = client.post("/api/v1/urls", json={
        "original_url": "https://www.google.com",
        "custom_alias": unique_alias
    }, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["short_code"] == unique_alias

def test_create_invalid_url(client, auth_headers):
    """Test that passing an invalid URL (like javascript injection) is rejected."""
    # Pydantic's HttpUrl validator automatically rejects this with a 422 error
    response = client.post("/api/v1/urls", json={
        "original_url": "javascript:alert(1)"
    }, headers=auth_headers)
    
    assert response.status_code == 422

def test_list_urls(client, auth_headers):
    """Test that a user can fetch a list of all URLs they own."""
    client.post("/api/v1/urls", json={"original_url": "https://www.test1.com"}, headers=auth_headers)
    client.post("/api/v1/urls", json={"original_url": "https://www.test2.com"}, headers=auth_headers)
    
    response = client.get("/api/v1/urls", headers=auth_headers)
    
    assert response.status_code == 200
    # The user just created 2 URLs, so their list should be exactly 2
    assert len(response.json()) == 2
