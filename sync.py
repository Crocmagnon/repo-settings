#!/usr/bin/env python3
"""Align the settings of every non-archived repo owned by the token's user with settings.json."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"


def request(method, url, token, body=None):
    req = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            link = resp.headers.get("Link", "")
            next_url = re.search(r'<([^>]+)>;\s*rel="next"', link)
            return json.load(resp), next_url and next_url.group(1)
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url} failed: {e.code} {e.read().decode()}")


def owned_repos(token):
    url = f"{API}/user/repos?affiliation=owner&per_page=100"
    while url:
        page, url = request("GET", url, token)
        yield from (r["full_name"] for r in page if not r["archived"])


def diff(current, wanted):
    return {k: v for k, v in wanted.items() if current.get(k) != v}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show the plan, exit 1 on drift")
    parser.add_argument("--yes", action="store_true", help="apply without asking")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    wanted = json.loads((Path(__file__).parent / "settings.json").read_text())

    # The list endpoint omits fields like delete_branch_on_merge, so fetch each repo.
    plan = {}
    for name in owned_repos(token):
        repo, _ = request("GET", f"{API}/repos/{name}", token)
        if changes := diff(repo, wanted):
            plan[name] = changes
            for k, v in changes.items():
                print(f"{name}: {k} {json.dumps(repo.get(k))} → {json.dumps(v)}")

    if not plan:
        print("No drift.")
        return
    if args.dry_run:
        sys.exit(1)
    if not args.yes and input(f"Apply to {len(plan)} repos? [y/N] ").lower() != "y":
        sys.exit("Aborted.")
    for name, changes in plan.items():
        request("PATCH", f"{API}/repos/{name}", token, changes)
        print(f"{name}: updated")


if __name__ == "__main__":
    main()
