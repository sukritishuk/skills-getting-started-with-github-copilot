"""
Edge case tests for the activities list endpoint (GET /activities).

Tests focus on boundary conditions, data consistency, and response structure.
Follows the AAA (Arrange-Act-Assert) pattern.
"""
import pytest


class TestActivitiesListDataConsistency:
    """Test data consistency and structure validation."""

    def test_participant_count_matches_list_length(self, client):
        """Arrange: Request activities data
        Act: Compare max_participants against actual participant list length
        Assert: Verify relationship between count and list
        """
        # Arrange
        response = client.get("/activities")
        data = response.json()

        # Act & Assert
        for activity_name, activity_data in data.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            # Verify count doesn't exceed max
            assert participant_count <= max_participants, \
                f"Activity '{activity_name}' has {participant_count} participants " \
                f"but max is {max_participants}"

    def test_activities_response_is_consistent(self, client):
        """Arrange: Call GET /activities twice
        Act: Compare responses
        Assert: Verify identical data returned
        """
        # Arrange & Act
        response1 = client.get("/activities")
        response2 = client.get("/activities")
        
        data1 = response1.json()
        data2 = response2.json()

        # Assert
        assert data1 == data2, "Activities data should be consistent across multiple requests"

    def test_all_activities_have_consistent_schema(self, client):
        """Arrange: Get all activities
        Act: Check each activity's schema
        Assert: All activities follow same structure
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert - verify all activities have identical field types
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            # All participants should be strings (emails)
            assert all(isinstance(email, str) for email in activity_data["participants"])

    def test_description_not_empty(self, client):
        """Arrange: Get activities
        Act: Check descriptions
        Assert: All activities have non-empty descriptions
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert len(activity_data["description"]) > 0, \
                f"Activity '{activity_name}' has empty description"

    def test_schedule_not_empty(self, client):
        """Arrange: Get activities
        Act: Check schedules
        Assert: All activities have non-empty schedules
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert len(activity_data["schedule"]) > 0, \
                f"Activity '{activity_name}' has empty schedule"

    def test_max_participants_positive(self, client):
        """Arrange: Get activities
        Act: Check max_participants values
        Assert: All are positive integers
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0, \
                f"Activity '{activity_name}' has non-positive max_participants"


class TestActivitiesListResponseStatus:
    """Test response status codes and headers."""

    def test_get_activities_returns_200(self, client):
        """Arrange: Ready to request activities
        Act: Send GET request
        Assert: Verify 200 status code
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_response_content_type_is_json(self, client):
        """Arrange: Request activities
        Act: Check response headers
        Assert: Verify application/json content type
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert "application/json" in response.headers.get("content-type", "")

    def test_response_has_reasonable_size(self, client):
        """Arrange: Get activities response
        Act: Check response size
        Assert: Verify response is not empty but reasonable
        """
        # Arrange & Act
        response = client.get("/activities")
        
        # Assert
        assert len(response.content) > 100, "Response should contain activity data"
        assert len(response.content) < 100000, "Response should not be excessively large"


class TestActivitiesListComprehensiveness:
    """Test that activities list is comprehensive."""

    def test_minimum_expected_activities_count(self, client):
        """Arrange: Get activities
        Act: Count activities
        Assert: Verify expected number of activities exist
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert - Based on app.py, there should be 9 activities
        assert len(data) == 9, "Should have all 9 expected activities"

    def test_specific_activities_exist(self, client):
        """Arrange: Get activities
        Act: Check for specific activity names
        Assert: Verify all key activities present
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        
        key_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Science Club",
            "Debate Team"
        }

        # Assert
        for activity in key_activities:
            assert activity in data, f"Activity '{activity}' should exist"


class TestActivitiesListParticipantData:
    """Test participant-related data in activities list."""

    def test_participants_is_always_list_not_none(self, client):
        """Arrange: Get activities
        Act: Check participants field
        Assert: Verify never None, always list
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert activity_data["participants"] is not None
            assert isinstance(activity_data["participants"], list)

    def test_no_duplicate_emails_in_participants(self, client):
        """Arrange: Get activities
        Act: Check for duplicate emails in participant lists
        Assert: Verify no duplicates
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            participants = activity_data["participants"]
            assert len(participants) == len(set(participants)), \
                f"Activity '{activity_name}' has duplicate participants"

    def test_participants_are_valid_emails(self, client):
        """Arrange: Get activities
        Act: Check participant email format
        Assert: Verify all follow email pattern
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            for email in activity_data["participants"]:
                assert "@" in email, f"Participant '{email}' in '{activity_name}' is not valid email format"
                assert "." in email, f"Participant '{email}' in '{activity_name}' is not valid email format"
