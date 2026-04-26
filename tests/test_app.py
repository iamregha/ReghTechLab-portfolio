"""
ReghTechLab — Test Suite
=========================
Run with: pytest tests/ -v
"""
import pytest
from portfolio import create_app
from portfolio.extensions import db
from portfolio.models import User, Post

app = create_app("testing")

# ── Fixture ───────────────────────────────────────────────
# A fixture is setup code that runs before each test.

@pytest.fixture
def client():
    # Config is handled by TestingConfig in config.py
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def logged_in_client(client):
    """
    A client that is already registered and logged in.
    Used for tests that need an authenticated user.
    """
    client.post("/register", data={
        "username":         "testuser",
        "email":            "test@reghtechlab.com",
        "password":         "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    return client


# ── Public page tests ─────────────────────────────────────
# These verify your public-facing pages always load.
# If any of these fail after a code change —
# something fundamental broke.

def test_homepage_loads(client):
    """Homepage must return 200."""
    res = client.get("/")
    assert res.status_code == 200


def test_blog_index_loads(client):
    """Blog index must return 200."""
    res = client.get("/blog")
    assert res.status_code == 200


def test_login_page_loads(client):
    """Login page must return 200."""
    res = client.get("/login")
    assert res.status_code == 200


def test_register_page_loads(client):
    """Register page must return 200."""
    res = client.get("/register")
    assert res.status_code == 200


# ── Auth tests ────────────────────────────────────────────

def test_user_can_register(client):
    """A new user registers and lands on homepage."""
    res = client.post("/register", data={
        "username":         "abraham",
        "email":            "abraham@reghtechlab.com",
        "password":         "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"abraham" in res.data


def test_register_rejects_short_password(client):
    """Password under 8 characters must be rejected."""
    res = client.post("/register", data={
        "username":         "testuser",
        "email":            "test@example.com",
        "password":         "short",
        "confirm_password": "short",
    }, follow_redirects=True)
    assert b"8 characters" in res.data


def test_register_rejects_mismatched_passwords(client):
    """Mismatched passwords must be rejected."""
    res = client.post("/register", data={
        "username":         "testuser",
        "email":            "test@example.com",
        "password":         "password123",
        "confirm_password": "different456",
    }, follow_redirects=True)
    assert b"match" in res.data


def test_register_rejects_duplicate_username(client):
    """Two users cannot share the same username."""
    # First registration
    client.post("/register", data={
        "username":         "sameuser",
        "email":            "first@example.com",
        "password":         "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)

    # Log out before attempting to register again
    client.get("/logout", follow_redirects=True)

    # Second registration with the same username, different email
    res = client.post("/register", data={
        "username":         "sameuser",
        "email":            "second@example.com",
        "password":         "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert b"taken" in res.data
    


def test_user_can_login(client):
    """A registered user can log in."""
    client.post("/register", data={
        "username":         "logintest",
        "email":            "login@example.com",
        "password":         "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)

    client.get("/logout", follow_redirects=True)

    res = client.post("/login", data={
        "identifier": "logintest",
        "password":   "password123",
    }, follow_redirects=True)
    assert b"logintest" in res.data


def test_login_rejects_wrong_password(client):
    """Wrong password must be rejected."""
    client.post("/register", data={
        "username":         "wrongpass",
        "email":            "wrong@example.com",
        "password":         "correctpass123",
        "confirm_password": "correctpass123",
    }, follow_redirects=True)

    client.get("/logout")

    res = client.post("/login", data={
        "identifier": "wrongpass",
        "password":   "wrongpassword",
    }, follow_redirects=True)
    assert b"Invalid" in res.data


# ── Access control tests ──────────────────────────────────
# These verify your @login_required decorators work.
# An unauthenticated user hitting a protected route
# must be redirected to login — never shown the page,
# never shown a 500 error.

def test_new_post_requires_login(client):
    """Unauthenticated user redirected from /blog/new."""
    res = client.get("/blog/new")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_logout_requires_login(client):
    """Unauthenticated user cannot hit /logout directly."""
    res = client.get("/logout")
    assert res.status_code == 302


# ── Blog tests ────────────────────────────────────────────

def test_nonexistent_post_returns_404(client):
    """A slug that does not exist must return 404."""
    res = client.get("/blog/this-post-does-not-exist")
    assert res.status_code == 404


def test_authenticated_user_can_create_post(logged_in_client):
    """A logged in user can publish a post."""
    res = logged_in_client.post("/blog/new", data={
        "title":     "Why Fuel Station Reporting Fails",
        "excerpt":   "A look at the reporting gap in downstream retail.",
        "content":   "Manual reporting is the silent killer of operational intelligence in retail fuel networks. " * 5,
        "category":  "Retail Operations",
        "published": "on",
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Why Fuel Station Reporting Fails" in res.data


def test_post_slug_is_generated_from_title(logged_in_client):
    """A post slug must be derived from the title."""
    logged_in_client.post("/blog/new", data={
        "title":     "Slug Generation Test Post",
        "excerpt":   "Testing slug generation works correctly.",
        "content":   "This is a test of the slug generation system in ReghTechLab. " * 5,
        "category":  "Tutorials",
        "published": "on",
    }, follow_redirects=True)

    with app.app_context():
        post = db.session.execute(
            db.select(Post).filter_by(
                slug="slug-generation-test-post"
            )
        ).scalar_one_or_none()
        assert post is not None


def test_user_can_comment_on_post(logged_in_client):
    """A logged in user can comment on a post."""
    logged_in_client.post("/blog/new", data={
        "title":     "Post for Comment Test",
        "excerpt":   "Testing comment functionality.",
        "content":   "This post exists solely to test commenting. " * 5,
        "category":  "Tutorials",
        "published": "on",
    }, follow_redirects=True)

    res = logged_in_client.post(
        "/blog/post-for-comment-test",
        data={"content": "Great post, very insightful!"},
        follow_redirects=True
    )
    assert res.status_code == 200
    assert b"Great post" in res.data