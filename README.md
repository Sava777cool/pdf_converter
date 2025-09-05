# PDF menu analyzer

> Script for work with pdf files, get data from pdf and save it to json file.

![python](https://img.shields.io/badge/python-3.11-BLUE)

## Content
- [Installation](#installation)
- [Description](#description)

## Installation
- Ubuntu
- Python3.11

#### Virtualenv
```shell script
$ sudo apt install virtualenv
```
## Clone
`https://github.com/Sava777cool/github_crawler.git`

## Setup
Install virtualenv in project folder.
```shell script
[project_folder]$ virtualenv -p $(which python3.11) venv
```
**Don't change the name "venv", the path to the virtual environment is used when creating services.** 

**If you want to change the name, make the appropriate changes to the file `[project_folder]/services/install.sh`**
```shell script
...
touch "$ENV_PRJ_SRC"
echo "VENV_PATH=${PWD}/venv" >> "${ENV_PRJ_SRC}"
...
```
Activate virtualenv
```shell script
[project_folder]$ source venv/bin/activate
```
Install python packages from requirements.txt
```shell script
(venv)[project_folder]$ pip install -r requirements.txt
```
Create the .env in the following folder `[project_folder]/config/`
and enter the appropriate data for each service api, example data in file .env_example:
```.env_example
# [project_folder]/config/.env_example

OPENAI_API_KEY = xxxx

```
Add PDF files to `[project_folder]`

## Description
The program consists of the following packages:
#### main.py
- main file for start crawling;

#### complete_YOUR_FILE_NAME_menu.json
- file with transformed menu data;

#### Run scripts

`python main.py` - start script for analyze pdf files.
