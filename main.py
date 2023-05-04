from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware  # Cross origin resources sharing


from models import (
    UserDataFromClient,
    UserDataToClient, 
    UserDataEditsFromClient,
    ProjectDataFromClient,
    ProjectDataToClient, 
    PatentDataToClient,
    UserInput,
    AiResponse)
from database import (
    fetch_one_user,
    fetch_one_project, 
    fetch_one_patent,
    create_user,
    create_project,
    create_patent,
    modify_user,
    modify_project_chat,
    modify_project_patents)
from big_query_utils import query_patent
from llm_utils import (
    construct_ai_prompt, 
    generate_ai_response)



app = FastAPI()

# An "origin" is any combination of URL and port. 
# Allow resource sharing between React (running on port 3000) and FastAPI (running on some different port)
# NOTE: If you don't get the origins *exactly right* (e.g. if you make it https when it is supposed to be http),
#  you will see errors like this in browser debugging tools: 
#      Access to XMLHttpRequest at 'http://localhost:8000/api/user' from origin 'http://localhost:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
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

USER_ID_QUERY = Query(max_length=24, min_length=24, regex='^[a-z0-9]+$', description='_id field of entry in `projects` collection of MongoDB')
PROJECT_ID_QUERY = Query(max_length=24, min_length=24, regex='^[a-z0-9]+$', description='_id field of entry in `users` collection of MongoDB')

def reformat_mongodb_id_field(response: dict) -> dict:
    """
    MongoDB ObjectID field cannot be encoded into JSON for transmission back to frontend. Convert to string.
    :param response: Dictionary containing a MongoDB document.
    """
    if '_id' in response:
        # For _id field of MongoDB entry...
        # 1) Have to convert _id field from bson.ObjectId to string.
        # 2) Have to put into differently named field. _id is not returned to the client if response_model is a BaseModel (as opposed to returning a dict).
        response['mongo_id'] = str(response.pop('_id'))
    return response

# ==========================================================
@app.get("/")
def read_root():
    return {'ping': 'pong'}


@app.get("/api/user/{email}", response_model=UserDataToClient)
async def get_user_by_email(email: str):
    db_response = await fetch_one_user(email)
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(404, f"There is no user with email {email}")


@app.get("/api/project/{project_id}", response_model=ProjectDataToClient)
async def get_project_by_id(project_id: str):
    db_response = await fetch_one_project(project_id)
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(404, f"There is no project with ID {project_id}")

# ==========================================================

@app.post("/api/user", response_model=UserDataToClient, status_code=status.HTTP_201_CREATED)
async def post_user(user_entry: UserDataFromClient):
    db_response = await create_user(user_entry.dict())
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(400, "Something went wrong / bad request")


@app.post("/api/project/", response_model=ProjectDataToClient, status_code=status.HTTP_201_CREATED)
async def post_project(project_entry: ProjectDataFromClient):
    db_response = await create_project(project_entry.dict())
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(400, "Something went wrong / bad request")

@app.post("/api/patent/{patent_spif}", response_model=PatentDataToClient)
async def post_patent(patent_spif: str, api_response: Response):
    # First, see if patent already exists in DB.
    db_response = await fetch_one_patent(patent_spif)
    if db_response:
        api_response.status_code = status.HTTP_200_OK
        return reformat_mongodb_id_field(db_response)
    else:
        # Patent doesn't exist, so query BigQuery for it.
        patent_data = query_patent(patent_spif)
        db_response = await create_patent(patent_data)
        if db_response:
            api_response.status_code = status.HTTP_201_CREATED
            return reformat_mongodb_id_field(db_response)
        raise HTTPException(400, "Something went wrong during patent creation in DB / bad request")
        

# ==========================================================

@app.put("/api/user/{user_id}", response_model=UserDataToClient)
async def put_user_modifications(user_id: str, user_entry: UserDataEditsFromClient):

    user_edits = {k: v for k, v in user_entry.dict().items() if v is not None}
    response = await modify_user(user_id, updated_user=user_edits)

    if response:
        return reformat_mongodb_id_field(response)
    
    raise HTTPException(400, f'Something went wrong modifying user {user_id}.')


@app.put("/api/project/{project_id}", response_model=ProjectDataToClient)
async def put_project_modifications(project_id: str, user_input: UserInput):

    # Get the project record that needs to be updated.
    project_entry = await fetch_one_project(project_id)

    # Check whether chat should be updated with contents of user_input.
    response1 = None
    if user_input.msg is not None:

        # First, get the part of the project chat corresponding to this user.
        user_id = user_input.user_id
        chat = project_entry['chat']
        user_chat = chat[user_id]

        # Second, put the new message from the user into the user's chat.
        # new_chat_msg = ChatEntry.parse_obj({'source': 'user', 'msg': user_input.msg})
        new_chat_msg = {'source': 'user', 'msg': user_input.msg}
        user_chat.append(new_chat_msg)

        # Third, update the dictionary of project chats with the updated user chat.
        chat[user_id] = user_chat

        # Finally, update the project entry in MongoDB with the new chat.
        response1 = await modify_project_chat(project_id, updated_chat=chat)

    response2 = None
    if user_input.patent_number is not None and user_input.patent_office is not None:
        
        # First, get the part of the project patents corresponding to this user.
        user_id = user_input.user_id
        patents = project_entry['patents']
        user_patents = patents[user_id]

        # Second, put the new patent from the user input into the user's list of patents.
        # new_chat_msg = ChatEntry.parse_obj({'source': 'user', 'msg': user_input.msg})
        new_patent = {'office': user_input.patent_office, 'number': user_input.patent_number}

        # Check if patent already exists in user's list of patents.
        patent_exists = any([p == new_patent for p in user_patents])
        if patent_exists:
            # It exists, so just return project data without modifications.
            response2 = project_entry 

        else:
            # Patent not in user's list of patents within project, so put it there. 
            user_patents.append(new_patent)

            # Third, update the dictionary of project patents with the updated user patent list.
            patents[user_id] = user_patents

            # Finally, update the project entry in MongoDB with the new patent list.
            response2 = await modify_project_patents(project_id, updated_patents=patents)

    response = None
    if response1 and response2:  # Both chat and patents were modified, so only trust return of latter since it was executed second.
        response = response2

    elif response1:
        response = response1

    elif response2:
        response = response2

    if response:
        return reformat_mongodb_id_field(response)
    
    raise HTTPException(400, 'Something went wrong.')

# ==========================================================
@app.get("/api/ai", response_model=AiResponse)
async def get_ai_response(project_id: Annotated[str, PROJECT_ID_QUERY], 
                          user_id: Annotated[str, USER_ID_QUERY]):

    # Get the chat (list of dicts with 'source' and 'msg' keys) for this project and user.
    project_entry = await fetch_one_project(project_id)
    chat = project_entry['chat']
    user_chat = chat[user_id]

    # Get the patent (TODO design prompt to allow more than one patent and then fetch all patents whose metadata is in project_entry['patents'][user_id]).
    patent_metadata = project_entry['patents'][user_id][0]
    patent_spif = patent_metadata['office'] + patent_metadata['number']
    patent = await fetch_one_patent(patent_spif)

    # TODO generate AI response based on the above.
    # ai_msg = 'This is a test AI response!'
    prompt = construct_ai_prompt(user_chat, patent)
    ai_msg = generate_ai_response(prompt)

    # Put the AI-generated message in the user_chat list, and then make that updated list 
    #  the entry for this user in the project. Update the DB accordingly.
    # Yes, I know, this is a GET endpoint, but I am ok updating the DB in it because in 
    #  PUT and POST typically imply the client is sending data to the backend. Here the
    #  backend (i.e. the AI) is the one generating the data.
    new_chat_msg = {'source': 'ai', 'msg': ai_msg}
    user_chat.append(new_chat_msg)
    chat[user_id] = user_chat
    response = await modify_project_chat(project_id, updated_chat=chat)
    if not response:
        raise HTTPException(400, 'Something went wrong.')

    data = AiResponse.parse_obj({'msg': ai_msg})
    return data