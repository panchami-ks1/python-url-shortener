import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.cache.redis_client import get_redis
from app.db.base import Base
from app.db.session import get_db, engine as prod_engine
from app.main import app

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=prod_engine)

@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=prod_engine)
    yield

@pytest.fixture
def db_session(setup_database):
    """
    Creates a new database session for a test.
    Automatically rolls back any changes made during the test so it doesn't affect the dev DB.
    """
    connection = prod_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    # Nested transaction for sub-transactions (like commit() inside services)
    nested = connection.begin_nested()
    
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def redis_client():
    client = fakeredis.FakeRedis()
    yield client
    client.flushall()

@pytest.fixture
def client(db_session, redis_client):
    def override_get_db():
        yield db_session

    def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
