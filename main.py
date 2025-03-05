from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import users, files, collaboration, ai
import os
from db import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Real-Time Collaborative Code - Editor ",
    description="A Fast-api powered real time ai editor with specific out of the world ai support for python and js",
    version="1.0.0",
)

origins = os.getenv("CORS_ORIGIN", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/files", tags=["Code Files"])
app.include_router(collaboration.router, prefix="/collaborate", tags=["Collaboration"])
app.include_router(ai.router, prefix="/ai", tags=["AI Debugging"])


@app.get("/")
def root():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Welcome to the real time Code Editor with AI support"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
