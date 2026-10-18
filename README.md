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

1. Add a line to `settings.json`, using the field name and value of the
   [update a repository](https://docs.github.com/en/rest/repos/repos#update-a-repository) API,
   e.g. `"has_wiki": false`.
2. Push to `main`. Check drift runs and lists every repository it would change.
3. Read the plan, then run **Apply settings**.

Only fields that the same API returns when reading a repository can be checked; a field it never
returns shows up as drift on every run. Nested objects such as `security_and_analysis` only list
the keys to enforce; when the API omits the whole object (it does for `security_and_analysis` on
private repositories, where the features are unavailable), the repository is skipped for it.

## Deliberately unmanaged

- Dependabot: Renovate is used instead, enabled per repository on purpose.

## No exclusion list

Every setting applies to every non-archived owned repository, forks included. There is no way to
exempt a repository yet: if one ever needs a different value, add an exclusion list to `sync.py`
first.

## Run locally

```fish
GITHUB_TOKEN=(gh auth token) python3 sync.py --dry-run
python3 test_sync.py
```

Without `--dry-run`, `sync.py` asks for confirmation before applying; `--yes` skips it.
