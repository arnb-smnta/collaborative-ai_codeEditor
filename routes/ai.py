from fastapi.responses import JSONResponse
from openai import OpenAI, RateLimitError
from fastapi import APIRouter, Depends, HTTPException, status, Request, FastAPI
import os
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from google import generativeai as genai
import logging
import httpx
import json

from auth import get_db, get_current_user
from models import CodeFile


router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY environment variable not set, will rely on Gemini")

# Gemini configuration
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    logger.warning(
        "GEMINI_API_KEY environment variable not set, fallback won't be available"
    )
else:
    genai.configure(api_key=gemini_api_key)

# Initialize OpenAI client if possible
openai_client = None
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["50/day", "5/minute"],
    storage_uri="memory://",
)


def detect_language(code: str) -> str:
    """Detects if the code is Python or JavaScript based on common syntax patterns."""
    python_indicators = [
        "import ",
        "def ",
        "class ",
        "print(",
        "#",
        "if __name__ ==",
        "->",
        ":",
    ]
    js_indicators = [
        "function ",
        "const ",
        "let ",
        "var ",
        "=>",
        "document.",
        "console.log",
        "export ",
        "import {",
    ]

    python_score = sum(1 for indicator in python_indicators if indicator in code)
    js_score = sum(1 for indicator in js_indicators if indicator in code)

    return (
        "Python"
        if python_score > js_score
        else "JavaScript"
        if js_score > python_score
        else "Unknown"
    )


async def check_openai_limit():
    """
    Check if OpenAI rate limits are available before making a full request
    Returns True if rate limits are available, False otherwise
    """
    if not openai_api_key:
        return False

    try:
        # Make a lightweight models.list call to check if rate limits are available
        # This consumes fewer tokens than a full completion request
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {openai_api_key}"},
            )

            # If we get a 429, rate limits are exceeded
            if response.status_code == 429:
                logger.info("OpenAI rate limits exceeded, switching to Gemini")
                return False

            # Check for other error responses
            if response.status_code != 200:
                logger.warning(
                    f"OpenAI API returned status code {response.status_code}"
                )
                return False

            return True
    except Exception as e:
        logger.warning(f"Error checking OpenAI limits: {str(e)}")
        return False


async def get_openai_response(prompt):
    """Get response from OpenAI API with error handling"""
    if not openai_client:
        return None, "OpenAI API key not configured"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content, None
    except RateLimitError:
        return None, "Rate limit exceeded"
    except Exception as e:
        return None, str(e)


async def get_gemini_response(prompt):
    """Get response from Gemini API with error handling"""
    if not gemini_api_key:
        return None, "Gemini API key not configured"

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)


@router.post("/debug/{file_id}")
@limiter.limit("10/minute; 100/day")
async def debug_code(
    request: Request,
    file_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """AI-powered debugging for Python and JavaScript code."""
    code_file = db.query(CodeFile).filter(CodeFile.id == file_id).first()

    if not code_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    if not code_file.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code file is empty"
        )

    language = detect_language(code_file.content)
    code_content = code_file.content.strip()

    if language == "JavaScript":
        prompt = f"""
        You are an expert JavaScript developer. Analyze the following JavaScript code and provide a structured debugging report.

        --- CODE ---
        ```js
        {code_content}
        ```
        ------------------
        
        **Instructions:**
        1. **Syntax Errors:** Identify incorrect JavaScript syntax and provide corrected versions.
        2. **Logical Errors:** Detect mistakes in conditionals, loops, and function logic.
        3. **Performance Issues:** Suggest faster alternatives (e.g., reduce unnecessary loops).
        4. **Security Risks:** Check for vulnerabilities such as XSS, CSRF, or unsafe eval usage.
        5. **Modern JS Practices:** Suggest improvements using ES6+ features.
        6. **Edge Cases:** Identify where the code might fail.
        7. **Corrected Code & Explanation:** Provide fixes and explain why they are necessary.

        **Now, analyze the JavaScript code and provide a structured debugging report.**
        """

    elif language == "Python":
        prompt = f"""
        You are an expert Python developer. Analyze the following Python code and provide a structured debugging report.

        --- CODE ---
        ```python
        {code_content}
        ```
        ------------------
        
        **Instructions:**
        1. **Syntax Errors:** Identify Python syntax mistakes and provide corrected versions.
        2. **Logical Errors:** Detect issues in loops, conditionals, and function calls.
        3. **Performance Issues:** Suggest optimizations like list comprehensions or avoiding redundant loops.
        4. **Security Risks:** Check for SQL injection, unvalidated inputs, and unsafe file handling.
        5. **Pythonic Best Practices:** Suggest improvements based on PEP-8.
        6. **Edge Cases:** Identify scenarios where this code might fail.
        7. **Corrected Code & Explanation:** Provide fixes and explain why they are necessary.

        **Now, analyze the Python code and provide a structured debugging report.**
        """

    else:
        prompt = f"""
        The following code has been submitted for debugging, but the programming language is unclear.

        --- CODE ---
        ```
        {code_content}
        ```
        ------------------
        
        **Instructions:**
        1. Try to **detect the possible programming language**.
        2. Identify any **syntax errors** and suggest fixes.
        3. Find **logical errors** and provide corrections.
        4. Suggest **best practices** for readability and maintainability.
        5. If you can, **recommend which language this code resembles most**.

        **Now, analyze the code and provide a debugging report.**
        """

    # Check if OpenAI has available rate limits
    openai_available = await check_openai_limit()

    if openai_available:
        # Use OpenAI if rate limits are available
        ai_provider_used = "OpenAI"
        suggestions, error = await get_openai_response(prompt)

        # If the request itself failed, try Gemini
        if not suggestions:
            logger.info(
                f"OpenAI request failed with error: {error}. Falling back to Gemini AI."
            )
            ai_provider_used = "Gemini"
            suggestions, error = await get_gemini_response(prompt)
    else:
        # Use Gemini if OpenAI rate limits are not available
        ai_provider_used = "Gemini"
        suggestions, error = await get_gemini_response(prompt)

    # If both services failed
    if not suggestions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error with all AI providers. Last error: {error}",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "file_id": file_id,
            "suggestions": suggestions,
            "ai_provider": ai_provider_used,
        },
    )


def setup_rate_limiting(app: FastAPI):
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "Too many requests. Please try again later."},
        )
