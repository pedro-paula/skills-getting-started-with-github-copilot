"""
Tests for the FastAPI application endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test cases for the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities list contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Basketball",
            "Soccer",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Science Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"

    def test_activity_participants_is_list(self):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test cases for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_returns_200(self):
        """Test successful signup returns 200"""
        response = client.post(
            "/activities/Basketball/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_new_participant_returns_message(self):
        """Test successful signup returns confirmation message"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant_to_list(self):
        """Test that signup actually adds participant to the activity"""
        # Get initial participant count
        response_initial = client.get("/activities")
        initial_count = len(response_initial.json()["Soccer"]["participants"])
        
        # Sign up new participant
        new_email = "testparticipant@mergington.edu"
        response = client.post(
            f"/activities/Soccer/signup?email={new_email}"
        )
        
        # Verify participant was added
        response_after = client.get("/activities")
        final_count = len(response_after.json()["Soccer"]["participants"])
        assert final_count == initial_count + 1
        assert new_email in response_after.json()["Soccer"]["participants"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with duplicate email returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup
        client.post(f"/activities/Art Club/signup?email={email}")
        
        # Duplicate signup
        response = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_invalid_email_format(self):
        """Test signup with invalid email format (should still work as it just stores the string)"""
        response = client.post(
            "/activities/Chess Club/signup?email=invalidemail"
        )
        assert response.status_code == 200
        # The endpoint doesn't validate email format, just stores it


class TestUnregisterEndpoint:
    """Test cases for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_returns_200(self):
        """Test unregistering an existing participant returns 200"""
        email = "testunreg@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Drama Club/unregister?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_returns_message(self):
        """Test unregister returns confirmation message"""
        email = "unregmsg@mergington.edu"
        
        client.post(f"/activities/Debate Team/signup?email={email}")
        
        response = client.delete(
            f"/activities/Debate Team/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Debate Team" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removetest@mergington.edu"
        activity_name = "Science Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify participant is there
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_400(self):
        """Test unregistering a participant who isn't signed up returns 400"""
        response = client.delete(
            "/activities/Programming Class/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregistering from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Fake Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootEndpoint:
    """Test cases for the root endpoint"""

    def test_root_redirects_to_static_html(self):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
