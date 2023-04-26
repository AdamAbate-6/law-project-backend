## Plans Per Use Case
### "How do claims x and y differ?"
Inputs are the above query and patent document(s) extracted from the vector DB
TODO:
* Try inputting patent as one doc
    * Experiment with different combinations of number, title, abstract, claims, description
    * Need to figure out how many characters average patent is and how that translates to input sequence lengths
* Try ChatGPT (i.e. gpt-3.5-turbo, as opposed to text-davinci-003 which is better than GPT-3 but lacks RLHF) with same setup as currently have
    * RESULT: Performing better. Oly tried with input of entire patent at once. TODO try with document chat over chat history https://python.langchain.com/en/latest/modules/chains/index_examples/chat_vector_db.html 
* Chunking
    * Try alternatives to stuffing (i.e. map-reduce, refine, map-rerank) for combination of patent chunked into several different docs
        * Will need to use free LLMs for map, combine, reduce operators
    * Try different chunk overlaps
    * Try separating sections and individual claims into distinct chunks. May require manual doc creation from different selected columns and then regex over the claims column



### "Identify weak points in this patent"
Inputs are the above query, patent document(s) extracted from the vector DB, and case law document(s) extracted from the vector DB 
TODO:
* 