## About 'Learning from the Best: Poetry Generation!'
My system revolves heavily on studying the world around it. Poetry generation
works by requesting an input from the user, which is then used to query
PoetryFoundation.org for related works. All scraped poems are stored in a CSV
file for future reference. Another CSV file stores POS frequency mappings. 
After building this knowledge base, the program builds an inspiring set of 10 
poems, using the scraped data to inform its decisions. The system then runs a 
genetic algorithm for 5 generations using two different metrics for meaning and
a metric for line dissimilarity within a poem. Mutation in the genetic algorithm
alter the poeticness or grammaticality of the poem. 

Additionally, this system restricts the definition of a poem to text that is 
grammatically correct, poetic in some way, and has meaning. This definition is
used in this system to guide the fitness metric in src/evaluation.py and the
mutations run during the genetic algorithm. 


## Setup 
This interface runs on Flask. To run the code, run the file src/app.py, then 
follow the port that Flask directs you to. It should run on 8000. 

Before doing that, set up a virtual environment:

python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python

Then install the following: 

pip install bs4
pip install sentence_transformers
pip install spacy
python3 -m spacy download en_core_web_lg
pip install pronouncing 
pip install gensim

## Reflection
This system was probably the most challenging thing that I've worked on while
studying computer science, both because of the level of work involved, but also
the lack of a clear endpoint. I kept thinking of ways to make my system smarter,
which ended up muddying my overall progress, so wrapping everything up was 
a sprint. I loved diving into the academic research into the field, but it made
me want to broaden my scope beyond what I am capable of as an individual. 

## Research 
I read a lot for this assignment! The following works guided me the most 

### An evolutionary algorithm approach to poetry generation (Manurung 2003)
This was a PhD thesis on poetry generation. Manurung restricts his defition
of a poem, which I encorporated in my system. He also specifically looked for
meaningfulnes, poeticness, and grammaticality. 


### Poetry Generation with PoeTryMe (Oliveira & Cardoso)
I adapted the architecture used in this system. This system build a
GrammarProcessor and a RelationsManager to meaningfully and correctly express 
semantic relations. While I couldn't build something as sophisticated, I paid
close attention to semantic relations and built a (cruder) GrammarProcessor. 


### Full-FACE Poetry Generation (Colton et. al.)
This system leverage WordNet in a really interesting way, which inspired me 
to work with WordNet for semantic relations. 