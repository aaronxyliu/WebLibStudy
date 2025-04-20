### Web Library Version Detecting Experiment Set

### Requirement
Operating System: Linux or Mac  
Python 3

#### Preparation

0. (Optional) Create a Python virtual environment and activate it.
```shell
$ python3 -m venv .
$ source bin/activate
```

The command `deactivate` can be used if you want to quit current environment.
```shell
$ deactivate
```

1. Use the shell script to quickly install all required Python packages. (This script is only valid for Mac. For Linux users, please change "brew" to "apt" in the shell script)
```shell
$ chmod +x env.sh
$ ./env.sh
```

2. Download latest version Chrome and the matching version [Chromedriver](https://developer.chrome.com/docs/chromedriver). Put the Chromedriver under the `/bin` folder and name it "chromedriver".
3. Set up a local or remote ([PlanetScale](https://planetscale.com/) is free to use) database server. Then create two databases, named "Libraries" and "1000-pTs".
4. Create a `.env` file under the root folder to contain your Github token used for crawling, which can be obtained [here](https://github.com/settings/tokens). The connection information of the database created in step 2 should also be put here. The `.env` file format is as follows.
```
GITHUB_TOKEN=gtp_pxt68oJ3A8k6zaapxye9JIm2BEMUvt26xp21
DB_HOST=127.0.0.1
DB_USERNAME=root
DB_PASSWORD=12345678
```


#### Experiment Steps
