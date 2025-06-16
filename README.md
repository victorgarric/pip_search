# pip_search

__Wrapping the needs of a "pip search" command necessity through PyPi.org__

## Installation & Usage
Install with `pip install pip_search`

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
````

Then run with `pip search`

![https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png](https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png)

Hold the **command** or **ctrl** key to click on the folder icons as a hyperlink.

## Dependencies
* bs4
* rich
* requests

## Updates log

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
