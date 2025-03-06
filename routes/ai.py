from fastapi.responses import JSONResponse
from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException, status
import os
from sqlalchemy.orm import Session

from auth import get_db, get_current_user
from models import CodeFile

router = APIRouter()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=openai_api_key)


def detect_language(code: str) -> str:
    """
    Detects if the code is written in Python or JavaScript based on common syntax patterns.
    """
    # More robust language detection
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

    if python_score > js_score:
        return "Python"
    elif js_score > python_score:
        return "JavaScript"
    else:
        return "Unknown"


@router.post("/debug/{file_id}")
def debug_code(
    file_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
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
        1. **Syntax Errors:** Identify any incorrect JavaScript syntax and provide corrected versions.
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
        # **Handle Unknown Language Gracefully**
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
    try:
        response = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "system", "content": prompt}]
        )
        suggestions = response.choices[0].message.content

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"file_id": file_id, "suggestions": suggestions},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while debugging: {str(e)}",
        )
