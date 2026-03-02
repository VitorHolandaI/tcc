"""
Tests for the main application entry point and health check.
"""


def test_health_check(client_professor):
    """Test the root endpoint returns a healthy status"""
    response = client_professor.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "API rodando" in data["message"]


def test_openapi_schema(client_professor):
    """Test that OpenAPI schema is accessible"""
    response = client_professor.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Escola API - Test Maker System"


def test_docs_accessible(client_professor):
    """Test that Swagger docs page is accessible"""
    response = client_professor.get("/docs")
    assert response.status_code == 200
