import pronouncing
import spacy
import gensim
import nltk
import numpy as np

from nltk.data import find
from nltk.corpus import wordnet


# load model 
nltk.download('word2vec_sample')
word2vec_sample = str(find('models/word2vec_sample/pruned.word2vec.txt'))
model = gensim.models.KeyedVectors.load_word2vec_format(word2vec_sample, binary=False)


nlp = spacy.load('en_core_web_lg')


# store CMU/pronouncing vowel phones 
VOWELS = ['AA', 'AE1', 'AE', 'AH0', 'AH1', 'AO', 'AW', 'AY', 
          'EH0', 'EH1', 'EH2', 'ER0', 'EY0', 'EY1', 
          'IH0', 'IH1', 'IH2', 'IY0', 'IY1',
          'OW0', 'OW1', 'OY',
          'UH0', 'UH1', 'UW0', 'UW1']


class PoeticManager():
    """ 
    Handles poeticness of each poem.
    """
    def __init__(self, words):
        self.words = words # a list of word tokens

    def add_alliteration_or_assonance(self, phone, line):
        """ 
        Takes in a phone (such as AH or P) and iterates through words in 
        the line, replacing with a similar word that matches the phone 
        """
        new_words = pronouncing.search(phone) # all words with matching phones
        new_line = []
        for word in line.split(): 
            if word not in new_words:
                try:
                    near_syn = [element[0] for element in \
                                model.most_similar(positive=[word], topn = 10)]
                except KeyError: # model not trained for those words
                    near_syn = word
                replace_with = set(new_words) & set(near_syn)
                # if there is an overlap with the set
                if len(replace_with) > 0:
                    new_line.append(np.random.choice(list(replace_with)))
                # edge case 
                else: 
                    new_line.append(word)
            else: 
                new_line.append(word)
        return ' '.join(new_line).capitalize()

    def add_alliteration_assonance_to_poem(self, lines):
        """
        For each line in the poem, add alliteration or assonance according to 
        the first phone of the first word in the line. 
        """
        new_poem = []
        for line in lines: 
            first_word = line.split()[0]

            try:
                phones = pronouncing.phones_for_word(first_word)[0]
            except: # edge case with numbers 
                second_word = line.split()[1]
                phones = pronouncing.phones_for_word(second_word)[0]

            first_phone = phones.split()[0]
            new_poem.append(self.add_alliteration_or_assonance(first_phone, line))
        return new_poem
    
    def alter_meter(self, line, word):
        """
        Takes in the meter of a word and tries to match the rest of the line 
        to the similar meter without disrupting the existing meaning.
        """
        word = word.strip(',').strip('?')
        try:
            new_meter = pronouncing.stresses_for_word(word)[0]
        except:
            return
        new_line = []
        matching_meter = pronouncing.search_stresses(new_meter)
        for word in line.split(): 
            if word not in matching_meter:
                try:
                    near_syn = [element[0] for element in \
                                model.most_similar(positive=[word], topn = 10)]
                except KeyError: # model not trained for those words
                    near_syn = word
                replace_with = set(matching_meter) & set(near_syn)
                # if there is an overlap with the set
                if len(replace_with) > 0:
                    new_line.append(np.random.choice(list(replace_with)))
                # edge case 
                else: 
                    new_line.append(word)
            else: 
                new_line.append(word)
        return line
    
    def alter_meter_for_poem(self, lines):
        """
        For each line in the poem, alter meter according to a randomly chosen
        word in the line.
        """
        new_poem = []
        for line in lines: 
            # randomly choose line in word to guide meter of the line 
            random_word = np.random.choice(tuple(line.split())) 
            new_poem.append(self.alter_meter(line, random_word))
        return new_poem
    
    def get_related_words(self, word):
        """
        Get synonyms, hypernyms, and hyponyms for a word. 
        """
        synonyms = set()
        synset = wordnet.synsets(word)
        for syn in synset:
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().replace('_', ' '))
            for hypernym in syn.hypernyms():
                for lemma in hypernym.lemmas():
                    synonyms.add(lemma.name().replace('_', ' '))
            for hyponym in syn.hyponyms():
                for lemma in hyponym.lemmas():
                    synonyms.add(lemma.name().replace('_', ' '))
        return synonyms

    def select_word_with_near_rhyme(self, close_words, desired_last_word):
        """
        Expand search for rhyming words to near rhymes 
        """
        desired_last_word = desired_last_word.strip('.').strip(',')
        try: 
            phones = pronouncing.phones_for_word(desired_last_word)[0]
        except:
            return []
        last_phones = pronouncing.rhyming_part(phones).split()[:-1]
        near_rhymes = pronouncing.search(' '.join(last_phones))
        return set(close_words) & set(near_rhymes)
            

    def find_rhyming_synonym(self, word, desired_last_word, flipped=False):
        """
        For a word and desired rhyme, find a semantically close word to that 
        rhymes with the desired words.
        """
        rhyming_words = pronouncing.rhymes(desired_last_word)

        try:
            near_syn = [element[0] for element in \
                        model.most_similar(positive=[word], topn = 10)]
        except KeyError: # model not trained for those words
            near_syn = word

        common_words = set(rhyming_words) & set(near_syn)
        if len(common_words) == 0: 
            synonyms = self.get_related_words(word)
            common_words = self.select_word_with_near_rhyme(synonyms, 
                                                            desired_last_word)
            
        if len(common_words) == 0 and not flipped: 
            self.find_rhyming_synonym(word=desired_last_word, 
                                      desired_last_word=word, 
                                      flipped=True)
            return np.random.choice(tuple(near_syn))
        
        return next(iter(common_words), None)

    def change_line_to_rhyme(self, original_line, desired_rhyme):
        """
        Alter a line so that its end word rhymes with the desired line. 
        """
        # remove punctuation and split into a list
        original_words = original_line.split()
        rhyme_words = desired_rhyme.split()

        rhyming_synonym = self.find_rhyming_synonym(original_words[-1], rhyme_words[-1])

        if rhyming_synonym:
            original_words[-1] = rhyming_synonym

        altered_line = ' '.join(original_words)
        return altered_line
    
    def add_rhymes_for_poem(self, lines):
        """
        Add rhyming to poem, randomly choosing one line for the other lines to 
        rhyme with. 
        """
        new_poem = []

        # randomly choose line in poem to rhyme with 
        rhyming_line = np.random.choice(lines) 

        for line in lines: 
            new_poem.append(self.change_line_to_rhyme(line, rhyming_line))
        return new_poem

    
    def mutate_poeticness(self, poem): 
        """
        With 70% probability, mutate the poeticness of the poem, choosing with
        equal probability to add alliteration or assonance, alter the meter, or
        to add rhyming/near rhyming to the poem.
        """
        lines = poem.lines
        mutate = np.random.choice([True, False], p=[0.7,0.3])
        if mutate:
            mutation = np.random.randint(0,3)
            if mutation == 0: # add alliteration or assonance
                lines = self.add_alliteration_assonance_to_poem(lines)
            elif mutation == 1: # alter meter  
                lines = self.alter_meter_for_poem(lines)
            elif mutation == 2: # add rhyming or near rhymes
                lines = self.add_rhymes_for_poem(lines)
        poem.lines = lines
        return poem

