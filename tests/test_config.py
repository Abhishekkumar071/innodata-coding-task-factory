from pathlib import Path

import pytest
from pydantic import ValidationError

from task_factory.config import (
    PINNED_BASE_COMMIT,
    PINNED_PYTEST_VERSION,
    PINNED_RELEASE_TAG,
    Settings,
    get_settings,
    load_settings,
    parse_env_file,
)
from task_factory.errors import ConfigError

SECRET = "sk-test-SUPERSECRET-123"


def test_defaults_are_pinned_values():
    s = load_settings(environ={}, env_file=None)
    assert s.click_base_commit == PINNED_BASE_COMMIT == "cf19179e8e2fd54c601378cec9e0d21bb12b6fb1"
    assert s.click_release_tag == PINNED_RELEASE_TAG == "8.5.1"
    assert s.pytest_pin == PINNED_PYTEST_VERSION == "9.0.2"
    assert s.click_repo_url == "https://github.com/pallets/click.git"
    assert s.upstream_changes_path == Path("artifacts/upstream/CHANGES.md")
    assert (s.llm_provider, s.llm_model, s.llm_mode) == ("google-genai", "gemini-2.5-flash", "live")
    assert s.llm_api_key is None
    assert s.llm_temperature == 0.0
    assert s.harbor_max_parallel == 2 and s.sandbox_max_parallel == 3
    assert s.cors_origins == ["http://localhost:5173"]
    assert s.sandbox_image == "click-sandbox:cf19179e8e2f"


def test_env_overrides_and_type_coercion():
    s = load_settings(
        environ={
            "LLM_MODEL": "gemini-2.5-pro",
            "HARBOR_MAX_PARALLEL": "1",
            "LLM_TEMPERATURE": "0.5",
            "CACHE_DIR": "/tmp/x",
            "CORS_ORIGINS": "http://a:1, http://b:2 ,",
            "LLM_MODE": "replay",
        },
        env_file=None,
    )
    assert s.llm_model == "gemini-2.5-pro"
    assert s.harbor_max_parallel == 1
    assert s.llm_temperature == 0.5
    assert s.cache_dir == Path("/tmp/x")
    assert s.cors_origins == ["http://a:1", "http://b:2"]
    assert s.llm_mode == "replay"


def test_empty_values_mean_default():
    s = load_settings(environ={"LLM_API_KEY": "", "LLM_MODEL": "   "}, env_file=None)
    assert s.llm_api_key is None
    assert s.llm_model == "gemini-2.5-flash"


def test_env_file_parsing_and_precedence(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n"
        "\n"
        "export LLM_MODEL='from-file'\n"
        'LOG_LEVEL="DEBUG"\n'
        f"LLM_API_KEY={SECRET}\n",
        encoding="utf-8",
    )
    s = load_settings(environ={"LOG_LEVEL": "WARNING"}, env_file=env_file)
    assert s.llm_model == "from-file"
    assert s.log_level == "WARNING"  # process env beats .env
    assert s.require_llm_api_key() == SECRET


def test_env_file_with_bom_and_crlf_is_accepted(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"\xef\xbb\xbfLLM_MODEL=bom-ok\r\nLOG_LEVEL=ERROR\r\n")
    assert parse_env_file(env_file) == {"LLM_MODEL": "bom-ok", "LOG_LEVEL": "ERROR"}


def test_env_file_bad_line_raises(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NOT A VALID LINE\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"\.env:1"):
        parse_env_file(env_file)


def test_api_key_is_secret_and_never_printed():
    s = load_settings(environ={"LLM_API_KEY": SECRET}, env_file=None)
    assert SECRET not in repr(s)
    assert SECRET not in str(s)
    assert SECRET not in s.model_dump_json()
    assert s.require_llm_api_key() == SECRET


def test_missing_api_key_raises_config_error():
    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        load_settings(environ={}, env_file=None).require_llm_api_key()


@pytest.mark.parametrize(
    ("var", "value"),
    [
        ("CLICK_BASE_COMMIT", "not-a-sha"),
        ("CLICK_BASE_COMMIT", PINNED_BASE_COMMIT.upper()),
        ("PYTEST_PIN", "latest"),
        ("LLM_MODE", "offline"),
        ("LLM_TEMPERATURE", "5"),
        ("HARBOR_MAX_PARALLEL", "0"),
        ("LOG_LEVEL", "verbose"),
    ],
)
def test_invalid_values_raise_config_error_without_echoing_input(var, value):
    with pytest.raises(ConfigError) as info:
        load_settings(environ={var: value, "LLM_API_KEY": SECRET}, env_file=None)
    text = str(info.value)
    assert var in text
    assert SECRET not in text
    if len(value) > 3:
        assert value not in text


def test_settings_are_frozen_and_strict():
    s = load_settings(environ={}, env_file=None)
    with pytest.raises(ValidationError):
        s.llm_model = "other"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Settings(unknown_field=1)  # type: ignore[call-arg]


def test_unrelated_env_vars_are_ignored():
    s = load_settings(environ={"PATH": "/bin", "RANDOM_VAR": "x"}, env_file=None)
    assert s == load_settings(environ={}, env_file=None)


def test_get_settings_is_cached_and_reads_environment(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("LLM_MODEL=from-dotenv\n", encoding="utf-8")
    first = get_settings()
    assert first.llm_model == "from-dotenv"  # .env in working directory (tmp_path)
    monkeypatch.setenv("LLM_MODEL", "from-env")
    assert get_settings() is first  # cached
    get_settings.cache_clear()
    assert get_settings().llm_model == "from-env"
