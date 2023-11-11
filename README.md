## Setup

### MongoDB

See https://www.helenjoscott.com/2022/01/29/mongod-mongo-mongosh-mongos-what-now/ for explanation of different MongoDB shell utilities

#### Install

    • Download mongosh
    	○ From https://www.mongodb.com/products/shell
    	○ Extract to user folder
    	○ Then add this to system environment variable path: C:\Users\abate\mongosh-1.8.0-win32-x64\bin
    • Download/install community server and make sure to agree to install Compass
    	○ https://www.mongodb.com/try/download/community
    	○ Add this to system environment variable path: C:\Program Files\MongoDB\Server\6.0\bin

#### First time setup

    • Open Compass
    • Under "New Connection"
    	○ Enter the connection string: mongodb://127.0.0.1:27017
    • Now you can create a new database if you want
    • Open a terminal
    	○ Run `mongosh`
    		§ This should show connection above
    	○ Run `show dbs`
    		§ This should list the databases

### Backend

#### Install Requirements

If developing on a Windows machine, I recommend PyEnv for configuring Python versions. This may be required before you can use pipenv if you don't already have the Python version specified in Pipfile installed.
https://github.com/pyenv-win/pyenv-win/blob/master/README.md#installation

Run `pyenv update` to make sure the Python 3.11.6 installer is available (you can check via `pyenv install -l`), then run `pyenv install 3.11.6`. NOTE: do NOT install a version that has a letter in it (e.g. 3.11.6b1), as that may cause version requirement checks to fail.

Also C++ build tools should be installed before installing the pip environment

```
cd backend
# This will populate the Pipfile with package and version information in requirements.txt
pipenv shell
# This actually installs the requirements using Pipfile.
pipenv install
```

If you run into an error about compiled vs installed versions of the numpy API being different, see the docstring [here](https://github.com/numpy/numpy/blob/maintenance/1.26.x/numpy/core/setup_common.py) for a mapping of C API hex to numpy version numbers. Install the version number
that the error message is complaining a package was compiled against. E.g. `pipenv install numpy==1.23`

#### To run

```
uvicorn main:app --reload
```

### Deployment TODOs

- Change main.py's frontend URI and database.py's database URI.
