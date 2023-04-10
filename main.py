from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Cross origin resources sharing

# from database import (
#     fetch_one_todo,
#     fetch_all_todos,
#     create_todo,
#     update_todo,
#     remove_todo
# )
from database import (fetch_one_project, fetch_one_user)

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

@app.get("/")
def read_root():
    return {'ping': 'pong'}

@app.get("/api/u{email}")
def get_user_by_email(email):
    response = await fetch_one_user(email)
    if response:
        return response
    raise HTTPException(404, f"There is no user with email {email}")

@app.get("/api/p{project_id}")
def get_project_by_id(project_id):
    response = await fetch_one_project(project_id)
    if response:
        return response
    raise HTTPException(404, f"There is no project with ID {project_id}")