from __future__ import annotations

from ph.hooks import plan_post_command_hook


def test_plan_success_runs_history_and_validation() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is True


def test_plan_failure_runs_history_only() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=3,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False


def test_plan_validate_command_skips_auto_validation() -> None:
    plan = plan_post_command_hook(
        command="validate",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False


def test_plan_help_success_appends_history_and_skips_validation() -> None:
    plan = plan_post_command_hook(
        command="help",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False


def test_plan_reset_success_skips_hook_entirely() -> None:
    plan = plan_post_command_hook(
        command="reset",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is False
    assert plan.run_validation is False


def test_plan_reset_failure_logs_history() -> None:
    plan = plan_post_command_hook(
        command="reset",
        exit_code=2,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False


def test_plan_no_post_hook_flag_skips_everything() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=True,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is False
    assert plan.run_validation is False


def test_plan_env_skip_skips_everything() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="quick",
        env={"PH_SKIP_POST_HOOK": "1"},
    )
    assert plan.append_history is False
    assert plan.run_validation is False


def test_plan_no_history_still_runs_validation() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=False,
        no_history=True,
        no_validate=False,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is False
    assert plan.run_validation is True


def test_plan_no_validate_still_logs_history() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=True,
        post_validate_mode="quick",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False


def test_plan_post_validate_never_skips_validation() -> None:
    plan = plan_post_command_hook(
        command="doctor",
        exit_code=0,
        no_post_hook=False,
        no_history=False,
        no_validate=False,
        post_validate_mode="never",
        env={},
    )
    assert plan.append_history is True
    assert plan.run_validation is False
