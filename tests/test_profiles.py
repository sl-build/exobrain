"""Tests for exocortex.profiles module."""


import pytest

from exocortex.profiles import (
    PROFILE_PROMPTS,
    add_profile,
    get_all_profiles,
    get_profile_details,
    get_valid_profile_names,
    remove_profile,
)


class TestBuiltinProfiles:
    """Built-in profiles must match the article's claims."""

    def test_five_article_profiles_exist(self):
        """Article lists: critic, planner, judge, extractor, reasoning."""
        required = {"critic", "planner", "judge", "extractor", "reasoning"}
        assert required.issubset(set(PROFILE_PROMPTS.keys())), \
            f"Missing profiles: {required - set(PROFILE_PROMPTS.keys())}"

    def test_critic_low_temp_deep(self):
        """Article: critic — low temperature, deep thinking."""
        c = PROFILE_PROMPTS["critic"]
        assert c["default_temperature"] <= 0.3, f"critic temp={c['default_temperature']} too high"
        assert c["default_depth"] == "deep"

    def test_planner_step_by_step_deep(self):
        """Article: planner — step-by-step with dependencies, deep."""
        p = PROFILE_PROMPTS["planner"]
        assert p["default_depth"] == "deep"

    def test_judge_neutral_precise(self):
        """Article: judge — evaluate options, neutral, precise."""
        j = PROFILE_PROMPTS["judge"]
        assert j["default_temperature"] <= 0.3, f"judge temp={j['default_temperature']} too high"
        assert j["default_depth"] in ("normal", "deep")

    def test_extractor_coldest(self):
        """Article: extractor — coldest temperature."""
        temps = {name: cfg["default_temperature"] for name, cfg in PROFILE_PROMPTS.items()}
        assert temps["extractor"] == min(temps.values()), \
            f"extractor ({temps['extractor']}) not coldest; min is {min(temps.values())}"

    def test_reasoning_balanced(self):
        """Article: reasoning — balanced analysis, general purpose."""
        r = PROFILE_PROMPTS["reasoning"]
        assert r["default_depth"] == "normal"

    def test_writer_profile_exists(self):
        """Code has a writer profile (not in article, but should work)."""
        assert "writer" in PROFILE_PROMPTS

    def test_all_builtins_have_required_keys(self):
        """Every profile must have system_prompt, default_depth, default_temperature."""
        for name, cfg in PROFILE_PROMPTS.items():
            assert "system_prompt" in cfg, f"{name} missing system_prompt"
            assert "default_depth" in cfg, f"{name} missing default_depth"
            assert "default_temperature" in cfg, f"{name} missing default_temperature"


class TestUserProfiles:
    """Custom profiles via profile-add / profile-remove."""

    def test_add_custom_profile(self, mock_config_dir):
        add_profile("custom1", "Custom prompt", "normal", 0.4)
        profiles = get_all_profiles()
        assert "custom1" in profiles
        assert profiles["custom1"]["system_prompt"] == "Custom prompt"
        assert profiles["custom1"]["default_depth"] == "normal"
        assert profiles["custom1"]["default_temperature"] == 0.4

    def test_custom_profile_appears_in_valid_names(self, mock_config_dir):
        add_profile("myprof", "My prompt", "deep", 0.2)
        names = get_valid_profile_names()
        assert "myprof" in names

    def test_cannot_override_builtin(self, mock_config_dir):
        with pytest.raises(ValueError, match="Cannot override built-in"):
            add_profile("critic", "Override", "normal", 0.5)

    def test_cannot_remove_builtin(self, mock_config_dir):
        with pytest.raises(ValueError, match="Cannot remove built-in"):
            remove_profile("critic")

    def test_remove_nonexistent_user_profile(self, mock_config_dir):
        with pytest.raises(KeyError):
            remove_profile("no_such_profile")

    def test_remove_custom_profile(self, mock_config_dir):
        add_profile("temp_prof", "Temp", "quick", 0.1)
        assert "temp_prof" in get_all_profiles()
        remove_profile("temp_prof")
        assert "temp_prof" not in get_all_profiles()

    def test_get_profile_details_builtin(self):
        details = get_profile_details("critic")
        assert details is not None
        assert details["source"] == "builtin"

    def test_get_profile_details_user(self, mock_config_dir):
        add_profile("user_prof", "User prompt", "deep", 0.5)
        details = get_profile_details("user_prof")
        assert details is not None
        assert details["source"] == "user"
        assert details["system_prompt"] == "User prompt"

    def test_get_profile_details_nonexistent(self):
        assert get_profile_details("no_such") is None

    def test_builtins_win_on_collision(self, mock_config_dir):
        """If user creates a profile with same name as builtin, builtin wins."""
        # This shouldn't be possible due to the guard, but get_all_profiles
        # explicitly prefers builtins
        profiles = get_all_profiles()
        assert profiles["critic"]["system_prompt"] == PROFILE_PROMPTS["critic"]["system_prompt"]


class TestGetAllProfilesMerged:
    """get_all_profiles must merge built-in + user profiles correctly."""

    def test_merges_builtin_and_user(self, mock_config_dir):
        add_profile("extra", "Extra prompt", "quick", 0.1)
        all_prof = get_all_profiles()
        # Built-in profiles present
        assert "critic" in all_prof
        # User profile present
        assert "extra" in all_prof
        assert all_prof["extra"]["system_prompt"] == "Extra prompt"
