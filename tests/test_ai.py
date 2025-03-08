import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from httpx import Response
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


# Mock responses for OpenAI and Gemini
mock_openai_response = "OpenAI Debugging Report"
mock_gemini_response = "Gemini Debugging Report"

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


# Mock for OpenAI availability check
@pytest.fixture
def mock_openai_available():
    """Mock for OpenAI rate limit check returning True (available)"""
    return AsyncMock(return_value=True)


@pytest.fixture
def mock_openai_unavailable():
    """Mock for OpenAI rate limit check returning False (unavailable)"""
    return AsyncMock(return_value=False)


# Mock for OpenAI response
@pytest.fixture
def mock_openai_success():
    """Mock for successful OpenAI response"""
    return AsyncMock(return_value=(mock_openai_response, None))


@pytest.fixture
def mock_openai_failure():
    """Mock for failed OpenAI response"""
    return AsyncMock(return_value=(None, "OpenAI API error"))


# Mock for Gemini response
@pytest.fixture
def mock_gemini_success():
    """Mock for successful Gemini response"""
    return AsyncMock(return_value=(mock_gemini_response, None))


@pytest.fixture
def mock_gemini_failure():
    """Mock for failed Gemini response"""
    return AsyncMock(return_value=(None, "Gemini API error"))


@pytest.mark.asyncio
@patch("routes.ai.check_openai_limit")
@patch("routes.ai.get_openai_response")
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_with_openai(
    mock_get_user,
    mock_openai_response,
    mock_check_openai,
    mock_db_session,
    mock_openai_available,
    mock_openai_success,
):
    """Test debugging API using OpenAI when it's available"""
    mock_check_openai.return_value = mock_openai_available.return_value
    mock_openai_response.return_value = mock_openai_success.return_value

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=1, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert mock_openai_response.return_value == response.json()["suggestions"]
    assert "OpenAI" == response.json()["ai_provider"]


@pytest.mark.asyncio
@patch("routes.ai.check_openai_limit")
@patch("routes.ai.get_gemini_response")
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_with_gemini_when_openai_unavailable(
    mock_get_user,
    mock_gemini_response,
    mock_check_openai,
    mock_db_session,
    mock_openai_unavailable,
    mock_gemini_success,
):
    """Test debugging API using Gemini when OpenAI is unavailable"""
    mock_check_openai.return_value = mock_openai_unavailable.return_value
    mock_gemini_response.return_value = mock_gemini_success.return_value

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=1, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert mock_gemini_response.return_value[0] == response.json()["suggestions"]
    assert "Gemini" == response.json()["ai_provider"]


@pytest.mark.asyncio
@patch("routes.ai.check_openai_limit")
@patch("routes.ai.get_openai_response")
@patch("routes.ai.get_gemini_response")
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_fallback_to_gemini(
    mock_get_user,
    mock_gemini_response,
    mock_openai_response,
    mock_check_openai,
    mock_db_session,
    mock_openai_available,
    mock_openai_failure,
    mock_gemini_success,
):
    """Test debugging API fallback to Gemini when OpenAI fails"""
    mock_check_openai.return_value = mock_openai_available.return_value
    mock_openai_response.return_value = mock_openai_failure.return_value
    mock_gemini_response.return_value = mock_gemini_success.return_value

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=1, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert mock_gemini_response.return_value[0] == response.json()["suggestions"]
    assert "Gemini" == response.json()["ai_provider"]


@pytest.mark.asyncio
@patch("routes.ai.check_openai_limit")
@patch("routes.ai.get_openai_response")
@patch("routes.ai.get_gemini_response")
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_all_providers_fail(
    mock_get_user,
    mock_gemini_response,
    mock_openai_response,
    mock_check_openai,
    mock_db_session,
    mock_openai_available,
    mock_openai_failure,
    mock_gemini_failure,
):
    """Test error handling when both OpenAI and Gemini fail"""
    mock_check_openai.return_value = mock_openai_available.return_value
    mock_openai_response.return_value = mock_openai_failure.return_value
    mock_gemini_response.return_value = mock_gemini_failure.return_value

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=1, content=TEST_CODE_PYTHON
    )

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error with all AI providers" in response.json()["detail"]


@pytest.mark.asyncio
@patch("routes.ai.check_openai_limit")
@patch("routes.ai.get_openai_response")
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_javascript(
    mock_get_user,
    mock_openai_response,
    mock_check_openai,
    mock_db_session,
    mock_openai_available,
    mock_openai_success,
):
    """Test debugging API for JavaScript code"""
    mock_check_openai.return_value = mock_openai_available.return_value
    mock_openai_response.return_value = mock_openai_success.return_value

    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(
        id=2, content=TEST_CODE_JS
    )

    response = client.post("/ai/debug/2", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_200_OK
    assert mock_openai_response.return_value[0] == response.json()["suggestions"]
    assert "OpenAI" == response.json()["ai_provider"]


@pytest.mark.asyncio
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_file_not_found(mock_get_user, mock_db_session):
    """Test error handling when file is not found"""
    # Mock database response
    mock_db_session.query().filter().first.return_value = None

    response = client.post(
        "/ai/debug/99", headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "File not found"


@pytest.mark.asyncio
@patch("routes.ai.get_current_user", side_effect=mock_get_current_user)
async def test_debug_code_empty_file(mock_get_user, mock_db_session):
    """Test handling of an empty code file"""
    # Mock database response
    mock_db_session.query().filter().first.return_value = CodeFile(id=3, content="")

    response = client.post("/ai/debug/3", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Code file is empty"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_check_openai_limit_success(mock_httpx_get):
    """Test successful OpenAI rate limit check"""
    # Mock httpx response for successful API call
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_httpx_get.return_value = mock_response

    from routes.ai import check_openai_limit

    result = await check_openai_limit()
    assert result is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_check_openai_limit_rate_limited(mock_httpx_get):
    """Test OpenAI rate limit exceeded detection"""
    # Mock httpx response for rate limit exceeded
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 429
    mock_httpx_get.return_value = mock_response

    from routes.ai import check_openai_limit

    result = await check_openai_limit()
    assert result is False


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_check_openai_limit_error(mock_httpx_get):
    """Test OpenAI API error handling"""
    # Mock httpx response for other API error
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 500
    mock_httpx_get.return_value = mock_response

    from routes.ai import check_openai_limit

    result = await check_openai_limit()
    assert result is False


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", side_effect=Exception("Connection error"))
async def test_check_openai_limit_exception(mock_httpx_get):
    """Test exception handling in OpenAI limit check"""
    from routes.ai import check_openai_limit

    result = await check_openai_limit()
    assert result is False


@pytest.mark.asyncio
async def test_rate_limit():
    """Test if rate limiting works (returns HTTP 429 on excessive requests)"""
    # Make multiple requests to trigger rate limit
    for _ in range(10):  # Exceeding the rate limit intentionally
        client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})

    response = client.post("/ai/debug/1", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many requests" in response.json()["error"]
