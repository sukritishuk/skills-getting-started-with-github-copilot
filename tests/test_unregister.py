"""
Tests for the unregister endpoint (DELETE /activities/{activity_name}/unregister).
"""
import pytest


def test_unregister_success(client, sample_activity_name, sample_email):
    """Test successful unregister from an activity"""
    # First sign up
    client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    
    # Then unregister
    response = client.delete(
        f"/activities/{sample_activity_name}/unregister",
        params={"email": sample_email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert sample_email in data["message"]


def test_unregister_removes_participant(client, sample_activity_name, sample_email):
    """Test that unregister removes participant from the activity"""
    # Sign up
    client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    
    # Unregister
    response = client.delete(
        f"/activities/{sample_activity_name}/unregister",
        params={"email": sample_email}
    )
    assert response.status_code == 200
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert sample_email not in activities[sample_activity_name]["participants"]


def test_unregister_not_registered_returns_400(client, sample_activity_name, sample_email):
    """Test that unregistering someone not signed up returns 400"""
    response = client.delete(
        f"/activities/{sample_activity_name}/unregister",
        params={"email": sample_email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_unregister_invalid_activity_returns_404(client, sample_email):
    """Test that unregister from non-existent activity returns 404"""
    response = client.delete(
        "/activities/Nonexistent%20Activity/unregister",
        params={"email": sample_email}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.parametrize("invalid_activity", [
    "Nonexistent Club",
    "Invalid Activity",
    "Fake Class",
    ""
])
def test_unregister_various_invalid_activities(client, invalid_activity):
    """Test unregister with various invalid activity names"""
    response = client.delete(
        f"/activities/{invalid_activity}/unregister",
        params={"email": "test@example.com"}
    )
    
    assert response.status_code == 404


def test_unregister_not_registered_error_message(client, sample_activity_name, sample_email):
    """Test that unregister not registered returns appropriate error message"""
    response = client.delete(
        f"/activities/{sample_activity_name}/unregister",
        params={"email": sample_email}
    )
    
    data = response.json()
    assert "not" in data["detail"].lower() or "register" in data["detail"].lower()


def test_unregister_existing_participant(client, sample_activity_name):
    """Test unregistering an existing participant from initial data"""
    # Chess Club has michael@mergington.edu
    response = client.delete(
        f"/activities/{sample_activity_name}/unregister",
        params={"email": "michael@mergington.edu"}
    )
    
    assert response.status_code == 200
    
    # Verify removal
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities[sample_activity_name]["participants"]
