"""
Edge case tests for the signup endpoint (POST /activities/{activity_name}/signup).

Tests focus on boundary conditions, capacity limits, and data integrity.
Follows the AAA (Arrange-Act-Assert) pattern.
"""
import pytest


class TestSignupCapacityLimits:
    """Test signup behavior at capacity limits."""

    def test_signup_when_activity_at_capacity(self, client, initial_activities):
        """Arrange: Fill an activity to max capacity
        Act: Try to signup one more participant
        Assert: Verify signup is rejected (or behavior defined by requirements)
        """
        # Arrange
        activity_name = "Chess Club"
        max_participants = initial_activities[activity_name]["max_participants"]
        existing_count = len(initial_activities[activity_name]["participants"])
        
        # Fill activity to capacity by adding participants
        test_emails = [f"capacity_test_{i}@mergington.edu" for i in range(max_participants - existing_count)]
        for email in test_emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act - Try to signup when at capacity
        over_capacity_email = "over_capacity@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": over_capacity_email}
        )
        
        # Assert - API should allow signup regardless (current behavior)
        # This test documents current behavior; adjust assertion if requirements change
        assert response.status_code == 200, \
            "Current API allows signup even when activity is at capacity"

    def test_signup_near_capacity_succeeds(self, client, initial_activities):
        """Arrange: Fill activity to capacity - 1
        Act: Signup to reach capacity
        Assert: Verify signup succeeds
        """
        # Arrange
        activity_name = "Art Studio"
        max_participants = initial_activities[activity_name]["max_participants"]
        existing_count = len(initial_activities[activity_name]["participants"])
        
        # Fill to capacity - 1
        test_emails = [f"near_cap_{i}@mergington.edu" for i in range(max_participants - existing_count - 1)]
        for email in test_emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act - Signup to reach capacity
        final_email = "final_spot@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": final_email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert final_email in activities[activity_name]["participants"]

    def test_capacity_limit_respected_per_activity(self, client, initial_activities):
        """Arrange: Get max participants for multiple activities
        Act: Verify each activity respects its own limit
        Assert: No activity exceeds its max_participants
        """
        # Arrange
        response = client.get("/activities")
        activities = response.json()
        
        # Act & Assert
        for activity_name, activity_data in activities.items():
            actual_count = len(activity_data["participants"])
            max_allowed = activity_data["max_participants"]
            assert actual_count <= max_allowed, \
                f"Activity '{activity_name}' exceeds capacity: {actual_count} > {max_allowed}"


class TestSignupDataIntegrity:
    """Test data integrity during signup."""

    def test_signup_preserves_existing_participants(self, client, sample_activity_name):
        """Arrange: Note existing participants in activity
        Act: Add new participant via signup
        Assert: Existing participants still present
        """
        # Arrange
        existing_response = client.get("/activities")
        existing_data = existing_response.json()
        original_participants = existing_data[sample_activity_name]["participants"].copy()
        
        # Act
        new_email = "new_participant@mergington.edu"
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        updated_participants = updated_data[sample_activity_name]["participants"]
        
        for original_email in original_participants:
            assert original_email in updated_participants, \
                f"Original participant '{original_email}' was lost during signup"

    def test_signup_does_not_affect_other_activities(self, client):
        """Arrange: Get snapshot of all activities
        Act: Signup to one activity
        Assert: Other activities unchanged
        """
        # Arrange
        before_response = client.get("/activities")
        before_data = before_response.json()
        
        # Act
        client.post(
            f"/activities/Chess Club/signup",
            params={"email": "new_student@mergington.edu"}
        )
        
        # Assert
        after_response = client.get("/activities")
        after_data = after_response.json()
        
        for activity_name in before_data:
            if activity_name != "Chess Club":
                assert before_data[activity_name] == after_data[activity_name], \
                    f"Activity '{activity_name}' was modified by signup to different activity"

    def test_signup_increments_participant_count(self, client, sample_activity_name):
        """Arrange: Get initial participant count
        Act: Signup new participant
        Assert: Count increased by exactly 1
        """
        # Arrange
        before_response = client.get("/activities")
        before_count = len(before_response.json()[sample_activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": "counter_test@mergington.edu"}
        )
        
        # Assert
        after_response = client.get("/activities")
        after_count = len(after_response.json()[sample_activity_name]["participants"])
        
        assert after_count == before_count + 1, \
            f"Participant count should increase by 1, got {after_count - before_count}"


class TestSignupDuplicatePrevention:
    """Test duplicate signup prevention."""

    def test_duplicate_signup_with_exact_same_email(self, client, sample_activity_name):
        """Arrange: Sign up with email
        Act: Try to signup with exact same email
        Assert: Second attempt returns 400
        """
        # Arrange
        test_email = "duplicate_test@mergington.edu"
        
        # Act - First signup
        response1 = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        assert response1.status_code == 200
        
        # Act - Second signup with same email
        response2 = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Assert
        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data
        assert "already" in data["detail"].lower() or "signup" in data["detail"].lower()

    def test_duplicate_signup_error_does_not_modify_data(self, client, sample_activity_name):
        """Arrange: Attempt duplicate signup
        Act: Check if participant count changed
        Assert: Count unchanged after failed duplicate
        """
        # Arrange
        test_email = "dup_check@mergington.edu"
        
        # Sign up once
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Get count after first signup
        after_first = client.get("/activities")
        count_after_first = len(after_first.json()[sample_activity_name]["participants"])
        
        # Act - Try duplicate signup
        duplicate_response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        assert duplicate_response.status_code == 400
        
        # Assert - Count should remain same
        after_duplicate = client.get("/activities")
        count_after_duplicate = len(after_duplicate.json()[sample_activity_name]["participants"])
        
        assert count_after_first == count_after_duplicate, \
            "Failed duplicate signup should not modify participant count"


class TestSignupEmailValidation:
    """Test email-related edge cases in signup."""

    def test_signup_with_different_email_formats(self, client, sample_activity_name):
        """Arrange: Prepare different email formats
        Act: Sign up with each format
        Assert: All succeed (API accepts)
        """
        # Arrange
        email_formats = [
            "simple@example.com",
            "with.dot@example.com",
            "with-dash@example.com",
            "with_underscore@example.com",
            "with+plus@example.com",
        ]
        
        # Act & Assert
        for email in email_formats:
            response = client.post(
                f"/activities/{sample_activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200, f"Email '{email}' should be accepted"

    def test_signup_preserves_email_exactly(self, client, sample_activity_name):
        """Arrange: Signup with specific email
        Act: Retrieve activities and find email
        Assert: Email stored exactly as provided
        """
        # Arrange
        test_email = "PreservedCase@Example.Com"
        
        # Act
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Assert
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email in activities[sample_activity_name]["participants"], \
            f"Email should be preserved exactly as provided: {test_email}"

    @pytest.mark.parametrize("email", [
        "verylongemailaddress@example.com",
        "a@b.co",
        "test.email.with.many.dots@example.com",
    ])
    def test_signup_various_email_formats(self, client, sample_activity_name, email):
        """Arrange: Various valid email formats
        Act: Signup with each format
        Assert: All succeed
        """
        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200


class TestSignupResponseValidation:
    """Test signup response structure and content."""

    def test_signup_response_contains_message(self, client, sample_activity_name):
        """Arrange: Perform signup
        Act: Check response content
        Assert: Message field present with email and activity name
        """
        # Arrange
        test_email = "response_test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]
        assert sample_activity_name in data["message"]

    def test_signup_success_message_contains_confirmation(self, client, sample_activity_name, sample_email):
        """Arrange: Perform valid signup
        Act: Check response message
        Assert: Message confirms signup action
        """
        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        data = response.json()
        message = data["message"].lower()
        assert "sign" in message or "registered" in message or "added" in message, \
            f"Response message should confirm signup: {data['message']}"
