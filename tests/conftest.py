import os
import sys
import tempfile
import pytest
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def temp_cache_dir():
    """Provides a temporary directory for cache testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_app_config():
    """Provides a mock app_config for testing"""
    from src.config import AppConfig

    config = AppConfig(
        cache_base_dir="test_cache",
        douban_api_request_delay_max_seconds=0.1,
        list_cache_ttl_seconds=3600,
        imdb_request_delay_max_seconds=0.1,
        imdb_cache_ttl_id_not_found_seconds=3600,
        douban_rate_limit_delay_seconds=60,
        bootstrap_interval_seconds=3600,
        bootstrap_list_interval_seconds=10,
        bootstrap_lists_max=10,
        sync_imdb_cache_interval_seconds=3600,
        sync_imdb_cache_to=[],
    )
    return config


@pytest.fixture
def mock_douban_item():
    """Provides a mock Douban item for testing"""
    return {
        "title": "The Shawshank Redemption",
        "url": "https://movie.douban.com/subject/1292052/",
        "type": "movie",
        "rating": {"value": 9.7},
    }


@pytest.fixture
def mock_http_response():
    """Factory fixture for creating mock HTTP responses"""

    def _create_response(status_code=200, json_data=None, text="", headers=None):
        response = Mock()
        response.status_code = status_code
        response.json = Mock(return_value=json_data or {})
        response.text = text
        response.headers = headers or {}
        response.url = Mock()
        response.url.host = "test.example.com"
        return response

    return _create_response
