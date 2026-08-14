# YasinCoder Release Policy

## Versioning

YasinCoder follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

- MAJOR: incompatible user/configuration or public API changes.
- MINOR: backward-compatible features.
- PATCH: backward-compatible fixes and documentation/security corrections.

The canonical version is stored in `VERSION` and is consumed by `pyproject.toml`.

## Release checklist

1. Work only from the GitHub issue assigned to the release phase.
2. Ensure the working tree contains no secrets, credentials, model binaries, caches, logs or developer-specific paths.
3. Run:
   - `python -m compileall -q .`
   - `python -m unittest discover -s tests -p 'test_*.py' -v`
4. Verify the clean-clone invariants and configuration examples.
5. Update `CHANGELOG.md` with user-visible changes.
6. Update `VERSION`.
7. Tag the exact release commit as `vX.Y.Z`.
8. Build artifacts from Git only; runtime/model data must never be required.
9. Publish the GitHub release with generated source artifacts.
10. Keep rollback simple: users can return to the previous Git tag and retain their external configuration/runtime data.

## Packaging

The repository is the source of truth. A release must be buildable from a fresh clone with Python and the declared build backend. No GGUF/model file is packaged.

## Configuration and migration

User configuration belongs outside Git. New releases must preserve compatible settings where possible. When a setting is renamed or removed, document the migration in the changelog and release notes. Never silently overwrite user configuration.

## Stable vs experimental

Stable features are documented, tested and covered by the release gate. Experimental features must be clearly labeled and must not be required for a clean installation.

## Rollback

To roll back, check out the previous release tag, reinstall/build from that tag, and reuse the user's external configuration. Do not restore model binaries or secrets from Git history.
