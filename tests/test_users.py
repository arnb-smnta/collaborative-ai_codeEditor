import sys
import os
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User
from auth import get_password_hash, create_access_token


# Utility to create a test user
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


# Utility to get auth token
def get_auth_token(username):
    return create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=30)
    )


# Test: Create initial admin
def test_create_initial_admin(client: TestClient, db_session: Session):
    # Ensure no users exist in the database
    db_session.query(User).delete()
    db_session.commit()

    response = client.post(
        "/auth/initial-admin", json={"username": "admin", "password": "adminpass"}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Initial admin user created successfully"


# Test: Initial admin cannot be created when users exist
def test_create_initial_admin_fails_if_users_exist(
    client: TestClient, db_session: Session
):
    # Ensure at least one user exists
    if db_session.query(User).count() == 0:
        create_test_user(db_session, "existing_user", "password123")

    response = client.post(
        "/auth/initial-admin", json={"username": "another_admin", "password": "pass123"}
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Initial admin can only be created when no users exist"
    )


# Test: Register a new user
def test_register_user(client: TestClient, db_session: Session):
    response = client.post(
        "/auth/register", json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"
    assert "user_id" in response.json()
    assert response.json()["username"] == "testuser"


# Test: Register with existing username fails
def test_register_duplicate_username(client: TestClient, db_session: Session):
    # Create a user first
    existing_username = "duplicateuser"
    if (
        db_session.query(User).filter(User.username == existing_username).first()
        is None
    ):
        create_test_user(db_session, existing_username, "password123")

    response = client.post(
        "/auth/register", json={"username": existing_username, "password": "newpass123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


# Test: Login with correct credentials
def test_login_success(client: TestClient, db_session: Session):
    # Create a test user
    username = "loginuser"
    password = "loginpass123"
    if db_session.query(User).filter(User.username == username).first() is None:
        create_test_user(db_session, username, password)

    response = client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert response.json()["message"] == "User logged in successfully"
    assert "user" in response.json()
    assert response.json()["user"]["username"] == username


# Test: Login with incorrect credentials fails
def test_login_invalid_credentials(client: TestClient, db_session: Session):
    # Create a test user
    username = "invalidloginuser"
    if db_session.query(User).filter(User.username == username).first() is None:
        create_test_user(db_session, username, "correctpass123")

    response = client.post(
        "/auth/login", data={"username": username, "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


# Test: Update user (allowed for self)
def test_update_self(client: TestClient, db_session: Session):
    # Create a test user
    username = "updateself"
    password = "selfpass123"
    user = create_test_user(db_session, username, password)
    token = get_auth_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    new_username = "updatedselfuser"
    response = client.put(
        f"/auth/users/{user.id}", json={"username": new_username}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully"
    assert response.json()["user"]["username"] == new_username


# Test: Update user password
def test_update_password(client: TestClient, db_session: Session):
    # Create a test user
    username = "passwordupdateuser"
    password = "oldpass123"
    user = create_test_user(db_session, username, password)
    token = get_auth_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    new_password = "newpass123"
    response = client.put(
        f"/auth/users/{user.id}", json={"password": new_password}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully"

    # Verify login works with new password
    response = client.post(
        "/auth/login", data={"username": username, "password": new_password}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# Test: Update another user fails (without admin rights)
def test_update_user_unauthorized(client: TestClient, db_session: Session):
    # Create a normal user
    normal_username = "normaluser"
    normal_user = create_test_user(db_session, normal_username, "userpass123")
    token = get_auth_token(normal_username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create another user
    other_username = "otheruser"
    other_user = create_test_user(db_session, other_username, "otherpass123")

    response = client.put(
        f"/auth/users/{other_user.id}", json={"username": "hackedname"}, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this user"


# Test: Admin can update any user
def test_admin_can_update_user(client: TestClient, db_session: Session):
    # Create an admin user
    admin_username = "adminforupdate"
    admin_user = create_test_user(
        db_session, admin_username, "adminpass123", is_admin=True
    )
    token = get_auth_token(admin_username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a normal user
    normal_username = "normalforupdate"
    normal_user = create_test_user(db_session, normal_username, "userpass123")

    # Admin updates normal user
    new_username = "updatedbyadmin"
    response = client.put(
        f"/auth/users/{normal_user.id}",
        json={"username": new_username, "is_admin": True},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully"
    assert response.json()["user"]["username"] == new_username
    assert response.json()["user"]["is_admin"] is True


# Test: Non-admin can't change admin status
def test_non_admin_cant_change_admin_status(client: TestClient, db_session: Session):
    # Create a normal user
    normal_username = "cantchangeadmin"
    normal_user = create_test_user(db_session, normal_username, "userpass123")
    token = get_auth_token(normal_username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        f"/auth/users/{normal_user.id}", json={"is_admin": True}, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can change admin status"


# Test: Delete user (self-delete allowed)
def test_delete_self(client: TestClient, db_session: Session):
    # Create a test user
    username = "deleteself"
    user = create_test_user(db_session, username, "deletepass123")
    token = get_auth_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/auth/users/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    assert response.json()["user_id"] == user.id

    # Verify user no longer exists
    deleted_user = db_session.query(User).filter(User.id == user.id).first()
    assert deleted_user is None


# Test: Deleting another user fails (without admin rights)
def test_delete_user_unauthorized(client: TestClient, db_session: Session):
    # Create two normal users
    user_a_username = "usera"
    user_a = create_test_user(db_session, user_a_username, "passa123")
    token = get_auth_token(user_a_username)
    headers = {"Authorization": f"Bearer {token}"}

    user_b_username = "userb"
    user_b = create_test_user(db_session, user_b_username, "passb123")

    response = client.delete(f"/auth/users/{user_b.id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this user"

    # Verify user B still exists
    existing_user = db_session.query(User).filter(User.id == user_b.id).first()
    assert existing_user is not None


# Test: Admin can delete any user
def test_admin_can_delete_user(client: TestClient, db_session: Session):
    # Create an admin user
    admin_username = "adminfordelete"
    admin_user = create_test_user(
        db_session, admin_username, "adminpass123", is_admin=True
    )
    token = get_auth_token(admin_username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a normal user
    normal_username = "normalfordelete"
    normal_user = create_test_user(db_session, normal_username, "userpass123")

    response = client.delete(f"/auth/users/{normal_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    assert response.json()["user_id"] == normal_user.id

    # Verify user was deleted
    deleted_user = db_session.query(User).filter(User.id == normal_user.id).first()
    assert deleted_user is None


# Test: Cannot delete last admin
def test_cannot_delete_last_admin(client: TestClient, db_session: Session):
    # Ensure there's only one admin
    db_session.query(User).filter(User.is_admin == True).delete()
    db_session.commit()

    last_admin_username = "lastadmin"
    last_admin = create_test_user(
        db_session, last_admin_username, "adminpass123", is_admin=True
    )
    token = get_auth_token(last_admin_username)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/auth/users/{last_admin.id}", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete the last admin user"

    # Verify admin still exists
    existing_admin = db_session.query(User).filter(User.id == last_admin.id).first()
    assert existing_admin is not None


# Test: Admin can create new admin user
def test_admin_create_admin_user(client: TestClient, db_session: Session):
    # Create an admin user
    admin_username = "adminmaker"
    admin_user = create_test_user(
        db_session, admin_username, "adminpass123", is_admin=True
    )
    token = get_auth_token(admin_username)
    headers = {"Authorization": f"Bearer {token}"}

    new_admin_data = {
        "username": "newadmin",
        "password": "newadminpass123",
        "is_admin": True,
    }

    response = client.post("/auth/signup-admin", json=new_admin_data, headers=headers)
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"
    assert response.json()["username"] == new_admin_data["username"]
    assert response.json()["is_admin"] is True


# Test: Non-admin can't create admin user
def test_non_admin_cant_create_admin(client: TestClient, db_session: Session):
    # Create a normal user
    normal_username = "normauser"
    normal_user = create_test_user(db_session, normal_username, "userpass123")
    token = get_auth_token(normal_username)
    headers = {"Authorization": f"Bearer {token}"}

    new_admin_data = {
        "username": "attemptedadmin",
        "password": "adminpass123",
        "is_admin": True,
    }

    response = client.post("/auth/signup-admin", json=new_admin_data, headers=headers)
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Only admins can create new users with admin privileges"
    )


# Test: Username already exists in signup-admin
def test_signup_admin_duplicate_username(client: TestClient, db_session: Session):
    # Create an admin user
    admin_username = "adminfortesting"
    admin_user = create_test_user(
        db_session, admin_username, "adminpass123", is_admin=True
    )
    token = get_auth_token(admin_username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create another user
    existing_username = "existingusername"
    existing_user = create_test_user(db_session, existing_username, "userpass123")

    # Try to create admin with existing username
    new_admin_data = {
        "username": existing_username,
        "password": "newpass123",
        "is_admin": True,
    }

    response = client.post("/auth/signup-admin", json=new_admin_data, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


# Test: User not found when updating
def test_update_user_not_found(client: TestClient, db_session: Session):
    # Create a user
    username = "updatetester"
    user = create_test_user(db_session, username, "userpass123")
    token = get_auth_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    non_existent_id = 999999  # A user ID that shouldn't exist

    response = client.put(
        f"/auth/users/{non_existent_id}", json={"username": "newname"}, headers=headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# Test: User not found when deleting
def test_delete_user_not_found(client: TestClient, db_session: Session):
    # Create a user
    username = "deletetester"
    user = create_test_user(db_session, username, "userpass123")
    token = get_auth_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    non_existent_id = 999999  # A user ID that shouldn't exist

    response = client.delete(f"/auth/users/{non_existent_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# Test: Username already taken when updating
def test_update_username_already_taken(client: TestClient, db_session: Session):
    # Create two users
    username1 = "firstuser"
    user1 = create_test_user(db_session, username1, "userpass123")

    username2 = "seconduser"
    user2 = create_test_user(db_session, username2, "userpass123")
    token = get_auth_token(username2)
    headers = {"Authorization": f"Bearer {token}"}

    # Try to update second user with first user's username
    response = client.put(
        f"/auth/users/{user2.id}", json={"username": username1}, headers=headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"
