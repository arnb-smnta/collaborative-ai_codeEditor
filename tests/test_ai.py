import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from main import app
from routes.ai import detect_language
from models import CodeFile

client = TestClient(app)


# Mock user authentication
def mock_get_current_user():
    return {"id": 1, "username": "test_user"}


# Mock database session
@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


# Mock OpenAI API Response
mock_ai_response = MagicMock()
mock_ai_response.choices = [MagicMock()]
mock_ai_response.choices[0].message.content = "Mock Debugging Report"

# Test Data
TEST_CODE_PYTHON = "def hello():\n    print('Hello World')"
TEST_CODE_JS = "function hello() {\n    console.log('Hello World');\n}"
TEST_CODE_UNKNOWN = "<html><body>Hello</body></html>"


@pytest.mark.parametrize(
    "code, expected_language",
    [
        (TEST_CODE_PYTHON, "Python"),
        (TEST_CODE_JS, "JavaScript"),
        (TEST_CODE_UNKNOWN, "Unknown"),
    ],
)
def test_detect_language(code, expected_language):
    """Test language detection logic"""
    assert detect_language(code) == expected_language


@pytest.mark.asyncio
@patch(
    "app.routers.debugger.client.chat.completions.create", return_value=mock_ai_response
)
@patch("app.routers.debugger.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_python(mock_get_user, mock_openai, mock_db_session):
    """Test debugging API for Python code"""

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=1, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert "Mock Debugging Report" in response.json()["suggestions"]


@pytest.mark.asyncio
@patch(
    "app.routers.debugger.client.chat.completions.create", return_value=mock_ai_response
)
@patch("app.routers.debugger.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_javascript(mock_get_user, mock_openai, mock_db_session):
    """Test debugging API for JavaScript code"""

    mock_db_session.query().filter().first.return_value = CodeFile(
        id=2, content=TEST_CODE_JS
    )

    response = client.post("/ai/debug/2", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert "Mock Debugging Report" in response.json()["suggestions"]


@pytest.mark.asyncio
@patch("app.routers.debugger.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_file_not_found(mock_get_user, mock_db_session):
    """Test error handling when file is not found"""

    mock_db_session.query().filter().first.return_value = None  # No file found

    response = client.post(
        "/ai/debug/99", headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "File not found"


@pytest.mark.asyncio
@patch("app.routers.debugger.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_empty_file(mock_get_user, mock_db_session):
    """Test handling of an empty code file"""

    mock_db_session.query().filter().first.return_value = CodeFile(id=3, content="")

    response = client.post("/ai/debug/3", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Code file is empty"


@pytest.mark.asyncio
@patch(
    "app.routers.debugger.client.chat.completions.create",
    side_effect=Exception("OpenAI API error"),
)
@patch("app.routers.debugger.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_openai_error(mock_get_user, mock_openai, mock_db_session):
    """Test handling of OpenAI API errors"""

    mock_db_session.query().filter().first.return_value = CodeFile(
        id=4, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/4", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error while debugging" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limit():
    """Test if rate limiting works (returns HTTP 429 on excessive requests)"""

    for _ in range(10):  # Exceeding the rate limit intentionally
        client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many requests" in response.json()["error"]
