# Warping the needs of a "pip search" command necessity through PyPi.org 
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

![https://raw.githubusercontent.com/victorgarric/pip_search/main/screenshot.png](https://raw.githubusercontent.com/victorgarric/pip_search/main/screenshot.png)

Hold the **command** or **ctrl** key to click on the folder icons as a hyperlink.


---
0.0.7 Update:
- Merge from pip_search_color, colorized output with hyperlink features

---
0.0.6 Update : 
- Parsing with beautiful soup, allowing results with one package to be parsed

Changes thanks to @nsultova

---
0.0.4 Update : 
- Adding multiple keywords support
- Adding usage info

Changes thanks to @Maxz44
