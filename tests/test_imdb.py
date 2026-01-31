import pytest
import httpx
from unittest.mock import Mock, patch

# Import from src package
from src.imdb import (
    ImdbApi,
    DoubanHtmlImdbApi,
    DoubanIDatabaseImdbApi,
    get_imdb_api,
)


class TestImdbApiBase:
    """Test suite for base ImdbApi class"""

    @pytest.fixture
    def mock_imdb_api(self, temp_cache_dir, monkeypatch):
        """Provides a mock implementation of ImdbApi"""

        class MockImdbApi(ImdbApi):
            async def fetch_imdb_id(self, douban_id: str, douban_item):
                return "tt1234567"

        # Use monkeypatch to temporarily override config values
        from src import config

        monkeypatch.setattr(config.app_config, "cache_base_dir", temp_cache_dir)
        monkeypatch.setattr(
            config.app_config, "imdb_cache_ttl_id_not_found_seconds", 3600
        )

        api = MockImdbApi()
        yield api
        api.cache.close()

    @pytest.mark.asyncio
    async def test_get_imdb_id_not_cached(self, mock_imdb_api, mock_douban_item):
        """Test fetching IMDb ID when not in cache"""
        result = await mock_imdb_api.get_imdb_id("1292052", mock_douban_item)

        assert result == "tt1234567"
        # Check it's cached
        assert mock_imdb_api.cache.get("1292052") == "tt1234567"

    @pytest.mark.asyncio
    async def test_get_imdb_id_cached(self, mock_imdb_api, mock_douban_item):
        """Test returning IMDb ID from cache"""
        # Pre-populate cache
        mock_imdb_api.cache.set("1292052", "tt7654321")

        result = await mock_imdb_api.get_imdb_id("1292052", mock_douban_item)

        # Should return cached value, not fetch new one
        assert result == "tt7654321"

    @pytest.mark.asyncio
    async def test_get_imdb_id_not_found_cached_with_ttl(
        self, temp_cache_dir, mock_douban_item, monkeypatch
    ):
        """Test that not-found results are cached with TTL"""

        class NotFoundApi(ImdbApi):
            async def fetch_imdb_id(self, douban_id: str, douban_item):
                return None

        from src import config

        monkeypatch.setattr(config.app_config, "cache_base_dir", temp_cache_dir)
        monkeypatch.setattr(
            config.app_config, "imdb_cache_ttl_id_not_found_seconds", 100
        )

        api = NotFoundApi()

        result = await api.get_imdb_id("9999999", mock_douban_item)

        assert result is None
        # Check it's cached with TTL
        cached_value, expire_time = api.get_cache().get("9999999", expire_time=True)
        assert cached_value is None
        assert expire_time is not None
        api.cache.close()


class TestDoubanHtmlImdbApi:
    """Test suite for DoubanHtmlImdbApi"""

    @pytest.fixture
    def html_api(self, temp_cache_dir, monkeypatch):
        """Provides DoubanHtmlImdbApi instance"""
        from src import config

        monkeypatch.setattr(config.app_config, "cache_base_dir", temp_cache_dir)
        monkeypatch.setattr(config.app_config, "imdb_request_delay_max_seconds", 0)
        monkeypatch.setattr(
            config.app_config, "imdb_cache_ttl_id_not_found_seconds", 3600
        )

        api = DoubanHtmlImdbApi()
        yield api
        api.cache.close()
        # api.client.close() # Skip closing async client

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_found(self, html_api, mock_douban_item):
        """Test successful IMDb ID extraction from HTML"""
        html_content = """
        <html>
            <div>IMDb: https://www.imdb.com/title/tt0111161/</div>
        </html>
        """

        with patch("src.imdb.get_response") as mock_get_response:
            mock_response = Mock()
            mock_response.text = html_content
            mock_get_response.return_value = mock_response

            result = await html_api.fetch_imdb_id("1292052", mock_douban_item)

            assert result == "tt0111161"
            mock_get_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_not_found(self, html_api, mock_douban_item):
        """Test when IMDb ID is not in HTML"""
        html_content = """
        <html>
            <div>No IMDb link here</div>
        </html>
        """

        with patch("src.imdb.get_response") as mock_get_response:
            mock_response = Mock()
            mock_response.text = html_content
            mock_get_response.return_value = mock_response

            result = await html_api.fetch_imdb_id("1292052", mock_douban_item)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_with_delay(self, html_api, mock_douban_item):
        """Test that random delay is applied"""
        with patch("src.imdb.get_response") as mock_get_response:
            with patch("src.imdb.asyncio.sleep") as mock_sleep:
                mock_response = Mock()
                mock_response.text = "IMDb: tt1234567"
                mock_get_response.return_value = mock_response

                await html_api.fetch_imdb_id("1292052", mock_douban_item)

                # Verify sleep was called
                mock_sleep.assert_called_once()


class TestDoubanIDatabaseImdbApi:
    """Test suite for DoubanIDatabaseImdbApi"""

    @pytest.fixture
    def database_api(self, temp_cache_dir, monkeypatch):
        """Provides DoubanIDatabaseImdbApi instance"""
        from src import config

        monkeypatch.setattr(config.app_config, "cache_base_dir", temp_cache_dir)
        monkeypatch.setattr(
            config.app_config, "douban_idatabase_url", "http://test-db:8000"
        )
        monkeypatch.setattr(config.app_config, "douban_idatabase_api_key", None)
        monkeypatch.setattr(config.app_config, "douban_idatabase_timeout_seconds", 10)
        monkeypatch.setattr(
            config.app_config, "imdb_cache_ttl_id_not_found_seconds", 3600
        )

        api = DoubanIDatabaseImdbApi()
        yield api
        api.cache.close()
        # api.client.close() # Skip closing async client

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_found(self, database_api, mock_douban_item):
        """Test successful IMDb ID fetch from douban-idatabase"""
        api_response = [
            {
                "douban_id": "1292052",
                "imdb_id": "tt0111161",
                "douban_title": "The Shawshank Redemption",
                "year": 1994,
                "rating": 9.7,
            }
        ]

        with patch("src.imdb.get_response") as mock_get_response:
            mock_response = Mock()
            mock_response.json = Mock(return_value=api_response)
            mock_get_response.return_value = mock_response

            result = await database_api.fetch_imdb_id("1292052", mock_douban_item)

            assert result == "tt0111161"
            mock_get_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_404_not_found(self, database_api, mock_douban_item):
        """Test handling of 404 response"""
        with patch("src.imdb.get_response") as mock_get_response:
            error = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=Mock(status_code=404)
            )
            mock_get_response.side_effect = error

            result = await database_api.fetch_imdb_id("9999999", mock_douban_item)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_empty_response(self, database_api, mock_douban_item):
        """Test handling of empty API response"""
        with patch("src.imdb.get_response") as mock_get_response:
            mock_response = Mock()
            mock_response.json = Mock(return_value=[])
            mock_get_response.return_value = mock_response

            result = await database_api.fetch_imdb_id("1292052", mock_douban_item)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_no_imdb_id_in_response(
        self, database_api, mock_douban_item
    ):
        """Test handling when item exists but has no IMDb ID"""
        api_response = [
            {
                "douban_id": "1292052",
                "imdb_id": None,
                "douban_title": "The Shawshank Redemption",
                "year": 1994,
                "rating": 9.7,
            }
        ]

        with patch("src.imdb.get_response") as mock_get_response:
            mock_response = Mock()
            mock_response.json = Mock(return_value=api_response)
            mock_get_response.return_value = mock_response

            result = await database_api.fetch_imdb_id("1292052", mock_douban_item)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_imdb_id_server_error_propagates(
        self, database_api, mock_douban_item
    ):
        """Test that 500 errors are propagated"""
        with patch("src.imdb.get_response") as mock_get_response:
            error = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=Mock(status_code=500)
            )
            mock_get_response.side_effect = error

            with pytest.raises(httpx.HTTPStatusError):
                await database_api.fetch_imdb_id("1292052", mock_douban_item)

    @pytest.mark.asyncio
    async def test_api_key_included_in_headers(
        self, temp_cache_dir, mock_douban_item, monkeypatch
    ):
        """Test that API key is included in request headers when configured"""
        from src import config

        monkeypatch.setattr(config.app_config, "cache_base_dir", temp_cache_dir)
        monkeypatch.setattr(
            config.app_config, "douban_idatabase_url", "http://test-db:8000"
        )
        monkeypatch.setattr(
            config.app_config, "douban_idatabase_api_key", "test-api-key-123"
        )
        monkeypatch.setattr(config.app_config, "douban_idatabase_timeout_seconds", 10)
        monkeypatch.setattr(
            config.app_config, "imdb_cache_ttl_id_not_found_seconds", 3600
        )

        api = DoubanIDatabaseImdbApi()

        assert api.client.headers.get("X-API-Key") == "test-api-key-123"

        api.cache.close()
        # api.client.close() # Skip closing async client

    @pytest.mark.asyncio
    async def test_base_url_configured(self, database_api):
        """Test that base URL is properly configured"""
        assert str(database_api.client.base_url) == "http://test-db:8000"

    @pytest.mark.asyncio
    async def test_timeout_configured(self, database_api):
        """Test that timeout is properly configured"""
        assert database_api.client.timeout.read == 10


class TestGetImdbApi:
    """Test suite for get_imdb_api factory function"""

    def test_returns_database_api_when_url_configured(self, monkeypatch):
        """Test that DoubanIDatabaseImdbApi is returned when URL is configured"""
        from src import config

        monkeypatch.setattr(
            config.app_config, "douban_idatabase_url", "http://test-db:8000"
        )
        monkeypatch.setattr(config.app_config, "douban_idatabase_api_key", None)
        monkeypatch.setattr(config.app_config, "douban_idatabase_timeout_seconds", 10)

        api = get_imdb_api()

        assert isinstance(api, DoubanIDatabaseImdbApi)
        api.cache.close()
        # api.client.close() # Skip closing async client

    def test_returns_html_api_when_url_not_configured(self, monkeypatch):
        """Test that DoubanHtmlImdbApi is returned when URL is not configured"""
        from src import config

        monkeypatch.setattr(config.app_config, "douban_idatabase_url", None)

        api = get_imdb_api()

        assert isinstance(api, DoubanHtmlImdbApi)
        api.cache.close()
        # api.client.close() # Skip closing async client

    def test_returns_html_api_when_url_empty_string(self, monkeypatch):
        """Test that DoubanHtmlImdbApi is returned when URL is empty string"""
        from src import config

        monkeypatch.setattr(config.app_config, "douban_idatabase_url", "")

        api = get_imdb_api()

        assert isinstance(api, DoubanHtmlImdbApi)
        api.cache.close()
        # api.client.close() # Skip closing async client
