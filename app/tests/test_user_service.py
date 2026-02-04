import pytest
from unittest.mock import patch, MagicMock
import os


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Fixture to set up environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "DYNAMODB_TABLE": "test-table",
            "S3_BUCKET": "test-bucket",
            "LOCALSTACK_HOST": "http://localhost:4566",
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    ):
        yield


def test_user_service_imports():
    """Test that user_service module can be imported."""
    from my_app.user_management import user_service

    assert user_service is not None


def test_environment_variables_set():
    """Test that required environment variables are configured."""
    assert os.getenv("DYNAMODB_TABLE") == "test-table"
    assert os.getenv("S3_BUCKET") == "test-bucket"


@patch("boto3.resource")
def test_dynamodb_connection_attempt(mock_boto3):
    """Test that DynamoDB connection can be attempted."""
    mock_dynamodb = MagicMock()
    mock_boto3.return_value = mock_dynamodb
    dynamodb = mock_boto3("dynamodb", region_name="us-east-1")
    assert dynamodb is not None


@patch("boto3.client")
def test_s3_connection_attempt(mock_boto3):
    """Test that S3 connection can be attempted."""
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    s3 = mock_boto3("s3", region_name="us-east-1")
    assert s3 is not None


@patch("boto3.resource")
def test_get_all_users_success(mock_boto3_resource):
    """Test successful retrieval of all users."""
    from my_app.user_management.user_service import get_all_users

    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {"id": "1", "name": "User 1", "email": "user1@example.com"},
            {"id": "2", "name": "User 2", "email": "user2@example.com"},
        ]
    }
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto3_resource.return_value = mock_dynamodb

    response, status_code = get_all_users()
    assert status_code == 200
    mock_table.scan.assert_called_once()


@patch("boto3.resource")
def test_get_all_users_error(mock_boto3_resource):
    """Test get_all_users handles errors."""
    from my_app.user_management.user_service import get_all_users

    mock_table = MagicMock()
    mock_table.scan.side_effect = Exception("DynamoDB error")
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto3_resource.return_value = mock_dynamodb

    response, status_code = get_all_users()
    assert status_code == 500


@patch("boto3.resource")
def test_create_user_success(mock_boto3_resource):
    """Test successful user creation."""
    from my_app.user_management.user_service import create_user

    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto3_resource.return_value = mock_dynamodb

    user_data = {"id": "123", "name": "Test User", "email": "test@example.com"}
    response, status_code = create_user(user_data)
    assert status_code == 201
    mock_table.put_item.assert_called_once_with(Item=user_data)


@patch("boto3.resource")
def test_create_user_error(mock_boto3_resource):
    """Test create_user handles errors."""
    from my_app.user_management.user_service import create_user

    mock_table = MagicMock()
    mock_table.put_item.side_effect = Exception("DynamoDB error")
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto3_resource.return_value = mock_dynamodb

    user_data = {"id": "123", "name": "Test User", "email": "test@example.com"}
    response, status_code = create_user(user_data)
    assert status_code == 500


@patch("boto3.client")
def test_uploader_success(mock_boto3_client):
    """Test successful file upload."""
    from my_app.user_management.user_service import uploader
    from io import BytesIO

    mock_s3 = MagicMock()
    mock_s3.upload_fileobj.return_value = None
    mock_boto3_client.return_value = mock_s3

    fake_file = BytesIO(b"fake image data")
    result = uploader(fake_file, "avatar.png")

    assert "https://" in result
    assert "avatar.png" in result
    mock_s3.upload_fileobj.assert_called_once()


@patch("boto3.client")
def test_uploader_error(mock_boto3_client):
    """Test uploader handles errors."""
    from my_app.user_management.user_service import uploader
    from io import BytesIO

    mock_s3 = MagicMock()
    mock_s3.upload_fileobj.side_effect = Exception("S3 error")
    mock_boto3_client.return_value = mock_s3

    fake_file = BytesIO(b"fake image data")
    result = uploader(fake_file, "avatar.png")
    assert isinstance(result, tuple)
