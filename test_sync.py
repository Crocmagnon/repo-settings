from sync import diff


def test_diff():
    wanted = {"delete_branch_on_merge": True, "has_wiki": False}
    assert diff({"delete_branch_on_merge": True, "has_wiki": False}, wanted) == {}
    assert diff({"delete_branch_on_merge": False, "has_wiki": False}, wanted) == {"delete_branch_on_merge": True}
    # A field missing from the API response counts as drift.
    assert diff({}, wanted) == wanted


if __name__ == "__main__":
    test_diff()
    print("ok")
