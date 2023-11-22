import spacy
import numpy as np
import nltk
import gensim
import numpy as np

from nltk.data import find
from search_scraper import * 


# find and load model 
nltk.download('word2vec_sample')
word2vec_sample = str(find('models/word2vec_sample/pruned.word2vec.txt'))
model = gensim.models.KeyedVectors.load_word2vec_format(word2vec_sample, binary=False)


LINE_LENGTH = 10
VOWELS  = ('a', 'e', 'i', 'o', 'u')


# define sentence structures with placeholders for parts of speech
SENTENCE_TEMPLATES = {
    'simple': ['NOUN', 'VERB'],
    'simple-with-adj': ['ADJ', 'NOUN', 'VERB'],
    'compound': ['NOUN', 'VERB', 'NOUN'],
    'interrogative': ['ADV', 'VERB', 'NOUN', 'VERB'],
    'complex': ['ADV', 'VERB', 'NOUN', 'CCONJ', 'ADV', 'VERB'],
    'exclamatory': ['INTJ', 'VERB', 'NOUN', 'PUNCT'],
    'imperative': ['VERB', 'NOUN', 'PUNCT']       
}


nlp = spacy.load('en_core_web_lg')


class GrammarProcessor():
    """
    Handle all grammar and semantic relations for poetry generation. 
    """
    def __init__(self, table, inspiring_text):
        self.table = table
        self.related_words = {}
        self.build_related_words(inspiring_text)

    def build_related_words(self, inspiring_text):
        """ 
        Find words related to inspiring text using a trained word2vec model
        which finds the top 20 closest vectors. I found this model to return
        better results than the SpaCy vector model. Related words are then 
        added to a list associated with their POS. 
        """
        for token in nlp(inspiring_text):
            word = token.text
            try:
                near_syn = [element[0] for element in \
                            model.most_similar(positive=[word], topn = 20)]
            except KeyError: # model not trained for those words
                near_syn = [word]
            doc = nlp(' '.join(near_syn))
            for syn in doc: 
                syn_pos = syn.pos_
                pos_list = self.related_words.get(syn_pos)
                if pos_list is None:
                    self.related_words[syn_pos] = [syn.text]
                else: 
                    pos_list.append(syn.text)

    def write_new_line(self):
        """
        First method of line writing, based on POS probabilites handled in the 
        CSV frequency file. Uses frequencies as weighted probabilities to 
        build POS sequences filled by words from a token map. 
        """
        line_length = LINE_LENGTH + np.random.randint(-2,2)

        current_pos = self.table.get_next_pos('START')

        # don't start with punctuation or spaces
        while current_pos == 'PUNCT' or current_pos == 'SPACE':
            current_pos = self.table.get_next_pos('START')
        
        # add additional words 
        token_list = self.table.get_tokens_for_pos(current_pos)
        if self.related_words.get(current_pos) is not None:
            token_list += list(self.related_words.get(current_pos))

        line = [self.table.get_random_token_for_pos(current_pos)]

        while len(line) <= line_length:
            next_pos = self.table.get_next_pos(current_pos)

            # don't add punctuation or spaces in the middle 
            while next_pos == 'PUNCT' or next_pos == 'SPACE': 
                next_pos = self.table.get_next_pos(current_pos)
            current_pos = next_pos

            # add additional words 
            token_list = self.table.get_tokens_for_pos(current_pos)
            if self.related_words.get(current_pos) is not None and len(token_list) != 0:
                token_list += list(self.related_words.get(current_pos))

            # randomly choose next word from token list
            next_word = np.random.choice(token_list)
            line.append(next_word)
        
        new_line = ' '.join(line)
        self.check_articles(new_line)
        return f'{new_line.capitalize()},'

    def craft_sentence(self, structure):
        """
        'Craft' sentence using sentence structure template constant above. 
        These POS sequences were put together after studying grammatical 
        constructions. Words for each POS are chosen randomly, but are pulled
        from the input text and scraped poems. 
        """
        sentence_template = SENTENCE_TEMPLATES[structure]
        sentence = []

        for pos in sentence_template:
            words = list(self.table.get_tokens_for_pos(pos))
            related_words = self.related_words.get(pos)
            if related_words is not None: 
                words += list(related_words) 
            if words:
                word = np.random.choice(words)
                sentence.append(word)

        constructed_sentence = ' '.join(sentence)

        # change ending punctuation based on sentence type 
        if structure == 'interrogative': 
            punct = '?'
        else:
            punct = ','

        return constructed_sentence.capitalize() + punct

    def check_articles(self, line):
        """ 
        Helper method to change 'a' to and 'an' if it precedes a token
        beginning with a vowel or change 'an' to 'a' if it precedes a token
        beginning with a consonant. 
        """
        tokens = nlp(line)
        prev = ''
        for token in tokens: 
            if prev == 'a' and token.lower_.startswith(VOWELS):
                line = line.replace('a ','an ')
            elif prev == 'an' and not token.lower_.startswith(VOWELS):
                line = line.replace('an ','a ')
            prev = token.lower_
        return line

    def reformat_poem(self, poem):
        """
        Reformat poem to correct capitalization that may have been changed
        (lowercase i or proper nouns) and change punctuation. 
        """
        for line in poem: 
            doc = nlp(line)

            for token in doc: 
                if token.text == 'i' or token.pos_ == 'PROPN':
                    capitalized = token.text.capitalize()
                    line = line.replace(token.text, capitalized)

            if line[-1] != ',' or line[-1] != '?':
                line += ',' # end of each line should have a comma 

        last_line = poem[-1]
        last_line = last_line.replace(',','.') # last line should end in .

    def generate_poem(self, num_lines):
        """
        With equal probability, add a random line (using POS freqencies) or a 
        crafted word (using set sentence structures from above templates). 
        Check capitalization and reformat before returning the poem. 
        """
        poem = []
        for _ in range(num_lines):
            type_of_line = np.random.choice(['random', 'crafted'], p=[0.5,0.5])
            if type_of_line == 'random':
                poem.append(self.write_new_line())
            else: 
                structure = np.random.choice(tuple(SENTENCE_TEMPLATES.keys()))
                poem.append(self.craft_sentence(structure))
        self.reformat_poem(poem)
        return poem

    def swap_word_in_pos(self, line, pos):
        """
        Replace a randomly selected word in the line with an entirely random
        word with the same part of speech. 
        """
        doc = nlp(line)
        nouns = [token.text for token in doc if token.pos_ == pos]
        if len(nouns) == 0: 
            return line
        to_swap = np.random.choice(nouns)
        replace_with = np.random.choice(self.related_words.get(pos))
        return line.replace(to_swap, replace_with)

    def mutate_grammar(self, poem):
        """
        With 60% probability, mutate the grammar of a line by rewriting a line 
        or making a swap for nouns, verbs, or adjective. After mutating, 
        recalculate the poem's fitness. 
        """
        mutated_lines = [] 
        for line in poem.lines:
            mutate = np.random.choice([True, False], p=[0.6,0.4])
            if mutate:
                mutation = np.random.randint(0,2)
                if mutation == 0: # replace line 
                    structure = np.random.choice(tuple(SENTENCE_TEMPLATES.keys()))
                    line = self.craft_sentence(structure)
                    line = self.check_articles(line).capitalize()
                elif mutation == 1: # swap noun 
                    line = self.swap_word_in_pos(line, 'NOUN')
                elif mutation == 2: # swap verb 
                    line = self.swap_word_in_pos(line, 'VERB')
                else: # swap adjective
                    line = self.swap_word_in_pos(line, 'ADJ')
            mutated_lines.append(line)
        poem.lines = mutated_lines
        poem.calculate_fitness() # recalculate fitness after mutated 
