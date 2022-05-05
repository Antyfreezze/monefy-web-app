# monefy-web-app

![example workflow](https://github.com/parseltonguedev/monefy-web-app/actions/workflows/monefy-app-build.yml/badge.svg)
[![codecov](https://codecov.io/gh/parseltonguedev/monefy-web-app/branch/master/graph/badge.svg?token=IE74W8N4QN)](https://codecov.io/gh/parseltonguedev/monefy-web-app)

### Purpose of the project
Monefy-web-app idea - analyze and visualize data from Monefy App
that will be parsed from csv formatted backup created in Monefy mobile application  

The project was made for academic purpose to get new knowledge about Python, async, web, db, etc.

### Project structure

```
.
├── env
├── aws-ec2-sanic-web-app.yaml
├── config.py
├── Dockerfile
├── poetry.lock
├── pyproject.toml
├── README.md
├── requirements.txt
├── run.py
├── setup.py
├── src
│   ├── domain
│   ├── __init__.py
│   ├── models
│   ├── resources
│   └── schema
├── tests
└── utils.py
```

### Where the data comes from

Project using Dropbox storage to store Monefy csv backup files.

After user sends backup file, Monefy-web-app store it to Dropbox storage, parse it and save data to database

### Critical files

If run with pip:

* `requirements.txt` - required packages to run app

If run with poetry:

* `poetry.lock` - file with dependencies and their versions
to check dependecies tree run command: `poetry show --tree`
* `poetry.toml` - project description. Using for orchestrate project and its dependencies

Provide sensitive data with these commands for Dropbox client:

After creating Dropbox App in [Developers App console](https://www.dropbox.com/developers)
export `App key` and `App secret` to environment variable. 
Also required DROPBOX_PATH environment variable that's provide path to uploaded Monefy CSV backup files.

```
export DROPBOX_TOKEN=yourDropboxToken
export DROPBOX_PATH=yourPathToCsvBackups (example: /Apps/monefy/database/)
export DROPBOX_APP_SECRET=yourDropboxAppSecret
```

### How to run
* With pip:
1) Install Python 3.10
2) Clone project: `git clone`
3) Create and activate virtual environment:
    ```
    python3 -m venv env
    source env/bin/activate
    ```
4) Install required packages from `Critical files step`: `pip install -r requirements.txt`
5) Provide environment variables from `Critical files step`
6) You can provide additional parameters to run Monefy-web-app as:
   - --host (default: 0.0.0.0)
   - --port (default: 1337)
   - --auto-reload (default: False)
   - --debug (default: False)
   - --access_log (default: False)
    
    Example:
    `python run.py --port=8888 --auto-reload=True --debug=True --access_log=True`

* With poetry:

1) Install Python3.10
2) Clone project:
    ```
   git clone
   ```
3) Install poetry:
    Depends on OS - [poetry installation](https://python-poetry.org/docs/)
4) [Install dependencies](https://python-poetry.org/docs/basic-usage/#installing-dependencies):
    ```
   poetry install
   poetry shell
   ```
5) Provide environment variables from `Critical files step`
6) Run application. You can provide additional parameters to run Monefy-web-app as:
   - --host (default: 0.0.0.0)
   - --port (default: 1337)
   - --auto-reload (default: False)
   - --debug (default: False)
   - --access_log (default: False)
    
    Example:
    `python run.py --port=8888 --auto-reload=True --debug=True --access_log=True`
   

* With docker:

1) Edit Dockerfile for your Dropbox application configuration (Token, Path, App secret)
2) Optional: add commands to CMD for configure host, port, auto reload, debug or access log
3) Run Dockerfile:
    ```
   docker build --tag python-sanic .
   docker run -d -p 1337:1337 python-sanic
    ```
   
### How to enable Dropbox Webhook

1) Open created Dropbox Developer app
2) Scroll to `Webhooks`
3) Paste dropbox webhook endpoint and hit `Add` button:

    `http://application_ip:application_port/dropbox/dropbox_webhook`
4) After webhook has been added to Dropbox Developer App its status should be changed to `Enabled`

### How to run tests

Pytest supports several ways to run and select tests from CLI:

- Run tests in a module:
  - `pytest tests/test_%test_name%.py`

- Run tests in a directory:
  - `pytest`

### API endpoints

| Resource URL             | Method'(s) | Description                                                                                                                                                                                                             |
|--------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| /healthcheck             | GET        | Endpoint for smoke test                                                                                                                                                                                                 |
| /monefy/monefy_info      | GET, POST  | Get current Monefy statistic from Dropbox or add Monefy statistic from Dropbox to instance                                                                                                                              |
| /dropbox/dropbox_webhook | GET, POST  | Verify Dropbox webhook or trigger Webhook by actions in Dropbox storage<br/>                                                                                                                                            |
| /monefy_aggregation      | GET        | Download file with aggregated or detailed transaction information from latest uploaded Monefy backup file. Parameters - **format** (**required**, valid values - **csv**/**json**), **summarized** (optional parameter) |