import yaml

# MongoDB driver
import motor.motor_asyncio
from bson.objectid import ObjectId

from models import ChatEntry, PatentEntry

with open('../config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Connection between database.py and MongoDB
# client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb+srv://{config["mongodb_user"]}:{config["mongodb_pw"]}@cluster0.wyovote.mongodb.net/?retryWrites=true&w=majority')
# Create or get a database named Law.
database = client.law
# A collection is analogous to a SQL table.
users_collection = database.users
projects_collection = database.projects
patents_collection = database.patents
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

async def fetch_one_user(email: str) -> dict:
    document = await users_collection.find_one({'email_address': email})
    return document


async def fetch_one_project(project_id: str) -> dict:
    document = await projects_collection.find_one({'_id': ObjectId(project_id)})
    return document


async def fetch_one_patent(patent_spif: str) -> dict:
    document = await patents_collection.find_one({'spif': patent_spif})
    return document


async def create_user(user_entry: dict) -> dict:
    result = await users_collection.insert_one(user_entry)
    document = await users_collection.find_one({'_id': result.inserted_id})
    return document


async def create_patent(patent_data: dict) -> dict:
    result = await patents_collection.insert_one(patent_data)
    document = await patents_collection.find_one({'_id': result.inserted_id})
    return document


async def modify_user(user_id: str, updated_user: dict) -> dict:
    """Update the user entry with _id == user_id with the contents of updated_user

    Args:
        user_id (str): String representation of ObjectId for MongoDB user entry
        updated_user (dict): Dict whose keys are fields to be modified and whose values are the new field entries. Values should NOT be Nones.
    """
    await users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': updated_user
        }
    )
    document = await users_collection.find_one({'_id': ObjectId(user_id)})
    return document


async def create_project(project_entry: dict) -> dict:
    result = await projects_collection.insert_one(project_entry)
    document = await projects_collection.find_one({'_id': result.inserted_id})
    return document


async def modify_project(project_id: str, updated_project: dict) -> dict:
    """Update the project entry with _id == project_id with the contents of updated_project

    Args:
        project_id (str): String representation of ObjectId for MongoDB project entry
        updated_project (dict): Dict whose keys are fields to be modified and whose values are the new field entries. Values should NOT be Nones.
    """
    await projects_collection.update_one(
        {'_id': ObjectId(project_id)},
        {'$set': updated_project
        }
    )
    document = await projects_collection.find_one({'_id': ObjectId(project_id)})
    return document


async def modify_project_chat(project_id: str, updated_chat: dict[str, list[ChatEntry]]) -> dict:
    """
    updated_chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    """
    await projects_collection.update_one(
        {'_id': ObjectId(project_id)},
        {'$set': {
            'chat': updated_chat
            }
        }
    )
    document = await projects_collection.find_one({'_id': ObjectId(project_id)})
    return document


async def modify_project_patents(project_id: str, updated_patents: dict[str, list[PatentEntry]]) -> dict:

    await projects_collection.update_one(
        {'_id': ObjectId(project_id)},
        {'$set': {
            'patents': updated_patents
            }
        }
    )
    document = await projects_collection.find_one({'_id': ObjectId(project_id)})
    return document
