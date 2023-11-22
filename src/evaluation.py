import spacy 
import numpy as np

from nltk.corpus import wordnet
from sentence_transformers import SentenceTransformer, util


# load sentence_model
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')


nlp = spacy.load('en_core_web_lg')


def measure_meaning(inspiring_text, title):
    """
    Using spaCy's similarity function, return the average of the similarity
    of each line to the inspiring text 
    """
    doc = nlp(inspiring_text)
    return doc.similarity(nlp(title))

def measure_target_closeness(inspiring_text, poem):
    """
    Using SentenceTransformers, measure the closeness of the poem to the 
    input text using cosine similarity computations for each line. 
    """
    # compute embeddings
    target_embedding = sentence_model.encode([inspiring_text], convert_to_tensor=True)
    poem_embeddings = sentence_model.encode(poem, convert_to_tensor=True)

    # compute cosine-similarities for each line of poem with inspiring_text
    cosine_scores = util.cos_sim(target_embedding, poem_embeddings)
    cosine_scores = [cosine_scores[0][i].float() for i in range(len(poem))]

    cosine_scores = sorted(cosine_scores, reverse=True)

    # return the average
    return sum(cosine_scores) / len(cosine_scores)


def get_half_closest(inspiring_text, lines):
    """
    Using SentenceTransformers, sort lines based on their closeness to the 
    inspiring text and return the top half closest lines.  
    """
    target_embedding = sentence_model.encode([inspiring_text], convert_to_tensor=True)
    line_embeddings = sentence_model.encode(lines, convert_to_tensor=True)

    cosine_scores = util.cos_sim(target_embedding, line_embeddings)

    cosine_scores = cosine_scores[0]

    # add each line to a list with its cosine similarity score
    lines_with_scores = []
    for i in range(len(cosine_scores)):
        lines_with_scores.append([cosine_scores[i], i])

    # sort list by the highest cosine similarity score
    lines_with_scores = sorted(lines_with_scores, key=lambda x: x[0], reverse=True)
    closest_lines = [lines[i] for score, i in lines_with_scores]
    half = int((len(lines)/2))
    return closest_lines[:half]


def get_related_words(word):
    """ 
    Helper function to get synonyms, hypernyms, and hyponyms of a word. 
    """
    synonyms = set()
    synset = wordnet.synsets(word)
    for syn in synset:
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
        for hypernym in syn.hypernyms():
            for lemma in hypernym.lemmas():
                synonyms.add(lemma.name())
        for hyponym in syn.hyponyms():
            for lemma in hyponym.lemmas():
                synonyms.add(lemma.name())
    return synonyms


def get_keywords(text):
    """
    Helper function to get keywords of a text. 
    """
    doc = nlp(text)
    keywords = [token.text for token in doc if not token.is_stop 
                and not token.is_punct]
    return keywords


def get_words_related_to_text(inspiring_text):
    """
    Pulls keywords from the inspiring text and returns a list of all related
    words (synonyms, hyponyms, hypernyms).
    """
    doc = nlp(inspiring_text)
    keywords = [token.text for token in doc if not token.is_stop 
                and not token.is_punct]
    related_words = []
    for word in keywords: 
        related_words += list(get_related_words(word))
    return list(set(related_words))


def measure_keywords(inspiring_text, poem):
    """ 
    Using the inspiring text, get the keywords and related words (synonyms, 
    hypernyms, hyponyms). Check how often these are used each line of poetry.
    """
    doc = nlp(inspiring_text)
    keywords = [token.text for token in doc if not token.is_stop 
                and not token.is_punct]
    related_words = []
    for word in keywords: 
        related_words += list(get_related_words(word))
    related_words += keywords
    related_words = get_words_related_to_text(inspiring_text)
    measurement = 0
    for line in poem: 
        line_doc = nlp(line)
        line_count = 0
        for token in line_doc: 
            if token.text in related_words: 
                line_count += 1
        measurement += (line_count)
    return measurement / len(poem)


def measure_dissimilarity(poem):
    """
    Using SentenceTransformers, embed each line and get a similarity score for 
    each pair of lines in the poem. Use similarity score to calculate a 
    dissimilarity score 
    """
    embeddings = [sentence_model.encode(line.lower(), convert_to_tensor=True) \
                  for line in poem] # embed each line in poem 
    dissimilarities = []

    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            # get similarity score from each pair of line embedding 
            cosine_similarity = util.cos_sim(embeddings[i], embeddings[j])
            # dissimilarity is the difference 
            dissimilarity_score = 1 - cosine_similarity
            dissimilarities.append(dissimilarity_score)

    if dissimilarities:
        mean_dissimilarity = np.mean(dissimilarities) # 'normalize' 
    else:
        mean_dissimilarity = 0.0
    
    return mean_dissimilarity



def get_fitness(inspiring_text, poem, meaning_coef=1, keyword_coef=1, 
                dissimilarity_coef=10):
    """
    Using the above metrics, use their coefficients to weight their importance
    and return the sum of their weights. 
    """
    meaning_comp = measure_target_closeness(inspiring_text, poem) * meaning_coef
    keyword_comp = measure_keywords(inspiring_text, poem) * keyword_coef
    dissimilarity_comp = measure_dissimilarity(poem) * dissimilarity_coef
    meaning_string = "{:.8f}".format(meaning_comp)
    print(f"meaning: {meaning_string}, keyword: " + \
            f"{round(keyword_comp, 8)}, dissimilarity: " + \
            f"{round(dissimilarity_comp, 8)}")
    return meaning_comp + keyword_comp + dissimilarity_comp
