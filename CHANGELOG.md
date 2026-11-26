### 0.5.1

  - Rebrand to pip-search-ng
  - Release on PyPi

### 0.3.0 - 0.4.7

  - Move this log to CHANGELOG.md (from README.md)
  - README.md: update installation instructions (@God-damnit-all)
  - chore: deprecate Python < 3.14
  - chore(fix):
    - Errors reported by linters
    - GH actions
    - Narrow expected exception catches
    - Centralize Fastly, parser, and PoW exception messages on exception
      classes
    - Rework mock side-effect setup so vulture can analyze it
    - Refactor version fallback handling to satisfy return-count lint.
    - Cap async version-fetch connection pools to the semaphore concurrency
      limit
    - Update dependencies and GitHub actions

### 0.2.1

  - README.md: refer link to Acceptable Use Policy and add "2026 edition"

### 0.2.0

  - `--debug` changed to `--log-level`
  - HTTP tracing moved to TRACE log level
  - LICENSE update: Acceptable Use Policy

### 0.1.0

  - Migrate packaging/build to `pyproject.toml` + Hatch, define `project.scripts`, and align dev workflows with `uv` + Poe tasks (`lint`, `typecheck`, `test`).
  - Move from a legacy flat module layout to a structured package split: `cli/`, `http/`, `internal/`, and typed domain models (`dataclass`, `StrEnum`, protocols).
  - Fix passing through CAPTCHA: add a new Fastly challenge solver orchestration flow:
    - `FastlyChallengeSolver` handles probe -> script fetch -> parse -> round-based post-back.
    - Pluggable providers for PAT, PoW, and client metrics.
    - Robust parser/error taxonomy and explicit unsolvable handling (e.g., CAPTCHA).
  - Improve HTTP layer via a custom `httpx.Client` wrapper with request/response tracing and sensitive-header redaction.
  - Add Loguru-based `--log-level` control (default `WARNING`; levels: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`).
  - Scope verbose HTTP request/response tracing to `TRACE`; keep `DEBUG` focused on internal solver/search diagnostics.
  - Refactor search pipeline for clearer config/options handling, stronger typing, and concurrent missing-version resolution.
  - Expand tests significantly around challenge parsing/solving, providers, response builder, tracing, and search behavior.

### 0.0.14

  - Passing through CAPTCHA

### 0.0.13

  - Updated for version info

### 0.0.12

  - Updated to comply with new PyPi.org format

### 0.0.11

  - Add date format options

### 0.0.10

  - Add sorting options
  - Changes thanks to @dsoares and @genevera

### 0.0.9

  - Hotfix for Python 3.8 to 3.10 compatibility
  - Changes thanks to @jiyeqian

### 0.0.8 *(deleted for compatibility issues with python 3.8 to 3.10)*

  - Updated for better compatibility and better display
  - Changes thanks to @RCristiano

### 0.0.7

  - Merge from pip_search_color, colorized output with hyperlink features
  - Changes thanks to @kkatayama

### 0.0.6

  - Parsing with beautiful soup, allowing results with one package to be parsed
  - Changes thanks to @nsultova

### 0.0.4

  - Add multiple keywords support
  - Add usage info
  - Changes thanks to @Maxz44
