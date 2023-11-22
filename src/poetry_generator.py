import numpy as np
import spacy

from poem_scraper import PoemScraper
from grammar_processor import GrammarProcessor
from poetic_manager import PoeticManager
from poem import Poem
from evaluation import * 


nlp = spacy.load('en_core_web_lg')


NUM_INSPIRING_POEMS = 10


class PoetryGenerator():
    """
    Runs genetic algorithm to generate poetry based on an input text while 
    considering evaluation metrics in an evaluation file.  
    """
    def __init__(self):
        self.poems = []
        self.scraper = PoemScraper()

    def compile_inspiring_set(self, inspiring_text, num_lines):
        """
        Compile an inspring set by adding the inspiring text as a query in the
        scraper. That data is then sent to the GrammarProcessor to write lines
        and build a set of poems to run a genetic algorithm on. 
        """
        self.scraper.add_query(inspiring_text)
        self.grammar_processor = GrammarProcessor(self.scraper.pos_sequence, inspiring_text)
        self.poetic_manager = PoeticManager(get_related_words(inspiring_text))

        for _ in range(NUM_INSPIRING_POEMS):
            lines = self.grammar_processor.generate_poem(num_lines)
            self.poems.append(Poem(inspiring_text=inspiring_text, lines=lines))
        return self.scraper.get_all_authors()
    
    def crossover(self, poem1, poem2, inspiring_text):
        """ 
        From all lines, find the half of the lines that are most similar to
        the inspiring text.
        """
        all_lines = poem1.get_lines() + poem2.get_lines()
        closest_lines = get_half_closest(inspiring_text, all_lines)
        return Poem(inspiring_text=inspiring_text, lines=closest_lines)
    
    def fittest_half(self, poems):
        """ 
        Returns the fittest half of poems. Fitness is stored in each Poetry
        object to prevent the evaluation from running more than required. 
        """
        sorted_poems = sorted(poems, key = lambda x : x.get_fitness(), reverse=True)
        return sorted_poems[:int(len(poems)/2)]
    
    def genetic_algo(self, inspiring_text):
        """ 
        Iterate over the number of recipes, choosing two poems randomly based 
        on their fitness as a weighted probability. Cross their lines and 
        call for mutation on the new poem. At the end, take the top half of the
        new and old poems and store it. 
        """
        new_poems = []
        # chooses two poems based on probability corresponding to their fitness
        fitnesses = [poem.get_fitness() for poem in self.poems]
        p = np.array(fitnesses)
        p /= sum(p)

        for _ in range(len(self.poems)):
            # keep getting probabilities do not sum to 1 error
            # TODO fix this issue
            poem1, poem2 = np.random.choice([i for i in range(len(self.poems))], p=p, size=2, replace=False)

            # cross the poems together
            new_poem = self.crossover(self.poems[poem1], self.poems[poem2], inspiring_text)

            # call for potential mutation
            new_poem.mutate(self.grammar_processor, self.poetic_manager)
            new_poems.append(new_poem)

        # keep top 50% of old poems and newly generated poems for next generation
        self.poems = self.fittest_half(self.poems) \
            + self.fittest_half(new_poems)   

    def run_genetic_algo(self, generations, inspiring_text, num_lines=10):
        """ 
        Run genetic algorithm for the # of generations that the user inputs.
        """
        self.compile_inspiring_set(inspiring_text, num_lines)
        for i in range(generations):
            print(f"Running genetic algorithm for generation {i + 1}")
            self.genetic_algo(inspiring_text)  
        
    def get_top_poem(self):
        """
        At any point, sort the poems by their fitness and return the fittest
        poem. Add that poem to a JSON file for future reference. 
        """
        sorted_poems = sorted(self.poems, key=lambda x : x.get_fitness(), reverse=True)
        sorted_poems[0].append_to_json_file('fittest_poems.json')
        return sorted_poems[0]
    
    def get_authors(self):
        """
        Get all authors used during generation. 
        """
        return self.scraper.get_all_authors()
