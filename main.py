from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import users, files, collaboration, ai
import os
from db import engine, Base
from fastapi.openapi.utils import get_openapi
import yaml

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


@app.get("/openapi.yaml")
async def get_openapi_yaml():
    openapi_json = get_openapi(
        title="API Yaml file",
        version="1.0.0",
        description="This is an automatically generated OpenAPI schema .",
        routes=app.routes,
    )
    openapi_yaml = yaml.dump(openapi_json, default_flow_style=False)
    return openapi_yaml


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # Use Render's assigned port
    uvicorn.run(app, host="0.0.0.0", port=port)
