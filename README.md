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
```
cd backend
# This will populate the Pipfile with package and version information in requirements.txt
pipenv shell
# This actually installs the requirements using Pipfile.
 pipenv install
```

#### To run
```
uvicorn main:app --reload
```

### NOTES 
* Had to update to motor 3.1.1 because of asyncio error with Python 3.11 https://jira.mongodb.org/browse/MOTOR-1054