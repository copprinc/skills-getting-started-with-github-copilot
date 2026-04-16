"""Tests for the Mergington High School Activities API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and conditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a clean state before each test"""
    # Arrange: Define the initial state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Act: Reset the activities state
    activities.clear()
    activities.update(original)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Should return all available activities"""
        # Arrange
        expected_activity = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) >= 3
        assert expected_activity in data

    def test_get_activities_includes_descriptions(self, client):
        """Should include activity descriptions in response"""
        # Arrange
        expected_description = "Learn strategies and compete in chess tournaments"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert data["Chess Club"]["description"] == expected_description

    def test_get_activities_includes_participants_list(self, client):
        """Should include a list of current participants for each activity"""
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "participants" in data[activity_name]
        assert isinstance(data[activity_name]["participants"], list)
        assert len(data[activity_name]["participants"]) > 0

    def test_get_activities_includes_capacity_info(self, client):
        """Should include max participants and current participant count"""
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "max_participants" in data[activity_name]
        assert data[activity_name]["max_participants"] == 12


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_succeeds(self, client):
        """Should successfully sign up a new student for an activity"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert email in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Should add the student to the activity's participant list"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert email in data[activity]["participants"]

    def test_signup_for_nonexistent_activity_fails(self, client):
        """Should return 404 when signing up for an activity that doesn't exist"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student_fails(self, client):
        """Should reject signup if student is already registered"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"]

    def test_signup_multiple_different_students(self, client):
        """Should allow multiple different students to sign up"""
        # Arrange
        activity = "Chess Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        get_response = client.get("/activities")
        data = get_response.json()
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in data[activity]["participants"]
        assert email2 in data[activity]["participants"]

    def test_signup_same_student_multiple_activities(self, client):
        """Should allow a student to sign up for multiple different activities"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participant endpoint"""

    def test_remove_existing_participant_succeeds(self, client):
        """Should successfully remove a participant from an activity"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity}/participant?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in data["message"]
        assert email in data["message"]

    def test_remove_participant_actually_removes(self, client):
        """Should remove the participant from the activity's list"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity}/participant?email={email}")
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert email not in data[activity]["participants"]

    def test_remove_from_nonexistent_activity_fails(self, client):
        """Should return 404 when removing from an activity that doesn't exist"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity}/participant?email={email}")
        
        # Assert
        assert response.status_code == 404

    def test_remove_student_not_in_activity_fails(self, client):
        """Should return 400 when removing a student who isn't registered"""
        # Arrange
        activity = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity}/participant?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"]

    def test_remove_one_participant_keeps_others(self, client):
        """Should only remove the specified participant, leaving others intact"""
        # Arrange
        activity = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity}/participant?email={email_to_remove}")
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert email_to_remove not in data[activity]["participants"]
        assert email_to_keep in data[activity]["participants"]


class TestSignupAndRemovalWorkflows:
    """Integration tests for complex workflows combining signup and removal"""

    def test_signup_remove_signup_workflow(self, client):
        """Should allow a student to signup, be removed, and signup again"""
        # Arrange
        activity = "Programming Class"
        email = "workflow@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Remove
        remove_response = client.delete(f"/activities/{activity}/participant?email={email}")
        
        # Act - Sign up again
        resend_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert signup_response.status_code == 200
        assert remove_response.status_code == 200
        assert resend_response.status_code == 200

    def test_multiple_students_signup_and_partial_removal(self, client):
        """Should handle multiple signups and remove only specified students"""
        # Arrange
        activity = "Gym Class"
        emails = ["s1@mergington.edu", "s2@mergington.edu", "s3@mergington.edu"]
        
        # Act - Sign everyone up
        for email in emails:
            client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Remove middle student
        client.delete(f"/activities/{activity}/participant?email={emails[1]}")
        
        # Act - Get updated activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert emails[0] in data[activity]["participants"]
        assert emails[1] not in data[activity]["participants"]
        assert emails[2] in data[activity]["participants"]

    def test_full_activity_lifecycle(self, client):
        """Should handle complete lifecycle: signup, verify, remove, re-signup"""
        # Arrange
        activity = "Chess Club"
        email = "lifecycle@mergington.edu"
        
        # Act - Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        signup_data = response.json()
        
        # Act - Remove
        client.delete(f"/activities/{activity}/participant?email={email}")
        response = client.get("/activities")
        remove_data = response.json()
        
        # Act - Sign up again
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        final_data = response.json()
        
        # Assert
        assert email in signup_data[activity]["participants"]
        assert email not in remove_data[activity]["participants"]
        assert email in final_data[activity]["participants"]
