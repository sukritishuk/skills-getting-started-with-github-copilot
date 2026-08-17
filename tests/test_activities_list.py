"""
Tests for the activities list endpoint (GET /activities).
"""
import pytest


def test_get_activities_returns_200(client):
    """Test that GET /activities returns 200 OK"""
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict(client):
    """Test that GET /activities returns a dictionary/JSON object"""
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)


def test_get_activities_contains_expected_activities(client):
    """Test that the response contains all expected activities"""
    response = client.get("/activities")
    data = response.json()
    
    expected_activities = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Drama Club",
        "Art Studio",
        "Science Club",
        "Debate Team"
    ]
    
    for activity_name in expected_activities:
        assert activity_name in data


def test_activity_has_required_fields(client):
    """Test that each activity has the required structure"""
    response = client.get("/activities")
    data = response.json()
    
    required_fields = ["description", "schedule", "max_participants", "participants"]
    
    for activity_name, activity_data in data.items():
        for field in required_fields:
            assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"


def test_activity_participants_is_list(client):
    """Test that participants field is a list"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity_data in data.items():
        assert isinstance(activity_data["participants"], list), \
            f"Activity '{activity_name}' participants is not a list"


def test_activity_max_participants_is_integer(client):
    """Test that max_participants field is an integer"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity_data in data.items():
        assert isinstance(activity_data["max_participants"], int), \
            f"Activity '{activity_name}' max_participants is not an integer"


def test_chess_club_has_participants(client):
    """Test that Chess Club has expected initial participants"""
    response = client.get("/activities")
    data = response.json()
    chess_club = data["Chess Club"]
    
    assert len(chess_club["participants"]) >= 1
    assert "michael@mergington.edu" in chess_club["participants"]
    assert "daniel@mergington.edu" in chess_club["participants"]
