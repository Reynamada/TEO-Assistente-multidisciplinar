import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

# Utiliza banco de dados em memória (SQLite) para testes rápidos e isolados
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    # Cria as tabelas do banco de teste
    Base.metadata.create_all(bind=engine)
    yield
    # Remove as tabelas no fim da sessão
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_database):
    """Fixture que fornece uma sessão de banco de dados por teste."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback() # Previne vazamento de estado
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Fixture que fornece um TestClient com injeção de dependência do DB de teste sobrescrita."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # A gerência da sessão já é feita pelo fixture db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
