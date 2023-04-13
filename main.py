from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Cross origin resources sharing

# from database import (
#     fetch_one_todo,
#     fetch_all_todos,
#     create_todo,
#     update_todo,
#     remove_todo
# )
from models import User, Project
from database import (
    fetch_one_user,
    fetch_one_project, 
    create_user,
    create_project)



app = FastAPI()

# An "origin" is any combination of URL and port. 
# Allow resource sharing between React (running on port 3000) and FastAPI (running on some different port)
# NOTE: If you don't get the origins *exactly right* (e.g. if you make it https when it is supposed to be http),
#  you will see errors like this in browser debugging tools: 
#      Access to XMLHttpRequest at 'http://localhost:8000/api/todo' from origin 'http://localhost:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
# And in the uvicorn backend terminal you'll see preflight requests of type OPTIONS get rejected with a 400 bad request
#  every time you try to add or delete an item. You'll also not see anything but an empty item because todoList in App.js will be empty.

origins = ['http://localhost:3000']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def reformat_mongodb_id_field(response: dict) -> dict:
    """
    MongoDB ObjectID field cannot be encoded into JSON for transmission back to frontend. Convert to string.
    :param response: Dictionary containing a MongoDB document.
    """
    if '_id' in response:
        response['_id'] = str(response.pop('_id'))
    return response


@app.get("/")
def read_root():
    return {'ping': 'pong'}


@app.get("/api/user/{email}")
async def get_user_by_email(email: str):
    response = await fetch_one_user(email)
    if response:
        return reformat_mongodb_id_field(response)
    raise HTTPException(404, f"There is no user with email {email}")


@app.get("/api/project/{project_id}")
async def get_project_by_id(project_id: str):
    response = await fetch_one_project(project_id)
    if response:
        return reformat_mongodb_id_field(response)
    raise HTTPException(404, f"There is no project with ID {project_id}")


@app.post("/api/user")
async def post_user(user_entry: User):
    response = await create_user(user_entry.dict())
    if response:
        return reformat_mongodb_id_field(response)
    raise HTTPException(400, "Something went wrong / bad request")



@app.post("/api/project/")
async def post_project(project_entry: Project):
    response = await create_project(project_entry.dict())
    if response:
        return reformat_mongodb_id_field(response)
    raise HTTPException(400, "Something went wrong / bad request")
