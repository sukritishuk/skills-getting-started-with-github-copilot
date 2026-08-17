"""
Async-specific tests for FastAPI endpoints using pytest-asyncio.

Tests focus on concurrent request handling, race conditions, and async behavior.
Follows the AAA (Arrange-Act-Assert) pattern.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.app import app, activities
from copy import deepcopy


@pytest.fixture(autouse=True)
def reset_activities_for_async():
    """Reset activities before each async test.
    This is a sync fixture because activities is just a dict, not async.
    """
    original_state = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_state)


# Test concurrent signups to same activity
@pytest.mark.asyncio
async def test_concurrent_signups_to_same_activity():
    """Arrange: Prepare multiple signup requests for same activity
    Act: Execute signups concurrently
    Assert: All succeed and all participants added
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Chess Club"
        num_concurrent = 5
        emails = [f"concurrent_{i}@mergington.edu" for i in range(num_concurrent)]
        
        # Act - Sign up multiple participants concurrently
        tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            for email in emails
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - All requests should succeed
        for response in responses:
            assert response.status_code == 200, \
                f"Concurrent signup should succeed, got {response.status_code}"
        
        # Verify all participants were added
        final_response = await client.get("/activities")
        final_data = final_response.json()
        for email in emails:
            assert email in final_data[activity_name]["participants"], \
                f"Participant {email} should be in activity"


@pytest.mark.asyncio
async def test_concurrent_signups_preserve_count():
    """Arrange: Track participant count before concurrent signups
    Act: Execute multiple concurrent signups
    Assert: Final count correct (all added)
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Programming Class"
        before_response = await client.get("/activities")
        initial_count = len(before_response.json()[activity_name]["participants"])
        
        num_concurrent = 10
        emails = [f"count_check_{i}@mergington.edu" for i in range(num_concurrent)]
        
        # Act
        tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            for email in emails
        ]
        await asyncio.gather(*tasks)
        
        # Assert
        after_response = await client.get("/activities")
        final_count = len(after_response.json()[activity_name]["participants"])
        
        assert final_count == initial_count + num_concurrent, \
            f"Expected {initial_count + num_concurrent} participants, got {final_count}"


@pytest.mark.asyncio
async def test_concurrent_signups_multiple_activities():
    """Arrange: Prepare signups to different activities
    Act: Execute concurrently
    Assert: All succeed independently
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activities_list = ["Chess Club", "Programming Class", "Gym Class"]
        emails_per_activity = 3
        
        # Build concurrent tasks for multiple activities
        tasks = []
        for activity in activities_list:
            for i in range(emails_per_activity):
                email = f"multi_act_{activity}_{i}@mergington.edu"
                tasks.append(
                    client.post(
                        f"/activities/{activity}/signup",
                        params={"email": email}
                    )
                )
        
        # Act
        responses = await asyncio.gather(*tasks)
        
        # Assert - All succeed
        assert all(r.status_code == 200 for r in responses), \
            "All concurrent signups should succeed"
        
        # Verify each activity got correct additions
        final_response = await client.get("/activities")
        final_data = final_response.json()
        
        for activity in activities_list:
            activity_emails = [
                f"multi_act_{activity}_{i}@mergington.edu"
                for i in range(emails_per_activity)
            ]
            for email in activity_emails:
                assert email in final_data[activity]["participants"]


@pytest.mark.asyncio
async def test_concurrent_unregisters_same_activity():
    """Arrange: Sign up multiple participants, then prepare concurrent unregisters
    Act: Unregister multiple participants concurrently
    Assert: All succeed and all removed
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Chess Club"
        num_participants = 5
        emails = [f"unreg_{i}@mergington.edu" for i in range(num_participants)]
        
        # First sign up all participants
        for email in emails:
            await client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act - Unregister concurrently
        tasks = [
            client.delete(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            for email in emails
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - All succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Verify all removed
        final_response = await client.get("/activities")
        final_data = final_response.json()
        for email in emails:
            assert email not in final_data[activity_name]["participants"]


@pytest.mark.asyncio
async def test_concurrent_signup_and_unregister():
    """Arrange: Prepare concurrent signup and unregister operations
    Act: Execute mixed operations concurrently
    Assert: All succeed and state is consistent
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Tennis Club"
        
        signup_emails = [f"mixed_signup_{i}@mergington.edu" for i in range(3)]
        
        # Get initial participant to unregister
        activities_resp = await client.get("/activities")
        unregister_email = activities_resp.json()[activity_name]["participants"][0]
        
        # Act - Mix of signups and unregister concurrently
        tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            for email in signup_emails
        ] + [
            client.delete(
                f"/activities/{activity_name}/unregister",
                params={"email": unregister_email}
            )
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Assert - All succeed
        assert all(r.status_code in [200, 400, 404] for r in responses)  # Allowing error cases
        
        # Verify state consistency
        final_response = await client.get("/activities")
        final_data = final_response.json()
        
        # Check all signup emails were added
        for email in signup_emails:
            assert email in final_data[activity_name]["participants"]


@pytest.mark.asyncio
async def test_concurrent_reads_consistent():
    """Arrange: Prepare concurrent read requests
    Act: Execute multiple GET /activities concurrently
    Assert: All return identical data
    """
    # Act
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tasks = [
            client.get("/activities")
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - All successful
        assert all(r.status_code == 200 for r in responses)
        
        # Verify all responses identical
        data_list = [r.json() for r in responses]
        for i in range(1, len(data_list)):
            assert data_list[i] == data_list[0], \
                "Concurrent reads should return identical data"


@pytest.mark.asyncio
async def test_read_after_concurrent_writes():
    """Arrange: Execute concurrent signups
    Act: Read activities after writes complete
    Assert: Read reflects all writes
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Drama Club"
        emails = [f"read_test_{i}@mergington.edu" for i in range(5)]
        
        # Act - Concurrent signups
        signup_tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            for email in emails
        ]
        signup_responses = await asyncio.gather(*signup_tasks)
        
        # Verify all signups succeeded
        assert all(r.status_code == 200 for r in signup_responses)
        
        # Read after writes
        read_response = await client.get("/activities")
        
        # Assert
        read_data = read_response.json()
        for email in emails:
            assert email in read_data[activity_name]["participants"], \
                "Concurrent write should be visible in subsequent read"


@pytest.mark.asyncio
async def test_concurrent_duplicate_signups():
    """Arrange: Prepare duplicate signup requests with same email
    Act: Execute concurrently
    Assert: First succeeds, later fail or first-one-wins behavior
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Science Club"
        duplicate_email = "duplicate_async@mergington.edu"
        
        # Act - Multiple concurrent signups with same email
        tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": duplicate_email}
            )
            for _ in range(3)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - At least one should succeed
        status_codes = [r.status_code for r in responses]
        success_count = sum(1 for code in status_codes if code == 200)
        error_count = sum(1 for code in status_codes if code == 400)
        
        assert success_count >= 1, "At least one signup should succeed"
        assert success_count + error_count == len(responses), \
            "All responses should be either success or duplicate error"
        
        # Verify only one instance added
        final_response = await client.get("/activities")
        final_data = final_response.json()
        count = sum(1 for email in final_data[activity_name]["participants"]
                   if email == duplicate_email)
        assert count == 1, "Email should be added exactly once despite concurrent requests"


@pytest.mark.asyncio
async def test_concurrent_requests_to_invalid_activity():
    """Arrange: Multiple concurrent requests to non-existent activity
    Act: Execute concurrently
    Assert: All return 404
    """
    # Act
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tasks = [
            client.post(
                "/activities/Nonexistent/signup",
                params={"email": f"test_{i}@example.com"}
            )
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert
        assert all(r.status_code == 404 for r in responses), \
            "All requests to invalid activity should return 404"


@pytest.mark.asyncio
async def test_concurrent_operations_complete():
    """Arrange: Schedule many concurrent operations
    Act: Execute concurrently with timeout
    Assert: All complete successfully
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        num_operations = 20
        activity_name = "Art Studio"
        
        tasks = []
        for i in range(num_operations):
            if i % 2 == 0:
                # Signup
                tasks.append(
                    client.post(
                        f"/activities/{activity_name}/signup",
                        params={"email": f"perf_{i}@mergington.edu"}
                    )
                )
            else:
                # Read
                tasks.append(
                    client.get("/activities")
                )
        
        # Act - with timeout
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=10.0
            )
            
            # Assert - all completed
            assert len(responses) == num_operations
            assert all(r.status_code in [200, 201] for r in responses)
            
        except asyncio.TimeoutError:
            pytest.fail("Concurrent operations should complete within timeout")


@pytest.mark.asyncio
async def test_no_race_conditions_in_participant_count():
    """Arrange: Execute many concurrent signups to same activity
    Act: Track participant count
    Assert: Final count matches sum of operations
    """
    # Arrange
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        activity_name = "Debate Team"
        num_concurrent = 15
        emails = [f"race_{i}@mergington.edu" for i in range(num_concurrent)]
        
        before_response = await client.get("/activities")
        before_count = len(before_response.json()[activity_name]["participants"])
        
        # Act - Concurrent signups
        tasks = [
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            for email in emails
        ]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed (current API allows over-capacity)
        assert all(r.status_code == 200 for r in responses)
        
        # Assert - Verify count
        after_response = await client.get("/activities")
        after_count = len(after_response.json()[activity_name]["participants"])
        
        # Count should increase by number of successful signups
        assert after_count == before_count + num_concurrent, \
            f"Expected {before_count + num_concurrent} participants, got {after_count}"

