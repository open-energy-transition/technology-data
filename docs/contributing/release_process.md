<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Release Process

This guide describes how to create a new release of `technologydata`.

## Overview

The project uses [`setuptools_scm`](https://github.com/pypa/setuptools-scm) for automatic version management based on git tags. The release process is automated through a GitHub Actions workflow that:

- Builds the package
- Creates a GitHub release with auto-generated notes
- Publishes the package to PyPI

## Prerequisites

Before starting a release, ensure:

- All intended changes are merged into the branch you want to release from (the current default branch is `prototype-2`)
- CI/CD tests are passing on that branch
- You have push permissions to the repository

## Release Checklist

Follow these steps to create a new release:

### 1. Update CITATION.cff

!!! warning "Manual Step Required"
    Due to a current limitation in the release workflow (see [HOTFIX in release.yml](https://github.com/open-energy-transition/technology-data/blob/master/.github/workflows/release.yml#L38)), you must manually update the version number in `CITATION.cff`.

Edit `CITATION.cff` and update the version number on line 9:

```yaml
version: X.Y.Z
```

Replace `X.Y.Z` with your new version number (e.g., `0.3.0`).

### 2. Run Pre-commit Checks

Ensure all pre-commit hooks pass:

```bash
uv run pre-commit run --all-files
```

Fix any issues before proceeding.

### 3. Verify CI is Green

Check that all GitHub Actions workflows are passing:

- Navigate to the [Actions tab](https://github.com/open-energy-transition/technology-data/actions)
- Confirm the latest commit on your release branch has all checks passing

### 4. Create and Push the Tag

Create a git tag following semantic versioning (`vMAJOR.MINOR.PATCH`):

```bash
# Ensure you're on the correct branch
git checkout <branch-name>

# Create the tag
git tag v0.3.0

# Push the tag to trigger the release workflow
git push origin v0.3.0
```

!!! tip "Tag Format"
    Tags must follow the pattern `v*.*.*` (e.g., `v0.3.0`, `v1.0.0`) to trigger the release workflow.

### 5. Monitor the Release Workflow

Once you push the tag:

1. Go to the [Actions tab](https://github.com/open-energy-transition/technology-data/actions)
2. Find the "Release" workflow run triggered by your tag
3. Monitor the progress through the following jobs:
   - **Build and verify package**: Builds the distribution files
   - **Create GitHub release**: Creates a release with auto-generated notes
   - **Publish to PyPI**: Uploads the package to PyPI

### 6. Verify the Release

After the workflow completes successfully:

- **GitHub Release**: Check the [Releases page](https://github.com/open-energy-transition/technology-data/releases) for your new release
- **PyPI**: Verify the new version appears on [PyPI](https://pypi.org/project/technologydata/)
- **Installation**: Test installing the new version:

  Using pip:

  ```bash
  pip install --upgrade technologydata
  python -c "import technologydata; print(technologydata.__version__)"
  ```

  Or using uv:

  ```bash
  uv pip install --upgrade technologydata
  python -c "import technologydata; print(technologydata.__version__)"
  ```

## Version Numbering

The project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New functionality in a backwards-compatible manner
- **PATCH** (0.0.X): Backwards-compatible bug fixes

## Related Documentation

- [Contributing Instructions](instructions.md)
- [Release Notes](../home/release-notes.md)
