from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import json

def construct_ai_prompt(chat: list[dict[str, str]], patent: dict) -> str:

    # First, define templates. TODO this should be extracted elsewhere and choice of template made configurable for easy experimentation.
    sys_msg_template = """
    You are a helpful assistant to a patent lawyer. The lawyer wants your help understanding a patent.
    Answer the lawyer's questions about the patent in 300 words or less. Cite text from the patent in quotes in your answer. If you don't know the answer, just say that you don't know. 
    Don't try to make up an answer. If you are uncertain about any part of your answer, say so. 

    Use the following information in thinking through your answer. First, the patent is delimited by triple backticks. Second, the words that appear uniquely in each independent claim are
    given in a JSON delimited by triple backticks. For example, independent claim 1 has key '1' in the JSON, and its values are all words that appear only in independent claim 1 and its
    dependent claims.

    Patent: 
    ```
    {patent}
    ```
    Words Unique to Each Independent Claim and Its Dependent Claims:
    ```
    {unique_words}
    ```
    """

    sys_msg_prompt_template = SystemMessagePromptTemplate.from_template(sys_msg_template)

    human_template = """The lawyer's question is delimited with triple backticks.

    Lawyer's question: '''{question}'''"""

    human_msg_prompt_template = HumanMessagePromptTemplate.from_template(human_template)

    # Define list of messages to be input to AI. PromptTemplate entries don't yet have values filled in; that will happen later.
    messages = [sys_msg_prompt_template]
    # Append each previous message to the chat.
    for i, msg in enumerate(chat):

        if i == len(chat) - 1:
            # Last chat message gets special treatment as a HumanMessagePromptTemplate with values to fill in.
            messages.append(human_msg_prompt_template)
            continue

        messages.append(AIMessage(content=msg['msg']) if msg['source'] == 'ai' else HumanMessage(content=msg['msg']))


    # chat_prompt_template = ChatPromptTemplate.from_messages([sys_msg_prompt_template, human_msg_prompt_template])
    chat_prompt_template = ChatPromptTemplate.from_messages(messages)

    patent_as_string = json.dumps(patent)
    question = chat[-1]
    assert question['source'] == 'user', \
        f'Attempting to construct an AI prompt when last message was from `{question["source"]}`. Needs to be from `user`.'
    question_txt = question['msg']

# TODO Define unique_word_lists
    # Get a chat completion from the formatted messages.
    # Both page_content and 'source' key of metadata are injected into prompt in document QA. Formatting still unclear. For now just passing page_content because only have single doc.
    chat_prompt = chat_prompt_template.format_prompt(question=question_txt, 
                                                     patent=patent_as_string, 
                                                     unique_words=json.dumps(unique_word_lists)).to_messages()
    chat_prompt


def generate_ai_response(prompt: str) -> str:
    chat = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)