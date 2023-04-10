# MongoDB driver
import motor.motor_asyncio

from model import Todo

# Connection between database.py and MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
# Create or get a database named Law.
database = client.law
# A collection is analogous to a SQL table.
users_collection = database.users
projects_collection = database.projects
documents_collection = database.documents
# 4/9/2023 thoughts on schema design:
# law
# |-- users
# |   |-- _id
# |   |-- first_name
# |   |-- last_name
# |   |-- email_address
# |   |-- project_ids
# |-- projects
# |   |-- _id
# |   |-- name
# |   |-- chat
# |   |-- user_ids
# |   |-- document_ids
# |-- documents
# |   |-- _id
# |   |-- text
# |   |-- img_urls
# |   |-- user_ids
# |   |-- project_ids
# users and projects are many-to-many. One user can have many projects, and a project can be shared amongst users.
# projects and documents are also many-to-many. One project can have many documents, and some documents might be used by multiple projects.

async def fetch_one_user(email: str):
    document = await users_collection.find_one({'email_address': email})
    return document

async def fetch_one_project(project_id: int):
    document = await projects_collection.find_one({'project_id': project_id})
    return document