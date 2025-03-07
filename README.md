# 📌 Collaborative AI Code Editor API

## Overview

Welcome to the **Collaborative AI Code Editor API**! This powerful platform enables real-time collaborative coding with AI-powered debugging capabilities, integrated file management, and secure authentication. Built with FastAPI, this API delivers high performance, excellent scalability, and seamless integration options.

## 🚀 Key Features

- **User Authentication & Role Management**: Secure signup, login, and admin user management
- **AI-Powered Code Debugging**: Analyze and improve code with AI assistance
- **File Management System**: Create, retrieve, update, and delete files with ease
- **OAuth2 Token-Based Authentication**: Secure API access with JWT authentication
- **Real-Time Collaboration**: WebSockets for live editing and collaboration
- **Auto-Generated API Documentation**: Complete OpenAPI and Swagger UI documentation
- **Containerized Deployment**: Easy setup with Docker and Docker Compose

## 🔗 API Documentation

Explore the API via OpenAPI documentation:

**Swagger UI**: [https://collaborative-ai-codeeditor.onrender.com/docs](https://collaborative-ai-codeeditor.onrender.com/docs)  
_(Please be patient, as it may take a minute to load since it's hosted on Render's free tier.)_

**YAML Schema**: [https://collaborative-ai-codeeditor.onrender.com/openapi.yaml](https://collaborative-ai-codeeditor.onrender.com/openapi.yaml)

## 📥 Local Installation & Setup

### Prerequisites

Ensure you have the following installed:

- Python 3.8+
- FastAPI
- Uvicorn
- PostgreSQL (Optional, based on database selection)

### Clone & Setup Project

```bash
# Clone the repository
git clone https://github.com/your-repo/collaborative-ai_codeEditor.git
cd collaborative-ai_codeEditor

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

Your API will be running at **http://127.0.0.1:8000**

## 🐳 Docker Deployment

### Using Docker

1. Ensure Docker is installed on your system
2. Navigate to your project directory
3. Build and run the Docker container:

```bash
# Build the Docker image
docker build -t collaborative-ai-codeeditor .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./collab.db \
  -e SECRET_KEY=supersecret \
  -e OPENAI_API_KEY=your_openai_api_key \
  collaborative-ai-codeeditor
```

### Using Docker Compose

1. Make sure Docker and Docker Compose are installed
2. Navigate to your project directory where the `docker-compose.yml` file is located
3. Run:

```bash
# Start the services
docker-compose up

# To run in detached mode
docker-compose up -d

# To stop the services
docker-compose down
```

### Environment Variables

Configure the following environment variables for deployment:

- `DATABASE_URL`: Connection string for your database
- `SECRET_KEY`: Secret key for JWT token generation
- `OPENAI_API_KEY`: Your OpenAI API key for AI debugging features

## 🔑 API Endpoints

### Authentication Endpoints

| **Method** | **Endpoint**            | **Description**                         |
| ---------- | ----------------------- | --------------------------------------- |
| **POST**   | `/auth/register`        | Register a new non-admin user           |
| **POST**   | `/auth/signup-admin`    | Register a new admin user (protected)   |
| **POST**   | `/auth/login`           | Authenticate user & return access token |
| **POST**   | `/auth/initial-admin`   | Create an admin user if none exist      |
| **PUT**    | `/auth/users/{user_id}` | Update user details (protected)         |
| **DELETE** | `/auth/users/{user_id}` | Remove a user (protected)               |

### AI Debugging Endpoints (Protected Routes)

| **Method** | **Endpoint**          | **Description**            |
| ---------- | --------------------- | -------------------------- |
| **POST**   | `/ai/debug/{file_id}` | Debug a code file using AI |

### File Management Endpoints

| **Method** | **Endpoint**       | **Description**     |
| ---------- | ------------------ | ------------------- |
| **GET**    | `/files/`          | List all files      |
| **POST**   | `/files/`          | Create a new file   |
| **GET**    | `/files/{file_id}` | Retrieve a file     |
| **PUT**    | `/files/{file_id}` | Update file content |
| **DELETE** | `/files/{file_id}` | Delete a file       |

### Real-Time Collaboration

| **Method**    | **Endpoint**                 | **Description**                             |
| ------------- | ---------------------------- | ------------------------------------------- |
| **WebSocket** | `/collaborate/ws/{file_id}`  | Real-time collaborative code editing        |
| **WebSocket** | `/collaborate/notifications` | Real-time notifications (e.g., user joined) |

## 🧪 Testing

The project includes comprehensive test cases written with Pytest using a dedicated test database:

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## 🚀 Production Deployment

For production deployment, ensure you:

1. Use a secure, random SECRET_KEY
2. Configure a production database
3. Set up proper CORS settings
4. Use HTTPS for all traffic
5. Consider setting up a reverse proxy (Nginx, Traefik)
6. Implement proper monitoring and logging

## 📜 License

This project is licensed under the **MIT License**. You are free to modify and use it as per the license terms.

## 🤝 Contributing

We welcome contributions! If you'd like to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit & push (`git commit -m "Your message" && git push origin feature-branch`)
5. Open a pull request

---

✨ **Built with FastAPI & ❤️ by [Arnab Samanta]** ✨
