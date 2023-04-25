## Plans Per Use Case
### "How do claims x and y differ?"
Inputs are the above query and patent document(s) extracted from the vector DB
TODO:
* Try inputting patent as one doc
    * Experiment with different combinations of number, title, abstract, claims, description
* Chunking
    * Try alternatives to stuffing (i.e. map-reduce, refine, map-rerank) for combination of patent chunked into several different docs
    * Try different chunk overlaps
    * Try separating sections and individual claims into distinct chunks. May require manual doc creation from different selected columns and then regex over the claims column


### "Identify weak points in this patent"
Inputs are the above query, patent document(s) extracted from the vector DB, and case law document(s) extracted from the vector DB 