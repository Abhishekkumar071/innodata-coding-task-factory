import pytest

from task_factory import errors


@pytest.mark.parametrize(
    ("cls", "parent"),
    [
        (errors.ConfigError, errors.FactoryError),
        (errors.RepoStateError, errors.FactoryError),
        (errors.LLMError, errors.FactoryError),
        (errors.LLMResponseInvalid, errors.LLMError),
        (errors.SandboxError, errors.FactoryError),
        (errors.PrecheckFailed, errors.FactoryError),
        (errors.GuardViolation, errors.FactoryError),
        (errors.LeakageDetected, errors.GuardViolation),
        (errors.ScopeViolation, errors.GuardViolation),
        (errors.HarborError, errors.FactoryError),
        (errors.NotFound, errors.FactoryError),
        (errors.RunConflict, errors.FactoryError),
    ],
)
def test_hierarchy_matches_architecture(cls, parent):
    assert issubclass(cls, parent)
    assert issubclass(cls, Exception)


@pytest.mark.parametrize(
    ("cls", "status"),
    [
        (errors.FactoryError, 500),
        (errors.ConfigError, 400),
        (errors.RepoStateError, 500),
        (errors.LLMError, 502),
        (errors.LLMResponseInvalid, 502),
        (errors.SandboxError, 500),
        (errors.HarborError, 500),
        (errors.NotFound, 404),
        (errors.RunConflict, 409),
    ],
)
def test_http_status_mapping(cls, status):
    assert cls.http_status == status


def test_task_level_errors_are_flagged():
    for cls in (errors.PrecheckFailed, errors.GuardViolation, errors.LeakageDetected,
                errors.ScopeViolation):
        assert cls.task_level is True
    for cls in (errors.ConfigError, errors.RepoStateError, errors.HarborError):
        assert cls.task_level is False


def test_issues_are_listed_in_str():
    exc = errors.ScopeViolation("package invalid", issues=["a", "b"])
    assert exc.message == "package invalid"
    assert exc.issues == ["a", "b"]
    assert str(exc) == "package invalid\n  - a\n  - b"
    assert str(errors.NotFound("missing")) == "missing"
