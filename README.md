# **📌 Collaborative AI Code Editor API Documentation**

## **🔗 API Documentation**

Explore the API via OpenAPI documentation:

### **Swagger UI**

🔗 **Open API Documentation**[Click here](https://collaborative-ai-codeeditor.onrender.com/docs){:target="\_blank"}  
_(Please be patient, as it may take a minute to load since it's hosted on Render's free tier.)_ 🚀

- **YAML Schema**: [Click Here](https://collaborative-ai-codeeditor.onrender.com/openapi.yaml)

Welcome to the **Collaborative AI Code Editor API**! This API is designed for real-time collaborative coding with **AI-powered debugging**, **file management**, and **secure authentication**. Built with **FastAPI**, it ensures high performance, scalability, and ease of integration.

---

## **🚀 Key Features**

✅ **User Authentication & Role Management** (Signup, Login, Admin Creation)  
✅ **AI-Powered Code Debugging** (Analyze and improve your code)  
✅ **File Management System** (Create, Retrieve, Update, Delete files)  
✅ **OAuth2 Token-Based Authentication** (Secure API access)  
✅ **Real-Time Collaboration** (WebSockets for live editing)  
✅ **Auto-Generated API Documentation** (OpenAPI & Swagger UI)

---

## **📥 Installation & Setup**

### **1️⃣ Prerequisites**

Ensure you have the following installed:

- **Python 3.8+**
- **FastAPI**
- **Uvicorn**
- **PostgreSQL (Optional, based on database selection)**

### **2️⃣ Clone & Setup Project**

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

Now your API is running at **http://127.0.0.1:8000** 🚀

---

## **🔑 Authentication Endpoints**

| **Method** | **Endpoint**            | **Description**                         |
| ---------- | ----------------------- | --------------------------------------- |
| **POST**   | `/auth/signup`          | Register a new user                     |
| **POST**   | `/auth/login`           | Authenticate user & return access token |
| **POST**   | `/auth/initial-admin`   | Create an admin user if none exist      |
| **PUT**    | `/auth/users/{user_id}` | Update user details                     |
| **DELETE** | `/auth/users/{user_id}` | Remove a user                           |

---

## **🤖 AI Debugging Endpoints**

| **Method** | **Endpoint**                             | **Description**                                 |
| ---------- | ---------------------------------------- | ----------------------------------------------- |
| **POST**   | `/ai/debug/{file_id}`                    | Debug a code file using AI                      |
| **POST**   | `/ai/debug/{file_id}/explain`            | Get an explanation for AI debugging suggestions |
| **GET**    | `/ai/debug/models`                       | List available AI debugging models              |
| **POST**   | `/ai/debug/{file_id}/model/{model_name}` | Use a specific AI model for debugging           |

---

## **📂 File Management Endpoints**

| **Method** | **Endpoint**                            | **Description**                 |
| ---------- | --------------------------------------- | ------------------------------- |
| **GET**    | `/files/`                               | List all files                  |
| **POST**   | `/files/`                               | Create a new file               |
| **GET**    | `/files/{file_id}`                      | Retrieve a file                 |
| **PUT**    | `/files/{file_id}`                      | Update file content             |
| **DELETE** | `/files/{file_id}`                      | Delete a file                   |
| **GET**    | `/files/{file_id}/versions`             | Get file version history        |
| **PUT**    | `/files/{file_id}/restore/{version_id}` | Restore a previous file version |
| **POST**   | `/files/{file_id}/share`                | Share file with another user    |
| **GET**    | `/files/{file_id}/permissions`          | Get file permissions            |

---

## **🖥️ Real-Time Collaboration**

| **Method**    | **Endpoint**                 | **Description**                             |
| ------------- | ---------------------------- | ------------------------------------------- |
| **WebSocket** | `/collaborate/ws/{file_id}`  | Real-time collaborative code editing        |
| **WebSocket** | `/collaborate/notifications` | Real-time notifications (e.g., user joined) |

---

---

## **📜 License**

This project is licensed under the **MIT License**. You are free to modify and use it as per the license terms.

---

## **🤝 Contributing**

We welcome contributions! 🎉 If you'd like to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit & push (`git commit -m "Your message" && git push origin feature-branch`)
5. Open a pull request 🚀

---

✨ **Built with FastAPI & ❤️ by [Arnab Samanta]** ✨
