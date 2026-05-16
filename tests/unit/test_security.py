from jose import jwt

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token


def test_password_hashing():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert password != hashed
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    user_id = "123-abc"
    token = create_access_token(user_id)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
