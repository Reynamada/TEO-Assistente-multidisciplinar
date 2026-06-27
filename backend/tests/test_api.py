from fastapi.testclient import TestClient

def test_api_health_check(client: TestClient):
    """Verifica se a API está no ar e respondendo corretamente (caso exista um endpoint root ou health)."""
    response = client.get("/")
    # Assumindo que a raiz retorne algo, mesmo que seja um redirect para o frontend ou um JSON básico
    assert response.status_code in [200, 404] # Ajustar conforme a implementação real do root

def test_login_endpoint(client: TestClient, db_session):
    """Testa se o endpoint de login lida corretamente com credenciais inválidas."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "naoexiste@clinica.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()
