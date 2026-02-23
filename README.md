# pip_search

__Wrapping the needs of a "pip search" command necessity through PyPi.org__

## Installation & Usage

Install with: `uv tool install pip_search`

Use with `pip_search anything`

You can specify sorting options :

- `pip_search -s name`
- `pip_search -s released`

To use as the traditional `pip search <keywords>` method, add this alias to your **.zshrc, .bashrc, .bash_profile, etc.**

```bash
alias pip='function _pip(){
    if [ $1 = "search" ]; then
        pip_search "$2";
    else pip "$@";
    fi;
};_pip'

```

For fish users, run on fish shell:

```fish
function pip --wraps="pip"
    set command $argv[1]
    set -e argv[1]
    switch "$command"
        case 'search'
            pip_search $argv
        case '*'
            command pip $command $argv
    end
end

funcsave pip
```

Then run with `pip search`

![https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png](https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png)

Hold the **command** or **ctrl** key to click on the folder icons as a hyperlink.

## Development

```sh
uv sync --all-extras 
```

Make sure those are always "green":

```sh
uv run poe fix
uv run poe test
```

## Updates log

- 0.1.0

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

- 0.0.14

  - Passing through CAPTCHA

- 0.0.13

  - Updated for version info

- 0.0.12

  - Updated to comply with new PyPi.org format

- 0.0.11

  - Added date format options

- 0.0.10

  - Added sorting options
  - Changes thanks to @dsoares and @genevera

- 0.0.9

  - Hotfix for Python 3.8 to 3.10 compatibility
  - Changes thanks to @jiyeqian

- 0.0.8 *(deleted for compatibility issues with python 3.8 to 3.10)*

  - Updated for better compatibility and better display
  - Changes thanks to @RCristiano

- 0.0.7

  - Merge from pip_search_color, colorized output with hyperlink features
  - Changes thanks to @kkatayama

- 0.0.6

  - Parsing with beautiful soup, allowing results with one package to be parsed
  - Changes thanks to @nsultova

- 0.0.4

  - Adding multiple keywords support
  - Adding usage info
  - Changes thanks to @Maxz44
