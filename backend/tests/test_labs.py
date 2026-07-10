import pytest
from app.models.lab import Lab


@pytest.fixture(name="seed_test_labs")
def seed_test_labs_fixture(db):
    """
    Seed a set of mock labs specifically for unit testing in the SQLite test database.
    """
    labs = [
        Lab(
            title="Introduction to Bash",
            slug="intro-to-bash",
            description="Learn core bash command structures.",
            difficulty="Beginner",
            duration="30m",
            category="Linux",
            icon="terminal",
            estimated_time="30m",
            status="Active",
            coming_soon=True,
        ),
        Lab(
            title="Advanced Docker Containers",
            slug="advanced-docker-containers",
            description="Optimize multi-container operations.",
            difficulty="Advanced",
            duration="60m",
            category="Docker",
            icon="box",
            estimated_time="60m",
            status="Active",
            coming_soon=True,
        ),
        Lab(
            title="Terraform Basics",
            slug="terraform-basics",
            description="Write declarative cloud blueprints.",
            difficulty="Beginner",
            duration="45m",
            category="Terraform",
            icon="cpu",
            estimated_time="45m",
            status="Active",
            coming_soon=True,
        ),
    ]
    for lab in labs:
        db.add(lab)
    db.commit()
    return labs


def test_get_labs_all(client, seed_test_labs):
    response = client.get("/api/v1/labs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["labs"]) == 3
    assert data["labs"][0]["title"] in [lab.title for lab in seed_test_labs]


def test_get_labs_categories(client, seed_test_labs):
    response = client.get("/api/v1/labs/categories")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 3
    assert "Linux" in categories
    assert "Docker" in categories
    assert "Terraform" in categories


def test_get_lab_by_slug_success(client, seed_test_labs):
    response = client.get("/api/v1/labs/intro-to-bash")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "intro-to-bash"
    assert data["title"] == "Introduction to Bash"
    assert data["difficulty"] == "Beginner"


def test_get_lab_by_slug_not_found(client, seed_test_labs):
    response = client.get("/api/v1/labs/nonexistent-lab")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_labs_search(client, seed_test_labs):
    # Search for "Docker"
    response = client.get("/api/v1/labs?search=Docker")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["labs"][0]["slug"] == "advanced-docker-containers"


def test_get_labs_filter_difficulty(client, seed_test_labs):
    # Filter by "Beginner"
    response = client.get("/api/v1/labs?difficulty=Beginner")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    slugs = [lab["slug"] for lab in data["labs"]]
    assert "intro-to-bash" in slugs
    assert "terraform-basics" in slugs
    assert "advanced-docker-containers" not in slugs


def test_get_labs_filter_category(client, seed_test_labs):
    # Filter by "Linux"
    response = client.get("/api/v1/labs?category=Linux")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["labs"][0]["slug"] == "intro-to-bash"
