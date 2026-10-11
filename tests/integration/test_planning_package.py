from scripts.validate_project import validate_project


def test_repository_planning_package_is_self_consistent():
    assert validate_project() == []
