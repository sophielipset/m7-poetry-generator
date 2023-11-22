import spacy
import numpy as np
import os 
import csv


nlp = spacy.load("en_core_web_sm")


class FrequencyMap():
    """
    FrequencyMap maps a key to its frequency, and is to be used entirely by 
    POSManager. This class is adapted from a Java class written for a Data 
    Structures in Spring 2022 by Sophie Lipset and Maryam Akramova. 
    """
    def __init__(self, element='', freq_map=None):
        if freq_map is None: 
            self.freq_map = dict()
        else:
            self.freq_map = freq_map # option to load map from CSV file
        if element != '':
            self.freq_map[element] = 1

    def keys(self):
        """ 
        Method to return all keys for the FrequencyMap dictionary
        """
        return self.freq_map.keys()

    def change_frequency(self, next_):
        """
        Method to change the frequency that an element appears. If the element 
        is not in dictionary yet, create new key for it with value of 1.
        """
        if next_ == '':
            return
        if next_ in self.freq_map.keys():
            self.freq_map[next_] = self.freq_map[next_] + 1 
        else: 
            self.freq_map[next_] = 1 
    
    def get_random_value(self):
        """ 
        Get random value with probability based on its frequency in the map.
        Example: {'NOUN':2,'DET':1} will return 'NOUN' with 2/3 probability.
        """
        if len(self.freq_map.values()) == 0: 
            return ''
        probabilities = [value / sum(self.freq_map.values()) for value in\
                         self.freq_map.values()]
        choice = np.random.choice(tuple(self.freq_map.keys()),p=probabilities)
        return choice
    
    def __repr__(self):
        """
        String representation of FrequencyMap object to be used when debugging.
        """
        output = ''
        for obj in self.freq_map.keys():
            output += '{}:{},'.format(obj, self.freq_map.get(obj))
        return output

    def __str__(self):
        """
        String representation of FrequencyMap object to be printed.
        """
        output = ''
        for obj in self.freq_map.keys():
            output += '{}:{}\n'.format(obj, self.freq_map.get(obj))
        return output


class POSManager():
    """ 
    The POSManager class manages a dictionary mapping parts of speech to 
    a FrequencyMap and dictionary objects while pulling from and updating a 
    CSV file of part of speech (POS) frequencies. 
    """
    def __init__(self, filename='sequence_table.csv'):
        self.filename = filename
        self.table = self.read_pos_sequence_probabilities()

    def add_to_table(self, cur, next_, existing):
        """ 
        Based on a current and next token, either add to existing 
        FrequencyMap objects for a token map of words to their frequencies 
        for a specified POS and for a POS frequency map of next POS to their 
        frequencies, or create new objects.
        """
        cur_text = cur.lemma_.lower().replace('\\u200a','') # parse text representation 
        element = self.table.get(cur.pos_)

        if cur.is_alpha: 
            if next_ == '': # edge case 
                next_pos = ''
            else:
                next_pos = next_.pos_
            if element is not None:
                element['token_list'].append(cur_text)
                pos_freq = element['pos_freq']
                if not existing:
                    pos_freq.change_frequency(next_pos)
            else: 
                pos_freq = FrequencyMap(next_)
                element = {'pos_freq': pos_freq, 
                        'token_list': [cur_text]}
                self.table[cur.pos_] = element

    def add_to_start(self, token):
        """ 
        Adds frequencies of POS at the beginning of each line.
        """
        start = self.table.get('START')
        if start is not None: 
            pos_freq = start['pos_freq']
            pos_freq.change_frequency(token.pos_)
        else: 
            self.table['START'] = {'pos_freq': FrequencyMap(token.pos_)}

    def add_text(self, input_text, existing=False):
        """ 
        Helper method to construct a word map the goes through each token
        of the input text. Calls on the add_to_table() method to fill that 
        dictionary.
        
        Additional parameter will check if the text is "existing", meaning if 
        it already exists in the CSV file of scraped texts. An "existing" text
        will be parsed differently before it is sent through the code.

        If text is not already "existing", its POS patterns will be written 
        into the CSV file of POS sequences. 
        """
        if existing:
            input_text = input_text[2:-2].split("', '") # parsed differently 

        for line in input_text:
            tokens = nlp(line)
            self.add_to_start(tokens[0])
            for i in range(len(tokens)):
                cur_token = tokens[i]
                if i == len(tokens) - 1:
                    next_token = ''
                else: 
                    next_token = tokens[i+1]
                self.add_to_table(cur_token, next_token, existing)

        if not existing:
            self.write_pos_sequence_probabilities_to_csv()

    def read_pos_sequence_probabilities(self):
        """ 
        From CSV file, compile a part of speech frequency dictionary, which
        maps a key POS to another dictionary where the key is a next potential
        POS and the value is the count of how often that POS follows the first
        POS. Function returns the encompassing dictionary. 
        """
        if not os.path.isfile(self.filename) or os.stat(self.filename).st_size == 0:
            return dict()
        
        pos_probs = {}

        with open(self.filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                pos = row[''] # gets leftmost column where POS is stored

                if pos is not None:
                    probabilities = {} 

                    for next_pos, freq in row.items(): 
                        if freq is None: 
                            freq = 0
                        if next_pos != '':
                            probabilities[next_pos] = float(freq)

                    # add to a new dictionary to store in the object 
                    pos_probs[pos] = {'pos_freq': FrequencyMap(freq_map=probabilities),
                                       'token_list': []}
        return pos_probs

    def write_pos_sequence_probabilities_to_csv(self):
        """ 
        Using the POS frequency dictionary, write a CSV file where each
        column is a POS and the first element is also a POS. The intersection 
        is how often the row POS comes before the column POS.
        """
        with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # write header row with POS column names 
            header = [''] + list(self.table.keys())
            writer.writerow(header)

            # write rows with POS sequence probabilities
            for pos1 in self.table:
                pos_freq = self.table[pos1]['pos_freq'].freq_map
                probs = []

                for pos2 in self.table.keys():
                    value = pos_freq.get(pos2)
                    if value is None: 
                        value = 0
                    probs.append(value)
                    
                row = [pos1] + probs
                writer.writerow(row)

    def choose_next_pos(self, current_pos):
        """ 
        Reading from the POS frequency dictionary and given a current POS, 
        use the frequencies as weighted probabilities to find a next possible
        POS. If nothing is found, return the current POS.  
        """
        if current_pos in self.table['pos_freq']:
            prob_dict = self.table['pos_freq'][current_pos]
            probabilities = [value / sum(prob_dict.values()) for value in\
                        prob_dict.values()]
            return np.random.choice(tuple(prob_dict.keys()), p=probabilities)
        return current_pos  # return current POS if no suitable POS is found
    
    def get_tokens_for_pos(self, pos):
        """
        Returns list of all tokens associated with a particular POS. 
        """
        return self.table.get(pos)['token_list'] 
    
    def get_random_token_for_pos(self, pos):
        """
        Randomly chooses a token associated with a particular POS. If there are
        no tokens associated with that POS, return None. 
        """
        if len(self.table.get(pos)['token_list']) > 0:
            return np.random.choice(self.table.get(pos)['token_list'])
        return None
    
    def get_next_pos(self, pos):
        """
        Return the next POS based on weighted probabilities. 
        """
        return self.table.get(pos)['pos_freq'].get_random_value()

    def __repr__(self):
        """
        String representation of POSManager object to be used when debugging.
        """
        output = ''
        for pos in self.table.keys():
            output += '{}:{}-'.format(pos, self.table.get(pos))
        return output
    
    def __str__(self):
        """ 
        String representation of POSManager object to be printed. 
        """
        output = ''
        for pos in self.table.keys():
            output += '{}:\n{}\n{}\n'.format(pos, 
                                             self.table.get(pos)['pos_freq'],
                                             self.table.get(pos)['token_list'])
        return output