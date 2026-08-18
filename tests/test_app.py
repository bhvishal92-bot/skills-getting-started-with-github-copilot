"""
Tests for the Mergington High School Activities API

Tests cover all endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/signup
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a TestClient for testing the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_activity():
    """Return a valid activity name from the app's activities."""
    return "Chess Club"


@pytest.fixture
def test_email():
    """Return a test email address."""
    return "test.student@mergington.edu"


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status code 200."""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned."""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) >= 9  # At least 9 activities defined
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_details in activities.items():
            for field in required_fields:
                assert field in activity_details, f"Activity '{activity_name}' missing field '{field}'"

    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is a list."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert isinstance(
                activity_details["participants"], list
            ), f"Participants for '{activity_name}' is not a list"

    def test_get_activities_max_participants_is_integer(self, client):
        """Test that max_participants field is an integer."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert isinstance(
                activity_details["max_participants"], int
            ), f"max_participants for '{activity_name}' is not an integer"


class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client, test_activity, test_email):
        """Test successful signup for a new participant."""
        response = client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]

    def test_signup_adds_participant_to_activity(self, client, test_activity, test_email):
        """Test that signup actually adds the participant to the activity."""
        # Sign up
        client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        
        # Fetch activities and verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert test_email in activities[test_activity]["participants"]

    def test_signup_activity_not_found(self, client, test_email):
        """Test signup fails when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": test_email}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up(self, client, test_activity):
        """Test that signing up twice for same activity fails."""
        test_email = "duplicate.test@mergington.edu"
        
        # First signup
        response1 = client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_at_capacity(self, client):
        """Test that signup fails when activity is at full capacity."""
        # Create a full activity by getting an activity and checking its capacity
        response = client.get("/activities")
        activities = response.json()
        
        # Find an activity that's at or near capacity
        # For testing, we'll use Tennis which has max_participants: 10
        full_activity = "Tennis"
        activity_data = activities[full_activity]
        current_participants = len(activity_data["participants"])
        max_participants = activity_data["max_participants"]
        
        # Keep signing up until at capacity
        for i in range(max_participants - current_participants):
            test_email = f"capacity.test.{i}@mergington.edu"
            response = client.post(
                f"/activities/{full_activity}/signup",
                params={"email": test_email}
            )
            assert response.status_code == 200
        
        # Now try to sign up one more - should fail
        over_capacity_email = "over.capacity@mergington.edu"
        response = client.post(
            f"/activities/{full_activity}/signup",
            params={"email": over_capacity_email}
        )
        assert response.status_code == 400
        assert "at capacity" in response.json()["detail"]


class TestDeleteSignup:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_delete_successful(self, client):
        """Test successful removal of a participant."""
        test_activity = "Art Club"
        test_email = "delete.test@mergington.edu"
        
        # First, sign up
        client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        
        # Then delete
        response = client.delete(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]

    def test_delete_removes_participant_from_activity(self, client):
        """Test that delete actually removes the participant."""
        test_activity = "Music Band"
        test_email = "remove.test@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert test_email in activities[test_activity]["participants"]
        
        # Delete
        client.delete(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert test_email not in activities[test_activity]["participants"]

    def test_delete_activity_not_found(self, client, test_email):
        """Test delete fails when activity doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": test_email}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_delete_participant_not_found(self, client, test_activity):
        """Test delete fails when participant is not signed up for activity."""
        test_email = "not.signed.up@mergington.edu"
        
        response = client.delete(
            f"/activities/{test_activity}/signup",
            params={"email": test_email}
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
