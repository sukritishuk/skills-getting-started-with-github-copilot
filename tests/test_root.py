"""
Tests for the root endpoint (GET /).
"""
import pytest


def test_root_redirect(client):
    """Test that GET / redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    
    # Check for redirect status code (307 Temporary Redirect)
    assert response.status_code == 307
    
    # Check that Location header points to /static/index.html
    assert response.headers["location"] == "/static/index.html"


def test_root_redirect_follow(client):
    """Test following the redirect from GET /"""
    response = client.get("/", follow_redirects=True)
    
    # After following redirect, should get 200 (though /static/ files may not exist in test)
    # We're mainly testing that the redirect works
    assert response.status_code in [200, 404]  # 404 is OK if static files aren't available in test
