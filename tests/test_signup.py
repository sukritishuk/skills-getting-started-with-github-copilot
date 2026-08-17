"""
Tests for the signup endpoint (POST /activities/{activity_name}/signup).
"""
import pytest


def test_signup_success(client, sample_activity_name, sample_email):
    """Test successful signup for an activity"""
    response = client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert sample_email in data["message"]


def test_signup_adds_participant(client, sample_activity_name, sample_email):
    """Test that signup adds participant to the activity"""
    # Sign up
    response = client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    assert response.status_code == 200
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert sample_email in activities[sample_activity_name]["participants"]


def test_signup_duplicate_email_returns_400(client, sample_activity_name, sample_email):
    """Test that signing up twice with same email returns 400"""
    # First signup
    response1 = client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    assert response1.status_code == 200
    
    # Second signup with same email
    response2 = client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    assert response2.status_code == 400
    data = response2.json()
    assert "detail" in data


def test_signup_invalid_activity_returns_404(client, sample_email):
    """Test that signup for non-existent activity returns 404"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup",
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
def test_signup_various_invalid_activities(client, invalid_activity):
    """Test signup with various invalid activity names"""
    response = client.post(
        f"/activities/{invalid_activity}/signup",
        params={"email": "test@example.com"}
    )
    
    assert response.status_code == 404


def test_signup_already_registered_gets_error_message(client, sample_activity_name, sample_email):
    """Test that duplicate signup returns appropriate error message"""
    # First signup
    client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    
    # Second signup
    response = client.post(
        f"/activities/{sample_activity_name}/signup",
        params={"email": sample_email}
    )
    
    data = response.json()
    assert "already" in data["detail"].lower() or "sign" in data["detail"].lower()
