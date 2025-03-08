# 📌 Collaborative AI Code Editor API

## Overview

Welcome to the **Collaborative AI Code Editor API**! This powerful platform enables real-time collaborative coding with AI-powered debugging capabilities, integrated file management, and secure authentication. Built with FastAPI, this API delivers high performance, excellent scalability, and seamless integration options.

## 🔗 API Documentation

### 🔹 Swagger UI

<a href="https://collaborative-ai-codeeditor.onrender.com/docs" target="_blank">Click Here</a>  
_(Please be patient, as it may take a minute to load since it's hosted on Render's free tier.)_

### 🔹 YAML Schema

<a href="https://collaborative-ai-codeeditor.onrender.com/openapi.yaml" target="_blank">Click Here</a>

### 🔹 Postman HTTP REST APIs

<a href="https://documenter.getpostman.com/view/27224450/2sAYdoEmwb#89dab365-ef56-4af9-8246-1ef5698b6122" target="_blank">Click Here</a>

## 🚀 Key Features

- **Real-Time Collaboration**: Multiple users can edit code simultaneously with live cursor tracking and conflict resolution
- **AI-Powered Code Debugging**: OpenAI-based analysis for syntax errors, bugs, and performance improvements
- **User Authentication & Role Management**: Secure signup, login, and role-based access control
- **File Management System**: Complete CRUD operations for code files
- **WebSocket Communication**: Real-time updates and notifications across users
- **Auto-Generated API Documentation**: Comprehensive OpenAPI and Swagger UI documentation
- **Containerized Deployment**: Docker and Docker Compose setup for easy deployment

## 🔧 Technology Stack

- **Backend**: FastAPI, Pydantic, SQLAlchemy ORM
- **Database**: PostgreSQL for persistent storage
- **Real-Time**: WebSockets for live collaboration
- **AI Integration**: OpenAI API for code analysis
- **Authentication**: JWT-based OAuth2 implementation
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest with high coverage

## 🏗️ Architecture

```
┌───────────────────┐          ┌─────────────────────────────┐
│                   │          │                             │
│   Client Browser  │◄────────►│   FastAPI Application       │
│                   │          │                             │
└───────────────────┘          └─────────────────────────────┘
                                           │  ▲
                                           │  │
                                           ▼  │
                               ┌─────────────────────────────┐
                               │                             │
                               │     Authentication          │
                               │     JWT / OAuth2            │
                               │                             │
                               └─────────────────────────────┘
                                           │  ▲
                                           │  │
                                           ▼  │
┌───────────────────┐          ┌─────────────────────────────┐          ┌───────────────────┐
│                   │          │                             │          │                   │
│   WebSocket       │◄────────►│   Collaborative Editing     │◄────────►│   PostgreSQL DB   │
│   Connection      │          │   Controller                │          │                   │
│                   │          │                             │          └───────────────────┘
└───────────────────┘          └─────────────────────────────┘
                                           │  ▲
                                           │  │
                                           ▼  │
                               ┌─────────────────────────────┐          ┌───────────────────┐
                               │                             │          │                   │
                               │   AI Debugging Service      │◄────────►│ OpenAI/Gemini API │
                               │                             │          │                   │
                               └─────────────────────────────┘          └───────────────────┘
                                           │  ▲
                                           │  │
                                           ▼  │
                               ┌─────────────────────────────┐
                               │                             │
                               │   File Management Service   │
                               │                             │
                               └─────────────────────────────┘
```

## 📊 Database Schema

````
User
  - id: UUID (PK)
  - username: String
  - email: String
  - hashed_password: String
  - is_admin: Boolean
  - created_at: DateTime

CodeFile
  - id: UUID (PK)
  - title: String
  - content: Text
  - user_id: UUID (FK → User.id)
  - created_at: DateTime
  - updated_at: DateTime

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
````

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

| **Method**    | **Endpoint**                                     | **Description**                                                          |
| ------------- | ------------------------------------------------ | ------------------------------------------------------------------------ |
| **WebSocket** | `/collaborate/ws/{file_id}`                      | Real-time collaborative code editing                                     |
| **WebSocket** | `/collaborate/notifications/{file_id}`           | Real-time notifications for specific file id connected users             |
| **WebSocket** | `collaborate/notifications/subscribe/{file_id}"` | Real-tme notification sub for differnt files if any one wants to monitor |

Here’s a well-structured **Markdown documentation** for your WebSocket API that you can use in Postman or any other documentation tool:

---

# **📡 WebSocket API Documentation**

## **🔗 Connection Endpoints**

Postman supports WebSockets (currently in beta). To test WebSocket connections in Postman:

1. **Open Postman** and press `Ctrl + N` (or `Cmd + N` on macOS) to create a new request.
2. Select **"WebSocket Request"** from the available options.
3. Enter one of the WebSocket endpoints listed below.
4. Click **Connect** to establish the WebSocket connection.
5. Send and receive messages in real-time.

## **🌍 WebSocket Endpoints**

### **1️⃣ Collaboration WebSocket**

- **URL:**
  ```ws
  ws://localhost:8000/collaborate/ws/2
  ```
- **Description:**  
  This WebSocket connection allows users to collaborate in real-time on shared documents or projects.

- **Example Message Sent by Client:**
  ```json
  {
    "event": "edit",
    "user_id": 2,
    "content": "Updated text"
  }
  ```
- **Example Message Received:**
  ```json
  {
    "event": "update",
    "user_id": 5,
    "content": "User 5 made an update"
  }
  ```

---

### **2️⃣ Notifications WebSocket**

- **URL:**
  ```ws
  ws://localhost:8000/collaborate/notifications/2
  ```
- **Description:**  
  This WebSocket provides real-time notifications for updates, messages, or alerts related to the user.

- **Example Message Sent by Client:**
  ```json
  {
    "event": "subscribe",
    "user_id": 2
  }
  ```
- **Example Message Received:**
  ```json
  {
    "event": "new_notification",
    "message": "You have a new comment on your document"
  }
  ```

---

## **📖 Notes**

- Ensure your local WebSocket server is running before testing.
- Postman WebSocket support is still in **beta**, so some features might change.
- You can write test scripts in Postman to automate sending/receiving messages.

---

## 💻 Real-Time Collaboration Implementation

The real-time collaboration feature is implemented using WebSockets with the following key components:

- **Connection Manager**: Tracks active users and their editing sessions
- **Operational Transformation**: Resolves conflicts when multiple users edit the same section
- **Cursor Tracking**: Shows live positions of all collaborators in the document
- **Event Broadcasting**: Notifies all connected clients about changes in real-time
- **Connection Recovery**: Handles reconnection and state synchronization if connection drops

## 🤖 AI Debugging Integration

The AI-assisted debugging feature leverages the OpenAI API to:

1. Analyze submitted code for syntax errors and logical bugs
2. Suggest performance improvements based on best practices
3. Provide explanations for detected issues
4. Generate sample fixes that users can accept or reject
5. Support multiple programming languages with context-aware suggestions

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
7. uvicorn main:app --host 0.0.0.0 --port $PORT-use this as start command in the render application
8. Dont put PORT variable in env if using render free tier to host

## 🔄 Future Enhancements

The following optional features could be implemented in future versions:

1. **Caching Layer**: Redis integration for improved performance of frequent operations
2. **Message Queue**: Implementation of RabbitMQ for handling high volumes of real-time updates
3. **Version Control**: Git-like functionality for code file history
4. **Extended Language Support**: Expanded AI capabilities for additional programming languages
5. **Frontend Interface**: Dedicated UI built with a modern framework like React

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
