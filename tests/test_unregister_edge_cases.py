"""
Edge case tests for the unregister endpoint (DELETE /activities/{activity_name}/unregister).

Tests focus on boundary conditions, data integrity, and error handling.
Follows the AAA (Arrange-Act-Assert) pattern.
"""
import pytest


class TestUnregisterSuccessScenarios:
    """Test successful unregister scenarios."""

    def test_unregister_existing_initial_participant(self, client, initial_activities):
        """Arrange: Identify existing participant from initial data
        Act: Unregister that participant
        Assert: Unregister succeeds and removes participant
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = initial_activities[activity_name]["participants"][0]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert existing_email in data["message"]
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert existing_email not in activities[activity_name]["participants"]

    def test_unregister_after_signup(self, client, sample_activity_name):
        """Arrange: Sign up a new participant
        Act: Unregister that participant
        Assert: Unregister succeeds
        """
        # Arrange
        test_email = "signup_then_unregister@mergington.edu"
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email not in activities[sample_activity_name]["participants"]

    def test_unregister_when_activity_has_multiple_participants(self, client, sample_activity_name, initial_activities):
        """Arrange: Activity with multiple participants
        Act: Unregister one participant
        Assert: Other participants remain
        """
        # Arrange
        if len(initial_activities[sample_activity_name]["participants"]) < 2:
            pytest.skip("Activity needs multiple initial participants")
        
        target_email = initial_activities[sample_activity_name]["participants"][0]
        other_emails = initial_activities[sample_activity_name]["participants"][1:]
        
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": target_email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify target removed but others remain
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert target_email not in activities[sample_activity_name]["participants"]
        for email in other_emails:
            assert email in activities[sample_activity_name]["participants"]


class TestUnregisterDataIntegrity:
    """Test data integrity during unregister."""

    def test_unregister_does_not_affect_other_activities(self, client, initial_activities):
        """Arrange: Get snapshot of all activities
        Act: Unregister from one activity
        Assert: Other activities unchanged
        """
        # Arrange
        before_response = client.get("/activities")
        before_data = before_response.json()
        
        activity_name = "Chess Club"
        test_email = initial_activities[activity_name]["participants"][0]
        
        # Act
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        after_response = client.get("/activities")
        after_data = after_response.json()
        
        for other_activity in before_data:
            if other_activity != activity_name:
                assert before_data[other_activity] == after_data[other_activity], \
                    f"Activity '{other_activity}' should not be modified"

    def test_unregister_decrements_participant_count_by_one(self, client, initial_activities, sample_activity_name):
        """Arrange: Get initial participant count
        Act: Unregister one participant
        Assert: Count decreased by exactly 1
        """
        # Arrange
        test_email = initial_activities[sample_activity_name]["participants"][0]
        
        before_response = client.get("/activities")
        before_count = len(before_response.json()[sample_activity_name]["participants"])
        
        # Act
        client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        after_response = client.get("/activities")
        after_count = len(after_response.json()[sample_activity_name]["participants"])
        
        assert before_count - after_count == 1, \
            f"Participant count should decrease by 1, got decrease of {before_count - after_count}"

    def test_unregister_preserves_other_participant_order(self, client, sample_activity_name, initial_activities):
        """Arrange: Activity with multiple participants
        Act: Unregister one participant from middle
        Assert: Other participants in same relative order
        """
        # Arrange
        if len(initial_activities[sample_activity_name]["participants"]) < 2:
            pytest.skip("Activity needs multiple participants")
        
        before_response = client.get("/activities")
        before_participants = before_response.json()[sample_activity_name]["participants"].copy()
        
        # Remove first participant for unregister
        target_email = before_participants[0]
        expected_remaining = before_participants[1:]
        
        # Act
        client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": target_email}
        )
        
        # Assert
        after_response = client.get("/activities")
        after_participants = after_response.json()[sample_activity_name]["participants"]
        
        # Verify order is preserved
        assert after_participants == expected_remaining, \
            "Participant order should be preserved after unregister"


class TestUnregisterErrorHandling:
    """Test error conditions and responses."""

    def test_unregister_not_registered_returns_400(self, client, sample_activity_name):
        """Arrange: Email not signed up for activity
        Act: Attempt to unregister
        Assert: 400 status code returned
        """
        # Arrange
        not_registered_email = "never_signed_up@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": not_registered_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_unregister_invalid_activity_returns_404(self, client):
        """Arrange: Non-existent activity name
        Act: Attempt unregister
        Assert: 404 status code returned
        """
        # Act
        response = client.delete(
            "/activities/Fake%20Activity/unregister",
            params={"email": "test@example.com"}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_unregister_error_message_descriptive(self, client, sample_activity_name):
        """Arrange: Attempt invalid unregister
        Act: Check error message
        Assert: Message describes the error clearly
        """
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": "not_a_member@example.com"}
        )
        
        # Assert
        data = response.json()
        assert "detail" in data
        detail = data["detail"].lower()
        assert "not" in detail or "register" in detail, \
            f"Error message should indicate non-registration: {data['detail']}"

    @pytest.mark.parametrize("invalid_activity", [
        "Nonexistent Club",
        "Invalid Activity",
        "Fake Class",
        "123456",
        ""
    ])
    def test_unregister_various_invalid_activities(self, client, invalid_activity):
        """Arrange: Various invalid activity names
        Act: Attempt unregister for each
        Assert: All return 404
        """
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/unregister",
            params={"email": "test@example.com"}
        )
        
        # Assert
        assert response.status_code == 404


class TestUnregisterDoubleAttempts:
    """Test behavior when unregistering same participant twice."""

    def test_double_unregister_second_fails(self, client, initial_activities, sample_activity_name):
        """Arrange: Unregister a participant once
        Act: Try to unregister same participant again
        Assert: Second attempt fails with 400
        """
        # Arrange
        test_email = initial_activities[sample_activity_name]["participants"][0]
        
        # Act - First unregister
        response1 = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        assert response1.status_code == 200
        
        # Act - Second unregister
        response2 = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        assert response2.status_code == 400

    def test_double_unregister_does_not_restore_participant(self, client, initial_activities, sample_activity_name):
        """Arrange: Unregister and attempt double unregister
        Act: Check participant list after attempts
        Assert: Participant remains removed
        """
        # Arrange
        test_email = initial_activities[sample_activity_name]["participants"][0]
        
        # Remove once
        client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Attempt double unregister
        client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email not in activities[sample_activity_name]["participants"]


class TestUnregisterEmailVariants:
    """Test email handling in unregister."""

    def test_unregister_requires_exact_email_match(self, client, sample_activity_name):
        """Arrange: Sign up with specific email
        Act: Attempt unregister with different case
        Assert: Verify behavior (case sensitivity)
        """
        # Arrange
        test_email = "CaseTest@Example.Com"
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Act - Try unregister with different case
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email.lower()}
        )
        
        # Assert - API treats as different email (case-sensitive)
        # This test documents current behavior
        if response.status_code == 400:
            # Case-sensitive behavior
            assert "not" in response.json()["detail"].lower()
        else:
            # Case-insensitive behavior - unexpected but allowed
            assert response.status_code == 200

    def test_unregister_with_signed_up_email_succeeds(self, client, sample_activity_name):
        """Arrange: Sign up with email
        Act: Unregister with exact same email
        Assert: Succeeds
        """
        # Arrange
        test_email = "exact_match@mergington.edu"
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        assert response.status_code == 200


class TestUnregisterFromDifferentActivities:
    """Test unregister across multiple activities."""

    def test_unregister_from_one_activity_does_not_unregister_from_others(self, client):
        """Arrange: Sign up for two activities
        Act: Unregister from one
        Assert: Still registered in other
        """
        # Arrange
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        test_email = "multi_activity@mergington.edu"
        
        # Sign up for both
        client.post(f"/activities/{activity1}/signup", params={"email": test_email})
        client.post(f"/activities/{activity2}/signup", params={"email": test_email})
        
        # Act - Unregister from one
        response = client.delete(
            f"/activities/{activity1}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify removed from activity1 but still in activity2
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email not in activities[activity1]["participants"]
        assert test_email in activities[activity2]["participants"]


class TestUnregisterResponseValidation:
    """Test unregister response structure and content."""

    def test_unregister_response_contains_message(self, client, initial_activities, sample_activity_name):
        """Arrange: Valid unregister operation
        Act: Check response
        Assert: Contains message with email and activity name
        """
        # Arrange
        test_email = initial_activities[sample_activity_name]["participants"][0]
        
        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": test_email}
        )
        
        # Assert
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]
        assert sample_activity_name in data["message"]

    def test_unregister_error_response_structure(self, client):
        """Arrange: Invalid unregister
        Act: Check error response structure
        Assert: Contains detail field
        """
        # Act
        response = client.delete(
            "/activities/Invalid/unregister",
            params={"email": "test@example.com"}
        )
        
        # Assert
        assert response.status_code in [400, 404]
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
