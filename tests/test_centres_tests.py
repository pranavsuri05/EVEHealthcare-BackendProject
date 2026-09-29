import pytest


def test_create_centre(test_client):
    """Test creating a diagnostic centre"""
    response = test_client.post(
        "/centres",
        json={"name": "City Hospital", "location": "Downtown"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "City Hospital"
    assert response.json()["location"] == "Downtown"


def test_list_centres(test_client):
    """Test listing centres with pagination"""
    test_client.post("/centres", json={"name": "Centre 1", "location": "Loc 1"})
    test_client.post("/centres", json={"name": "Centre 2", "location": "Loc 2"})

    response = test_client.get("/centres?skip=0&limit=10")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_get_centre(test_client):
    """Test retrieving a specific centre"""
    create_response = test_client.post(
        "/centres", json={"name": "Test Centre", "location": "Test Location"}
    )
    centre_id = create_response.json()["id"]

    response = test_client.get(f"/centres/{centre_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Centre"


def test_get_nonexistent_centre(test_client):
    """Test retrieving non-existent centre"""
    response = test_client.get("/centres/9999")
    assert response.status_code == 404


def test_create_diagnostic_test(test_client):
    """Test creating a diagnostic test"""
    response = test_client.post(
        "/tests",
        json={"name": "Blood Test", "description": "Complete blood count"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Blood Test"


def test_create_duplicate_test(test_client):
    """Test creating duplicate test name"""
    test_client.post(
        "/tests", json={"name": "Unique Test", "description": "First"}
    )

    response = test_client.post(
        "/tests", json={"name": "Unique Test", "description": "Second"}
    )
    assert response.status_code == 409


def test_list_tests(test_client):
    """Test listing tests with pagination"""
    test_client.post("/tests", json={"name": "Test 1"})
    test_client.post("/tests", json={"name": "Test 2"})

    response = test_client.get("/tests?skip=0&limit=10")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_test(test_client):
    """Test retrieving a specific test"""
    create_response = test_client.post(
        "/tests", json={"name": "CBC Test"}
    )
    test_id = create_response.json()["id"]

    response = test_client.get(f"/tests/{test_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "CBC Test"


def test_add_test_to_centre(test_client):
    """Test adding a test to a centre with pricing"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post(
        "/tests", json={"name": "Test 1"}
    )
    test_id = test_response.json()["id"]

    response = test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": 500.0},
    )
    assert response.status_code == 201
    assert response.json()["price"] == 500.0
    assert response.json()["available"] is True


def test_add_duplicate_test_to_centre(test_client):
    """Test adding same test twice to same centre"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post("/tests", json={"name": "Test 1"})
    test_id = test_response.json()["id"]

    test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": 500.0},
    )

    response = test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": 600.0},
    )
    assert response.status_code == 409


def test_add_test_invalid_price(test_client):
    """Test adding test with invalid price"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post("/tests", json={"name": "Test 1"})
    test_id = test_response.json()["id"]

    response = test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": -100},
    )
    assert response.status_code == 422


def test_add_test_nonexistent_centre(test_client):
    """Test adding test to non-existent centre"""
    test_response = test_client.post("/tests", json={"name": "Test 1"})
    test_id = test_response.json()["id"]

    response = test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": 9999, "test_id": test_id, "price": 500},
    )
    assert response.status_code == 404


def test_list_centre_tests(test_client):
    """Test listing tests offered by a centre"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post("/tests", json={"name": "Test 1"})
    test_id = test_response.json()["id"]

    test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": 500},
    )

    response = test_client.get(f"/tests/centre/{centre_id}/tests")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
