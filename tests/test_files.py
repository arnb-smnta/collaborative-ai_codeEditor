import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
from sqlalchemy.orm import Session
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from models import CodeFile
from auth import create_access_token
from tests.conftest import override_get_db, TestingSessionLocal
from tests.test_users import create_test_user
from auth import get_db

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


#  Helper function to generate auth token
def get_auth_token(username):
    return create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=30)
    )


#  Test: Create a new file
def test_create_file():
    db: Session = TestingSessionLocal()
    user = create_test_user(db, "fileuser", "testpass")
    db.close()

    token = get_auth_token(user.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/files/", headers=headers)

    assert response.status_code == 201
    assert "newFile" in response.json()
    assert response.json()["message"] == "File successfully created"


#  Test: Retrieve a file successfully
def test_get_file():
    db: Session = TestingSessionLocal()
    user = create_test_user(db, "filefetchuser", "testpass")

    new_file = CodeFile(user_id=user.id, content="Sample Content")
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    db.close()

    token = get_auth_token(user.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/files/{new_file.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["file"]["id"] == new_file.id
    assert response.json()["file"]["content"] == "Sample Content"


#  Test: Get all files for a user
def test_get_all_files():
    db: Session = TestingSessionLocal()
    user = create_test_user(db, "filelistuser", "testpass")

    file1 = CodeFile(user_id=user.id, content="File 1")
    file2 = CodeFile(user_id=user.id, content="File 2")
    db.add_all([file1, file2])
    db.commit()
    db.close()

    token = get_auth_token(user.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/files/", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["files"]) == 2


#  Test: Unauthorized user cannot access another user's file
def test_get_file_unauthorized():
    db: Session = TestingSessionLocal()
    user1 = create_test_user(db, "user1", "testpass")
    user2 = create_test_user(db, "user2", "testpass")

    file = CodeFile(user_id=user2.id, content="Private File")
    db.add(file)
    db.commit()
    db.refresh(file)
    db.close()

    token = get_auth_token(user1.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/files/{file.id}", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this file"


#  Test: Update a file successfully
def test_update_file():
    db: Session = TestingSessionLocal()
    user = create_test_user(db, "updateuser", "testpass")

    file = CodeFile(user_id=user.id, content="Old Content")
    db.add(file)
    db.commit()
    db.refresh(file)
    db.close()

    token = get_auth_token(user.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        f"/files/{file.id}", json={"content": "New Updated Content"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "File successfully updated"


#  Test: Prevent unauthorized file update
def test_update_file_unauthorized():
    db: Session = TestingSessionLocal()
    user1 = create_test_user(db, "userA", "testpass")
    user2 = create_test_user(db, "userB", "testpass")

    file = CodeFile(user_id=user2.id, content="Secret Content")
    db.add(file)
    db.commit()
    db.refresh(file)
    db.close()

    token = get_auth_token(user1.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        f"/files/{file.id}", json={"content": "Hacked Content"}, headers=headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this file"


# Test: Delete a file successfully
def test_delete_file():
    db: Session = TestingSessionLocal()
    user = create_test_user(db, "deleteuser", "testpass")

    file = CodeFile(user_id=user.id, content="To be deleted")
    db.add(file)
    db.commit()
    db.refresh(file)
    db.close()

    token = get_auth_token(user.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/files/{file.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "File successfully deleted"


#  Test: Prevent unauthorized file deletion
def test_delete_file_unauthorized():
    db: Session = TestingSessionLocal()
    user1 = create_test_user(db, "deluser1", "testpass")
    user2 = create_test_user(db, "deluser2", "testpass")

    file = CodeFile(user_id=user2.id, content="Secret File")
    db.add(file)
    db.commit()
    db.refresh(file)
    db.close()

    token = get_auth_token(user1.username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/files/{file.id}", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this file"
