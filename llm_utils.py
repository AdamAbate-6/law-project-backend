import json
import re
import yaml
import os

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
    SystemMessage,
    PromptValue
)

# TODO Need to learn about more secure ways of doing auth.
with open('./api_keys.yaml', 'r') as f:
    __keys = yaml.safe_load(f)

os.environ["OPENAI_API_KEY"] = __keys['openai']
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../law-project-service-account.json'


def construct_ai_prompt(chat: list[dict[str, str]], patent: dict) -> PromptValue:

    # First, define templates. TODO this should be extracted elsewhere and choice of template made configurable for easy experimentation.
    sys_msg_template = """
    You are a helpful assistant to a patent lawyer. The lawyer wants your help understanding a patent. Address him or her in the second person.
    Answer the lawyer's questions about the patent in 150 words or less. Cite text from the patent in quotes in your answer. If you don't know the answer, just say that you don't know. 
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

    human_template = """The lawyer's question is delimited with triple backticks. Answer the question in fewer than 150 words.

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

    # Remove MongoDB _id field. It is unserializable, and while we could convert it to a string before serializing,
    #  it is not helpful to have in the prompt, so no point.
    patent_for_prompt = patent.copy()
    if '_id' in patent_for_prompt.keys():
        patent_for_prompt.pop('_id')
    patent_as_string = json.dumps(patent_for_prompt)

    # Validate last input in message history as being from user.
    question = chat[-1]
    assert question['source'] == 'user', \
        f'Attempting to construct an AI prompt when last message was from `{question["source"]}`. Needs to be from `user`.'
    question_txt = question['msg']

    unique_word_lists = get_unique_words_per_indep_claim(patent['claims'])

    # Get a chat completion from the formatted messages.
    # Both page_content and 'source' key of metadata are injected into prompt in document QA. Formatting still unclear. For now just passing page_content because only have single doc.
    chat_prompt = chat_prompt_template.format_prompt(question=question_txt, 
                                                     patent=patent_as_string, 
                                                     unique_words=json.dumps(unique_word_lists)).to_messages()
    return chat_prompt


def generate_ai_response(chat_prompt: PromptValue) -> str:
    """Given a prompt, generate the AI's response.

    Args:
        chat_prompt (PromptValue): A LangChain prompt, e.g. as returned from ChatPromptTemplate.format_prompt()

    Returns:
        str: The AI response
    """

    chat = ChatOpenAI(temperature=0)
    result = chat.generate([chat_prompt])
    return result.generations[0][0].text


def get_unique_words_per_indep_claim(claims: str) -> dict[str, list[str]]:
    """Identify the independent claims and get the word sets unique to each independent claim and its dependent claims.

    Args:
        claims (str): String of claims; it is assumed that claims are separated by three triple underscores.

    Returns:
        dict[str, list[str]]: Dictionary whose keys are independent claim numbers and whose values are the words 
    unique to each independent claim and its dependent claims 
    """

    claims_list = claims.split('\n     \n     \n       ')

    # Identify which entries of claims_list are independent claims.
    dep_claim_pattern = 'of\s+claim'
    indep_claim_indices = [i for i, c in enumerate(claims_list) if re.search(dep_claim_pattern, c) is None]

    # Make a dictionary whose keys are independent claim numbers and whose values are the 1) the text of those independent claims,
    #  and 2) the text of all dependent claims of each independent claim.
    indep_claims_and_their_dependents = dict()
    for i, c in enumerate(claims_list):
        if i in indep_claim_indices:
            # Is independent, so start an entry in indep_claims_and_their_dependents.
            # First numeric appearing in claim should be the claim number.
            claim_num = re.search('\d+', c).group()
            assert claim_num is not None, 'Could not find independent claim number.'
            indep_claims_and_their_dependents[claim_num] = c
        else:
            # Is dependent, so group to most recent independent claim since that is what dependent claim refers to.
            processed_indep_claim_indices = list(indep_claims_and_their_dependents.keys())
            processed_indep_claim_indices.sort()
            latest_indep_claim_index = processed_indep_claim_indices[-1]
            indep_claims_and_their_dependents[latest_indep_claim_index] = indep_claims_and_their_dependents[latest_indep_claim_index] + c

    # Get set of unique words for each independent claim and its dependent claims.
    word_sets = {ic_num: get_word_set(claims_text) for ic_num, claims_text in indep_claims_and_their_dependents.items()}

    # For each independent claim and its dependents, get list of words that appears only in them.
    unique_word_lists = dict()
    for ic_num, word_set in word_sets.items():
        unique_words = word_set
        for other_ic_num, other_word_set in word_sets.items():
            if ic_num == other_ic_num:
                continue
            unique_words = unique_words - other_word_set
        unique_word_lists[ic_num] = list(unique_words)

    return unique_word_lists


def get_word_set(multi_word_string: str) -> set:
    """Split a string into lower cased words with numerics not included and remove punctuation. Then return only the unique words.

    Args:
        multi_word_string (str): What it sounds like

    Returns:
        set: Set of unique un-punctuated words
    """
    # Assume words are split by spaces.
    words = multi_word_string.split(' ')

    # Remove punctuation and new-lines.
    def remove_chars(word: str, chars_to_remove: list):
        for char in chars_to_remove:
            word = word.replace(char, '')
        return word
    
    words = [remove_chars(word, ['.', ';', ',', '(', ')', ':', '\n']) for word in words]

    # Get rid of any length-0 or length-1 words (e.g. '', 'a') and any numerics (e.g. '10'). Also lower-case everything.
    words = [word.lower() for word in words if len(word) > 1 and not word.isnumeric()]
    
    # Remove any duplicates by using set().
    return set(words)