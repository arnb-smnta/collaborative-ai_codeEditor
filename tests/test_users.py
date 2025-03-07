import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User
from auth import get_password_hash, create_access_token
from datetime import timedelta


#  Utility to create a test user
def create_test_user(db: Session, username, password, is_admin=False):
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


#  Utility to get auth token
def get_auth_token(username):
    return create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=30)
    )


#  Test: Create initial admin
def test_create_initial_admin(client: TestClient):
    response = client.post(
        "/auth/initial-admin", json={"username": "admin", "password": "adminpass"}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Initial admin user created successfully"


#  Test: Initial admin cannot be created when users exist
def test_create_initial_admin_fails_if_users_exist(client: TestClient):
    response = client.post(
        "/auth/initial-admin", json={"username": "another_admin", "password": "pass123"}
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Initial admin can only be created when no users exist"
    )


#  Test: Signup a new user
def test_signup_user(client: TestClient):
    response = client.post(
        "/auth/signup", json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"


#  Test: Signup with existing username fails
def test_signup_duplicate_username(client: TestClient):
    response = client.post(
        "/auth/signup", json={"username": "testuser", "password": "newpass"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


#  Test: Login with correct credentials
def test_login_success(client: TestClient):
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


#  Test: Login with incorrect credentials fails
def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


#  Test: Update user (allowed for self and admins)
def test_update_user(client: TestClient, db_session: Session):
    create_test_user(db_session, "normaluser", "userpass")
    token = get_auth_token("normaluser")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/auth/users/2", json={"username": "updateduser"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully"


#  Test: Update another user fails (without admin rights)
def test_update_user_unauthorized(client: TestClient, db_session: Session):
    create_test_user(db_session, "otheruser", "userpass")
    token = get_auth_token("normaluser")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put("/auth/users/3", json={"username": "hacker"}, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this user"


#  Test: Delete user (self-delete allowed, admin can delete others)
def test_delete_user(client: TestClient, db_session: Session):
    create_test_user(db_session, "deleteuser", "deletepass")
    token = get_auth_token("deleteuser")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/auth/users/4", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"


#  Test: Deleting another user fails (without admin rights)
def test_delete_user_unauthorized(client: TestClient, db_session: Session):
    create_test_user(db_session, "userA", "passA")
    create_test_user(db_session, "userB", "passB")
    token = get_auth_token("userA")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/auth/users/6", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this user"


#  Test: Admin can delete any user
def test_admin_can_delete_user(client: TestClient, db_session: Session):
    create_test_user(db_session, "adminuser", "adminpass", is_admin=True)
    token = get_auth_token("adminuser")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/auth/users/5", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"


#  Test: Cannot delete last admin
def test_cannot_delete_last_admin(client: TestClient):
    token = get_auth_token("admin")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/auth/users/1", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete the last admin user"
