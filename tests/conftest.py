"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient instance for testing the FastAPI application.
    """
    return TestClient(app)


@pytest.fixture
def initial_activities():
    """
    Provide a copy of the initial activities data.
    This allows tests to reference the original state.
    """
    return deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset activities to initial state before each test.
    This ensures test isolation and prevents test pollution.
    Runs automatically before each test (autouse=True).
    """
    # Save original state
    original_state = deepcopy(activities)
    
    yield  # Run the test
    
    # Restore original state after test
    activities.clear()
    activities.update(original_state)


@pytest.fixture
def sample_email():
    """Provide a test email address."""
    return "test@mergington.edu"


@pytest.fixture
def sample_activity_name():
    """Provide a valid test activity name."""
    return "Chess Club"
