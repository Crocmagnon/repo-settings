@README.md

## Notes for agents

- `sync.py` uses the Python standard library only; keep it dependency-free so the workflows need no
  setup step.
- Never run `sync.py` without `--dry-run` yourself: applying changes every repository of the
  account. The user applies through the Apply settings workflow.
- When adding a setting, check its value in the dry-run plan before telling the user it is ready.
- Settings apply to all repositories, forks included, except per-repository `overrides` (see README).
