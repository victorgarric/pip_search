# pip_search

[__NG edition__](#ng-edition)

__Wrapping the needs of a "pip search" command necessity through PyPi.org__

See [Use Policy](./USE_POLICY.md).

## Installation & Usage

Install with:

```sh
uv pip install pip-search-ng
```

Use:

```sh
pip_search <search terms...>
```

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

![https://raw.githubusercontent.com/ink-splatters/pip_search/dev/screenshot.jpg](https://raw.githubusercontent.com/ink-splatters/pip_search/dev/screenshot.jpg)

## Development

```sh
uv sync --all-extras 
```

Quality checks:

```sh
uv run poe lint
uv run poe test
uv run poe vulture
```

Auto-fixing some linting issues (`ruff fix`):

```sh
uv run poe fix
```

## [Changelog](./CHANGELOG.md)

## NG Edition

_NG_ (_New generation_) is about:
- Making it work in 2026 and beyond (upstream didn't work anymore when the fork was started)
- Improving UX and/or extending functionality (currently - TODO/undecided)

