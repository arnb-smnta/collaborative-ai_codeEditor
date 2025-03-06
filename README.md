# API Documentation

## 📌 Overview

Welcome to the **FastAPI Backend**! This API provides authentication, AI-powered debugging, and file management functionalities. Designed with scalability and security in mind, it leverages **OAuth2 authentication** and follows best practices for modern web applications.

## 🚀 Features

- **User Authentication** (Signup, Login, Admin Creation, User Management)
- **AI-Powered Code Debugging**
- **File Management System** (Upload, Retrieve, Update, Delete)
- **OAuth2 Token-Based Authentication**
- **Auto-Generated API Documentation** (OpenAPI Schema)

## 📥 Installation

### 1️⃣ Prerequisites

Ensure you have the following installed:

- Python 3.8+
- FastAPI
- Uvicorn
- PostgreSQL (Optional, based on your database setup)

### 2️⃣ Setup & Run

```bash
# Clone the repository
git clone https://github.com/your-repo/fastapi-backend.git
cd fastapi-backend

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

## 🔑 Authentication Endpoints

| Method | Endpoint                | Description                               |
| ------ | ----------------------- | ----------------------------------------- |
| POST   | `/auth/signup`          | Register a new user                       |
| POST   | `/auth/login`           | Authenticate user and return access token |
| POST   | `/auth/initial-admin`   | Create an admin user if no users exist    |
| PUT    | `/auth/users/{user_id}` | Update user details                       |
| DELETE | `/auth/users/{user_id}` | Remove a user                             |

## 🤖 AI Debugging Endpoints

| Method | Endpoint              | Description                |
| ------ | --------------------- | -------------------------- |
| POST   | `/ai/debug/{file_id}` | Debug a code file using AI |

## 📂 File Management Endpoints

| Method | Endpoint           | Description             |
| ------ | ------------------ | ----------------------- |
| GET    | `/files/`          | List all files          |
| POST   | `/files/`          | Create a new file       |
| GET    | `/files/{file_id}` | Retrieve a file         |
| PUT    | `/files/{file_id}` | Update a file's content |
| DELETE | `/files/{file_id}` | Delete a file           |

## 🔗 API Documentation

This API uses OpenAPI for auto-generated documentation. You can access it at:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **YAML Schema**: [http://127.0.0.1:8000/openapi.yaml](http://127.0.0.1:8000/openapi.yaml)

## 📜 License

This project is licensed under the **MIT License**.

## 🤝 Contributing

We welcome contributions! Feel free to fork, open issues, and submit PRs.

---

✨ **Built with FastAPI & ❤️ by [Arnab Samanta]** ✨
