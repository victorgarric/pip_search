# pip_search

__Warping the needs of a "pip search" command necessity through PyPi.org__

## Installation & Usage
Install with `pip install pip_search`

Use with `pip_search anything`

To use as the traditional `pip search <keywords>` method, add this alias to your **.zshrc, .bashrc, .bash_profile, etc.**
```bash
alias pip='function _pip(){
    if [ $1 = "search" ]; then
        pip_search "$2";
    else pip "$@";
    fi;
};_pip'

```
Then run with `pip search`

![https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png](https://raw.githubusercontent.com/kkatayama/pip_search/master/screenshot.png)

Hold the **command** or **ctrl** key to click on the folder icons as a hyperlink.

## Dependancies
* bs4
* rich
* requests

## Updates log

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
