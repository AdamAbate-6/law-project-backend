# MongoDB driver
import motor.motor_asyncio
from bson.objectid import ObjectId

from models import User

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


async def fetch_one_project(project_id: str):
    document = await projects_collection.find_one({'_id': ObjectId(project_id)})
    return document


async def create_user(user_entry: dict):
    result = await users_collection.insert_one(user_entry)
    return user_entry


async def create_project(project_entry: dict):
    result = await projects_collection.insert_one(project_entry)
    return project_entry