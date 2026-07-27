"""
Integration tests for the Mergington High School Activities API
Tests complete user workflows and multi-endpoint interactions
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestCompleteUserWorkflows:
    """Integration tests for complete user workflows"""
    
    def test_full_signup_and_unregister_workflow(self):
        """Test complete workflow: view activities, signup, then unregister"""
        email = "workflow@mergington.edu"
        activity_name = "Chess Club"
        
        # Step 1: Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        initial_count = len(activities[activity_name]["participants"])
        
        # Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Step 3: Verify signup
        response = client.get("/activities")
        assert len(response.json()[activity_name]["participants"]) == initial_count + 1
        
        # Step 4: Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Step 5: Verify unregister
        response = client.get("/activities")
        assert len(response.json()[activity_name]["participants"]) == initial_count
    
    def test_multiple_students_signup_same_activity(self):
        """Test multiple students signing up for the same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        activity_name = "Programming Class"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students are registered
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert len(participants) == initial_count + len(emails)
        for email in emails:
            assert email in participants
    
    def test_student_signup_multiple_activities(self):
        """Test one student signing up for multiple activities"""
        email = "multiactivity@mergington.edu"
        activities = ["Chess Club", "Programming Class", "Drama Club"]
        
        # Sign up for multiple activities
        for activity in activities:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify signup in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities:
            assert email in data[activity]["participants"]
    
    def test_signup_unregister_chain(self):
        """Test signing up and unregistering multiple times"""
        email = "chain@mergington.edu"
        activity_name = "Art Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response2.status_code == 200
        
        # Sign up again (should work)
        response3 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response3.status_code == 200
        
        # Verify final state
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]


class TestParticipantCountTracking:
    """Integration tests for accurate participant count tracking"""
    
    def test_participant_count_updates_on_signup(self):
        """Test that participant count increases on signup"""
        email = "counttest1@mergington.edu"
        activity_name = "Volleyball Club"
        
        # Get initial count
        before = client.get("/activities").json()[activity_name]["participants"]
        initial_count = len(before)
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Check count increased
        after = client.get("/activities").json()[activity_name]["participants"]
        assert len(after) == initial_count + 1
    
    def test_participant_count_updates_on_unregister(self):
        """Test that participant count decreases on unregister"""
        email = "counttest2@mergington.edu"
        activity_name = "Soccer Team"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        before = client.get("/activities").json()[activity_name]["participants"]
        count_after_signup = len(before)
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        after = client.get("/activities").json()[activity_name]["participants"]
        count_after_unregister = len(after)
        
        assert count_after_unregister == count_after_signup - 1
    
    def test_availability_reflects_changes(self):
        """Test that available spots calculation reflects signups/unregisters"""
        email = "availability@mergington.edu"
        activity_name = "Math Olympiad"
        
        response = client.get("/activities")
        data = response.json()[activity_name]
        initial_available = data["max_participants"] - len(data["participants"])
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()[activity_name]
        available_after_signup = data["max_participants"] - len(data["participants"])
        
        assert available_after_signup == initial_available - 1
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()[activity_name]
        available_after_unregister = data["max_participants"] - len(data["participants"])
        
        assert available_after_unregister == initial_available


class TestErrorHandlingIntegration:
    """Integration tests for error handling across workflows"""
    
    def test_cannot_signup_then_duplicate_signup_then_unregister(self):
        """Test complete error scenario with duplicate attempt"""
        email = "errortest@mergington.edu"
        activity_name = "Debate Team"
        
        # Valid signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Duplicate signup attempt (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response2.status_code == 400
        
        # But unregister should still work
        response3 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response3.status_code == 200
    
    def test_unregister_after_failed_signup(self):
        """Test that unregister fails if signup never succeeded"""
        email = "neverregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_double_unregister_fails(self):
        """Test that unregistering twice fails"""
        email = "doubleunreg@mergington.edu"
        activity_name = "Programming Class"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # First unregister
        response1 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Second unregister (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response2.status_code == 400


class TestDataIntegrity:
    """Integration tests for data integrity across operations"""
    
    def test_email_format_preserved(self):
        """Test that email format is preserved throughout operations"""
        email = "complex.email.tag@mergington.edu"
        activity_name = "Drama Club"
        
        # Sign up
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify email is exactly as stored
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email in participants
        
        # Unregister and verify
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email not in participants
    
    def test_activity_structure_preserved(self):
        """Test that activity structure remains consistent"""
        activity_name = "Art Club"
        
        response = client.get("/activities")
        initial_activity = response.json()[activity_name]
        
        # Perform operations
        client.post(f"/activities/{activity_name}/signup?email=test1@mergington.edu")
        client.post(f"/activities/{activity_name}/signup?email=test2@mergington.edu")
        client.post(f"/activities/{activity_name}/unregister?email=test1@mergington.edu")
        
        # Verify structure is preserved
        response = client.get("/activities")
        final_activity = response.json()[activity_name]
        
        assert "description" in final_activity
        assert "schedule" in final_activity
        assert "max_participants" in final_activity
        assert "participants" in final_activity
        assert final_activity["description"] == initial_activity["description"]
        assert final_activity["schedule"] == initial_activity["schedule"]
        assert final_activity["max_participants"] == initial_activity["max_participants"]
    
    def test_other_activities_unaffected_by_operations(self):
        """Test that operations on one activity don't affect others"""
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        email = "isolation@mergington.edu"
        
        # Get initial state of both
        response = client.get("/activities")
        activity1_before = response.json()[activity1]["participants"].copy()
        activity2_before = response.json()[activity2]["participants"].copy()
        
        # Operate on activity1
        client.post(f"/activities/{activity1}/signup?email={email}")
        
        # Verify activity2 is unchanged
        response = client.get("/activities")
        assert response.json()[activity2]["participants"] == activity2_before
