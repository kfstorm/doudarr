import os
from unittest.mock import patch
from src.config import AppConfig, ENV_PREFIX


class TestAppConfig:
    """Test suite for AppConfig"""

    def test_default_values(self):
        """Test that default configuration values are correct"""
        config = AppConfig()

        assert config.cache_base_dir == "cache"
        assert config.douban_api_request_delay_max_seconds == 1
        assert config.list_cache_ttl_seconds == 86400
        assert config.imdb_request_delay_max_seconds == 30
        assert config.imdb_cache_ttl_id_not_found_seconds == 86400
        assert config.proxy_address is None
        assert config.bootstrap_interval_seconds == 86400
        assert config.bootstrap_list_interval_seconds == 30
        assert config.bootstrap_lists_max == 100
        assert config.douban_rate_limit_delay_seconds == 3600
        assert config.apikey is None
        assert config.sync_imdb_cache_interval_seconds == 3600
        assert config.sync_imdb_cache_to == []
        assert config.cookie_douban_com_dbcl2 is None

    def test_douban_idatabase_default_values(self):
        """Test douban-idatabase integration default values"""
        config = AppConfig()

        assert config.douban_idatabase_url is None
        assert config.douban_idatabase_api_key is None
        assert config.douban_idatabase_timeout_seconds == 10

    def test_env_prefix(self):
        """Test that ENV_PREFIX is correct"""
        assert ENV_PREFIX == "DOUDARR_"

    def test_config_from_environment(self):
        """Test loading configuration from environment variables"""
        env_vars = {
            "DOUDARR_CACHE_BASE_DIR": "/custom/cache",
            "DOUDARR_DOUBAN_API_REQUEST_DELAY_MAX_SECONDS": "2.5",
            "DOUDARR_LIST_CACHE_TTL_SECONDS": "7200",
            "DOUDARR_IMDB_REQUEST_DELAY_MAX_SECONDS": "60",
            "DOUDARR_PROXY_ADDRESS": "http://proxy.example.com:8080",
            "DOUDARR_APIKEY": "test-api-key",
            "DOUDARR_DOUBAN_IDATABASE_URL": "http://db-api:8000",
            "DOUDARR_DOUBAN_IDATABASE_API_KEY": "db-api-key",
            "DOUDARR_DOUBAN_IDATABASE_TIMEOUT_SECONDS": "15",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = AppConfig(_env_prefix=ENV_PREFIX)

            assert config.cache_base_dir == "/custom/cache"
            assert config.douban_api_request_delay_max_seconds == 2.5
            assert config.list_cache_ttl_seconds == 7200
            assert config.imdb_request_delay_max_seconds == 60
            assert config.proxy_address == "http://proxy.example.com:8080"
            assert config.apikey == "test-api-key"
            assert config.douban_idatabase_url == "http://db-api:8000"
            assert config.douban_idatabase_api_key == "db-api-key"
            assert config.douban_idatabase_timeout_seconds == 15

    def test_sync_imdb_cache_to_list(self):
        """Test loading sync_imdb_cache_to list from environment"""
        import json

        urls = [
            "http://doudarr-1:8000/sync?apikey=key1",
            "http://doudarr-2:8000/sync?apikey=key2",
        ]
        env_vars = {"DOUDARR_SYNC_IMDB_CACHE_TO": json.dumps(urls)}

        with patch.dict(os.environ, env_vars, clear=False):
            config = AppConfig(_env_prefix=ENV_PREFIX)

            assert config.sync_imdb_cache_to == urls

    def test_numeric_fields_type(self):
        """Test that numeric fields have correct types"""
        config = AppConfig()

        assert isinstance(config.douban_api_request_delay_max_seconds, float)
        assert isinstance(config.list_cache_ttl_seconds, float)
        assert isinstance(config.imdb_request_delay_max_seconds, float)
        assert isinstance(config.imdb_cache_ttl_id_not_found_seconds, float)
        assert isinstance(config.bootstrap_interval_seconds, float)
        assert isinstance(config.bootstrap_list_interval_seconds, float)
        assert isinstance(config.bootstrap_lists_max, int)
        assert isinstance(config.douban_rate_limit_delay_seconds, float)
        assert isinstance(config.sync_imdb_cache_interval_seconds, float)
        assert isinstance(config.douban_idatabase_timeout_seconds, float)

    def test_optional_fields_can_be_none(self):
        """Test that optional fields can be None"""
        config = AppConfig()

        # These should all be None by default
        assert config.proxy_address is None
        assert config.apikey is None
        assert config.cookie_douban_com_dbcl2 is None
        assert config.douban_idatabase_url is None
        assert config.douban_idatabase_api_key is None

    def test_douban_idatabase_url_empty_string(self):
        """Test that empty string for douban_idatabase_url works"""
        env_vars = {"DOUDARR_DOUBAN_IDATABASE_URL": ""}

        with patch.dict(os.environ, env_vars, clear=False):
            config = AppConfig(_env_prefix=ENV_PREFIX)

            # Empty string should be treated as not configured
            assert (
                config.douban_idatabase_url == "" or config.douban_idatabase_url is None
            )

    def test_field_descriptions_exist(self):
        """Test that all fields have descriptions"""
        schema = AppConfig.model_json_schema()

        for field_name, field_info in schema["properties"].items():
            assert (
                "description" in field_info
            ), f"Field {field_name} missing description"
            assert (
                len(field_info["description"]) > 0
            ), f"Field {field_name} has empty description"

    def test_douban_idatabase_field_descriptions_in_chinese(self):
        """Test that douban-idatabase field descriptions are in Chinese"""
        schema = AppConfig.model_json_schema()

        # Check douban_idatabase fields have Chinese descriptions
        assert (
            "douban-idatabase"
            in schema["properties"]["douban_idatabase_url"]["description"]
        )
        assert "API" in schema["properties"]["douban_idatabase_url"]["description"]

        assert "密钥" in schema["properties"]["douban_idatabase_api_key"]["description"]
        assert (
            "超时时间"
            in schema["properties"]["douban_idatabase_timeout_seconds"]["description"]
        )
