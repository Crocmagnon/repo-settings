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
# Unavailable on private repos with GitHub Free: the API silently ignores them there.
PUBLIC_ONLY = {"allow_auto_merge"}


def request(method, url, token, body=None, missing=False):
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
            raw = resp.read()
            return json.loads(raw) if raw else {}, next_url and next_url.group(1)
    except urllib.error.HTTPError as e:
        if missing and e.code == 404:
            return None, None
        sys.exit(f"{method} {url} failed: {e.code} {e.read().decode()}")


def owned_repos(token):
    url = f"{API}/user/repos?affiliation=owner&per_page=100"
    while url:
        page, url = request("GET", url, token)
        yield from (r["full_name"] for r in page if not r["archived"])


def diff(current, wanted):
    changes = {}
    for k, v in wanted.items():
        if isinstance(v, dict):
            # A nested object is absent where the feature is unavailable, e.g.
            # security_and_analysis on private repos: skip it rather than report drift forever.
            if k in current and (sub := diff(current[k] or {}, v)):
                changes[k] = sub
        elif current.get(k) != v:
            changes[k] = v
    return changes


def flat(d, prefix=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from flat(v, f"{prefix}{k}.")
        else:
            yield f"{prefix}{k}", v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show the plan, exit 1 on drift")
    parser.add_argument("--yes", action="store_true", help="apply without asking")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    wanted = json.loads((Path(__file__).parent / "settings.json").read_text())

    plan = {}
    for name in owned_repos(token):
        url = f"{API}/repos/{name}"
        # The list endpoint omits fields like delete_branch_on_merge, so fetch each repo.
        repo, _ = request("GET", url, token)
        calls = []
        for path, want in wanted.items():
            if path == "repo":
                want = {k: v for k, v in want.items() if not (repo["private"] and k in PUBLIC_ONLY)}
                current, method, target, prefix = repo, "PATCH", url, ""
            elif isinstance(want, bool):
                # A toggle answers 204/404 (vulnerability-alerts) or {"enabled": bool}.
                found, _ = request("GET", f"{url}/{path}", token, missing=True)
                enabled = found is not None and found.get("enabled", True)
                if enabled != want:
                    print(f"{name}: {path} {json.dumps(enabled)} → {json.dumps(want)}")
                    calls.append(("PUT" if want else "DELETE", f"{url}/{path}", {}))
                continue
            else:
                current, _ = request("GET", f"{url}/{path}", token)
                method, target, prefix = "PUT", f"{url}/{path}", f"{path}."
            if changes := diff(current, want):
                flat_current = dict(flat(current))
                for k, v in flat(changes):
                    print(f"{name}: {prefix}{k} {json.dumps(flat_current.get(k))} → {json.dumps(v)}")
                calls.append((method, target, changes))
        if calls:
            plan[name] = calls

    if not plan:
        print("No drift.")
        return
    if args.dry_run:
        sys.exit(1)
    if not args.yes and input(f"Apply to {len(plan)} repos? [y/N] ").lower() != "y":
        sys.exit("Aborted.")
    for name, calls in plan.items():
        for method, target, body in calls:
            request(method, target, token, body)
        print(f"{name}: updated")


if __name__ == "__main__":
    main()
