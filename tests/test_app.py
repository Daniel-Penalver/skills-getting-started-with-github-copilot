from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    test_client = TestClient(app, follow_redirects=False)
    yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = activities["Chess Club"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email"),
    [
        ("Nonexistent Club", "student@mergington.edu"),
        ("Chess Club", "michael@mergington.edu"),
    ],
)
def test_signup_rejects_missing_activity_or_duplicate_participant(
    client, activity_name, email
):
    # Arrange
    expected_status = 404 if activity_name == "Nonexistent Club" else 400
    expected_detail = (
        "Activity not found"
        if expected_status == 404
        else "Student is already signed up"
    )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Nonexistent Club", "student@mergington.edu", "Activity not found"),
        ("Chess Club", "student@mergington.edu", "Participant not found"),
    ],
)
def test_unregister_rejects_missing_activity_or_participant(
    client, activity_name, email, expected_detail
):
    # Arrange
    expected_status = 404

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail
