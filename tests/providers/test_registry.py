"""Tests for nanobot.providers.registry — ProviderSpec and lookup helpers."""

from nanobot.providers.registry import PROVIDERS, ProviderSpec, find_by_name


class TestProviderSpec:
    def test_label_uses_display_name(self):
        spec = ProviderSpec(name="test", keywords=(), env_key="", display_name="My Provider")
        assert spec.label == "My Provider"

    def test_label_falls_back_to_name_title(self):
        spec = ProviderSpec(name="my_provider", keywords=(), env_key="")
        assert spec.label == "My_Provider"

    def test_label_short_name_title(self):
        spec = ProviderSpec(name="abc", keywords=(), env_key="")
        assert spec.label == "Abc"

    def test_default_backend_is_openai_compat(self):
        spec = ProviderSpec(name="test", keywords=(), env_key="")
        assert spec.backend == "openai_compat"


class TestFindByName:
    def test_finds_existing_provider(self):
        spec = find_by_name("anthropic")
        assert spec is not None
        assert spec.name == "anthropic"
        assert spec.backend == "anthropic"

    def test_finds_provider_with_dashes(self):
        spec = find_by_name("github-copilot")
        assert spec is not None
        assert spec.name == "github_copilot"

    def test_finds_provider_with_underscores(self):
        spec = find_by_name("github_copilot")
        assert spec is not None
        assert spec.name == "github_copilot"

    def test_returns_none_for_unknown(self):
        assert find_by_name("nonexistent_provider") is None


class TestPROVIDERS:
    def test_contains_known_providers(self):
        names = {spec.name for spec in PROVIDERS}
        for expected in ("anthropic", "openai", "deepseek", "dashscope", "minimax"):
            assert expected in names

    def test_every_provider_has_unique_name(self):
        names = [spec.name for spec in PROVIDERS]
        assert len(names) == len(set(names))

    def test_every_provider_has_required_fields(self):
        for spec in PROVIDERS:
            assert spec.name
            assert isinstance(spec.keywords, tuple)
            assert isinstance(spec.env_key, str)
