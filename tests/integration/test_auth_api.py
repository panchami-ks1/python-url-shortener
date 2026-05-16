import uuid

def test_register_user(client):
    """Test that a new user can successfully register with a unique email."""
    # Generate a unique email so the test passes even if run multiple times
    unique_email = f"user_{uuid.uuid4()}@example.com"
    
    response = client.post("/auth/register", json={
        "email": unique_email,
        "password": "strongpassword"
    })
    
    assert response.status_code == 200
    assert response.json()["email"] == unique_email

def test_register_duplicate_user(client):
    """Test that registering an existing email returns a 400 Bad Request."""
    unique_email = f"duplicate_{uuid.uuid4()}@example.com"
    
    # Register the first time
    client.post("/auth/register", json={
        "email": unique_email,
        "password": "strongpassword"
    })
    
    # Try to register the exact same email again
    response = client.post("/auth/register", json={
        "email": unique_email,
        "password": "strongpassword"
    })
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_user(client):
    """Test that a user can login and receive a valid JWT token."""
    unique_email = f"login_{uuid.uuid4()}@example.com"
    
    # Register a user first
    client.post("/auth/register", json={
        "email": unique_email,
        "password": "strongpassword"
    })
    
    # Login with the registered credentials
    response = client.post("/auth/login", data={
        "username": unique_email,
        "password": "strongpassword"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
