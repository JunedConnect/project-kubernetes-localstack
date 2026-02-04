import pytest
from unittest.mock import patch
from flask import Flask
from io import BytesIO
from my_app.user_management.user_routes import (
    user_blueprint,
    validate_user_data,
    allowed_file,
)


def test_validate_user_data_success():
    """Test successful user data validation."""
    data = {"name": "John Doe", "email": "john@example.com"}
    error, status = validate_user_data(data)
    assert error is None
    assert status is None


def test_validate_user_data_missing_fields():
    """Test validation fails when required fields are missing."""
    assert validate_user_data({"email": "test@example.com"})[1] == 400
    assert validate_user_data({"name": "John Doe"})[1] == 400
    assert validate_user_data({})[1] == 400
    assert validate_user_data(None)[1] == 400


def test_allowed_file_extensions():
    """Test file extension validation."""
    assert allowed_file("avatar.png") is True
    assert allowed_file("photo.JPG") is True
    assert allowed_file("image.jpeg") is True
    assert allowed_file("document.pdf") is False
    assert allowed_file("script.exe") is False


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(user_blueprint)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@patch("my_app.user_management.user_routes.get_all_users")
def test_get_users_endpoint(mock_get_all_users, client):
    """Test GET /users endpoint."""
    mock_get_all_users.return_value = ({"users": [{"id": "1"}]}, 200)
    response = client.get("/users")
    assert response.status_code == 200
    mock_get_all_users.assert_called_once()


@patch("my_app.user_management.user_routes.create_user")
@patch("my_app.user_management.user_routes.uploader")
def test_post_user_validation_error(mock_uploader, mock_create_user, client):
    """Test POST /user with validation failure."""
    data = {"email": "test@example.com"}  # missing name
    response = client.post("/user", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    mock_create_user.assert_not_called()


@patch("my_app.user_management.user_routes.create_user")
@patch("my_app.user_management.user_routes.uploader")
def test_post_user_invalid_file(mock_uploader, mock_create_user, client):
    """Test POST /user with invalid file type."""
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "avatar": (BytesIO(b"fake pdf"), "document.pdf"),
    }
    response = client.post("/user", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    mock_uploader.assert_not_called()


@patch("my_app.user_management.user_routes.create_user")
@patch("my_app.user_management.user_routes.uploader")
def test_post_user_success(mock_uploader, mock_create_user, client):
    """Test POST /user success with valid data."""
    mock_uploader.return_value = "https://s3.example.com/avatar.png"
    mock_create_user.return_value = ({"id": "123", "name": "Test User"}, 201)

    data = {
        "name": "Test User",
        "email": "test@example.com",
        "avatar": (BytesIO(b"fake png"), "avatar.png"),
    }
    response = client.post("/user", data=data, content_type="multipart/form-data")

    assert response.status_code == 201
    mock_uploader.assert_called_once()
    mock_create_user.assert_called_once()
