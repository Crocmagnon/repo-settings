from sync import diff, flat


def test_diff():
    wanted = {"delete_branch_on_merge": True, "has_wiki": False}
    assert diff({"delete_branch_on_merge": True, "has_wiki": False}, wanted) == {}
    assert diff({"delete_branch_on_merge": False, "has_wiki": False}, wanted) == {"delete_branch_on_merge": True}
    # A field missing from the API response counts as drift.
    assert diff({}, wanted) == wanted


def test_diff_nested():
    wanted = {"sa": {"push": {"status": "enabled"}, "scan": {"status": "enabled"}}}
    current = {"sa": {"push": {"status": "disabled"}, "scan": {"status": "enabled"}, "other": {"status": "x"}}}
    assert diff(current, wanted) == {"sa": {"push": {"status": "enabled"}}}
    assert diff({"sa": {"push": {"status": "enabled"}, "scan": {"status": "enabled"}}}, wanted) == {}
    # A missing nested object means the feature is unavailable, not drift.
    assert diff({}, wanted) == {}


def test_flat():
    assert dict(flat({"a": 1, "b": {"c": {"d": 2}}})) == {"a": 1, "b.c.d": 2}


if __name__ == "__main__":
    test_diff()
    test_diff_nested()
    test_flat()
    print("ok")
