# repo-settings

Keeps the settings of every non-archived repository owned by `Crocmagnon` aligned with
[`settings.json`](settings.json). New repositories are picked up automatically: nothing to declare.

## How it works

- **Check drift** runs every Monday, on each push to `main`, and on demand. It runs
  `sync.py --dry-run`, which prints every difference as `repo: key current → wanted` and fails
  when there is one. GitHub mails the failure.
- **Apply settings** runs only on demand (Actions tab → Run workflow) and fixes the drift with
  `sync.py --yes`.

Both workflows use the `SETTINGS_TOKEN` secret: a fine-grained token on all `Crocmagnon`
repositories with *Administration: Read and write*. Renew it when it expires.

## Add a setting

Each top-level key of `settings.json` is a path under `/repos/{owner}/{repo}` of the GitHub API:

- `"repo"`: fields of [update a repository](https://docs.github.com/en/rest/repos/repos#update-a-repository),
  read with `GET` and written with `PATCH`, e.g. `"has_wiki": false`.
- Another key with an object, e.g. `"actions/permissions/workflow"`: read with `GET`, written
  with `PUT`.
- Another key with a boolean, e.g. `"vulnerability-alerts"`: an on/off feature, enabled with
  `PUT` and disabled with `DELETE`. Its state is read from `GET`, which answers either 204/404 or
  `{"enabled": …}`.

Then:

1. Add the setting to `settings.json`.
2. Push to `main`. Check drift runs and lists every repository it would change.
3. Read the plan, then run **Apply settings**.

The `SETTINGS_TOKEN` must carry the permission each endpoint asks for; all current ones need
*Administration*.

Only fields that the API returns when reading can be checked; a field it never returns shows up as
drift on every run. Nested objects such as `security_and_analysis` only list the keys to enforce;
when the API omits the whole object (it does for `security_and_analysis` on private repositories,
where the features are unavailable), the repository is skipped for it. `"repo"` fields that
private repositories cannot use on GitHub Free, which the API ignores without error, go in
`PUBLIC_ONLY` in `sync.py` (e.g. `allow_auto_merge`).

## Dependabot

Not used: Renovate is enabled per repository instead, on purpose. Dependabot alerts are disabled
(`vulnerability-alerts`) to avoid notifications, and security updates are left off.

## Per-repository overrides

Every setting applies to every non-archived owned repository, forks included, unless
`settings.json` overrides it under `"overrides"`, keyed by full repository name. An override is
merged into the common settings, key by key:

```json
"overrides": {
  "Crocmagnon/some-repo": {
    "actions/permissions/workflow": {"can_approve_pull_request_reviews": true}
  }
}
```

An overridden value is enforced like any other: if it changes on GitHub, Check drift reports it.
There is no way to leave a setting unmanaged for one repository.

## Run locally

```fish
GITHUB_TOKEN=(gh auth token) python3 sync.py --dry-run
python3 test_sync.py
```

Without `--dry-run`, `sync.py` asks for confirmation before applying; `--yes` skips it.
