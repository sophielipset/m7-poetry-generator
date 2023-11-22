import os
import json
import numpy as np

from evaluation import * 
from search_scraper import * 


class Poem(): 
    """
    Class representation of a poem, including calling on fitness calculations 
    and mutations. 
    """
    def __init__(self, inspiring_text, lines=[]):
        self.lines = lines
        self.inspiring_text = inspiring_text
        self.title = ''
        self.calculate_fitness()

    def calculate_fitness(self):
        """ 
        Calculate the fitness of the poem. 
        """
        if len(self.lines) > 0:
            self.fitness = get_fitness(self.inspiring_text, self.lines)
        else:
            self.fitness = 0 

    def mutate(self, grammar_processor, poetic_manager):
        """
        Selects for mutation 60% of the time, then selects either poetic or 
        grammatical mutation with set probability. 
        """
        mutate = np.random.choice([True, False], p=[0.6,0.4])
        if mutate:
            mutation = np.random.choice(['grammar', 'poeticness'], p=[0.4,0.6])
            if mutation == 'grammar': 
                grammar_processor.mutate_grammar(self)
            else: 
                poetic_manager.mutate_poeticness(self)

    def write_title(self):
        """
        Write poem title using related words (from evaluation file), then use
        Google search results to decide which word to use. 
        """
        related_words = get_words_related_to_text(self.inspiring_text)
        title_length = np.random.randint(1,4)
        title = [np.random.choice(related_words).replace('_', ' ')]

        while len(title) < title_length:
            word1, word2 = np.random.choice(related_words, size=2)
            next_word = get_next_word(' '.join(title),
                                      word1.replace('_', ' '), 
                                      word2.replace('_', ' '))
            title.append(next_word.replace('_', ' '))

        self.title =  ' '.join(title).title()

    def get_lines(self):
        """
        Get lines of poem, formatting last line. 
        """
        self.lines[len(self.lines) - 1] = self.lines[len(self.lines) - 1].replace(',','.')
        return self.lines

    def get_fitness(self):
        """
        Return poem's fitness
        """
        return self.fitness

    def append_to_json_file(self, file_path):
        """
        Write poem data to JSON file
        """
        self.write_title()
        formatted_poem = {
            'title': self.title,
            'poem': self.lines,
            'inspiring-text': self.inspiring_text,
        }

        # check if the file exists
        file_exists = os.path.exists(file_path)

        # load existing data or initialize with empty list if file doesn't exist
        existing_data = []
        if file_exists:
            with open(file_path, 'r') as json_file:
                existing_data = json.load(json_file)

        # append poem to the existing data
        existing_data.append(formatted_poem)

        # write the updated data back to the file
        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)

    def __str__(self):
        """
        String representation of a poem to be printed."""
        str_rep = f'--{self.title}--'
        for line in self.lines:
            str_rep += f'\n{line}'
        return str_rep