import requests
import csv 
import os

from bs4 import BeautifulSoup
from evaluation import get_keywords
from pos_manager import POSManager


class PoemScraper():
    """
    Manages data to build inspiring set. 
    """
    def __init__(self, filename='scraping_data.csv'):
        self.filename = filename
        self.link_data = []
        self.scraped_poems = dict()
        self.pos_sequence = POSManager()

    def add_query(self, query): 
        """
        Method first checks if the query already exists in the CSV file of 
        scraped data. If it does, convert the data to frequencies and token 
        lists in the POSManager. If not, use BeautifulSoup to scrape for new
        poems and parse thorough that data.
        """
        if not self.query_exists(self.filename, query): 
            poem_data = self.start_search(query)
            self.scrape_poems(poem_data)
        else: 
            # compile POSManager with the stored information
            self.convert_csv_to_frequencies(query)

    def start_search(self, query): 
        """
        Start search with a query. If the query returns fewer than 5 hits, 
        expand the search. 
        """
        poem_data = self.find_poems(query)
        if len(self.link_data) < 5: 
            poem_data = self.expand_search(query)
        return poem_data

    def expand_search(self, query):
        """
        Expand search to keywords found in the original query, using
        get_keywords() (also used by evaluation metrics) as a helper method to
        distinguish keywords from fillers. If keyword queries already exist, 
        convert that data to frequencies and token lists in the POSManager, 
        otherwise, scrape for new poems. 
        """
        keywords = get_keywords(query)
        poem_data = []
        for word in keywords:
            if not self.query_exists(self.filename, word): 
                poem_data += self.find_poems(word)
            else: 
                # compile POSManager with the stored information
                self.convert_csv_to_frequencies(word)
        return poem_data

    def find_poems(self, query):
        """
        Format a query and search for that query on PoetryFoundation.org. 
        Parse the returned poems for their links and titles and return as a 
        dictionary, including the query that returned those poems. 
        """
        formatted_text = query.replace(' ','%20')
        url = 'https://www.poetryfoundation.org/search?query={}&\
            refinement=poems'.format(formatted_text)
        data = requests.get(url)
        html = BeautifulSoup(data.text, 'html.parser')
        articles = html.select('div.c-feature-hd')

        poem_data = []
        for article in articles:
            title = article.select('a')[0].get_text()
            link = article.select('a')[0].get_attribute_list('href')
            poem_data.append({'query': query, 'title': title, 'link': link})
        return poem_data

    def scrape_poems(self, poem_data):
        """
        Using poem data, scrape the link value for the poem found at that 
        PoetryFoundation.org link. Scrape the HTML using BeautifulSoup and 
        parse the HTML elements with helper methods. Use the results of the 
        scraped poems to append the CSV file to prevent scraping 'double 
        dipping' and improve efficiency. 
        """
        results = []
        for element in poem_data: 
            poem_url = 'https://www.poetryfoundation.org{}'.format(element['link'][0])
            poem_data = requests.get(poem_url)
            poem_html = BeautifulSoup(poem_data.text, 'html.parser')
            lines = self.get_lines_from_html(poem_html)
            if len(lines) > 0:
                self.pos_sequence.add_text(lines)
                self.scraped_poems[element['title'][0]] = lines
                element['author'] = self.get_author_from_html(poem_html)
                results.append({'query': element['query'],
                                'author': element['author'],
                                'title': element['title'],
                                'poem': lines,
                                'link': element['link'][0]
                                })
        self.append_poem_data_to_csv(results, 'scraping_data.csv')

    def get_lines_from_html(self, html):
        """ 
        Helper method to parse poem lines from HTML. Removes characters that 
        were persistent while debugging. 
        """
        lines = []
        poem_tag = html.select('div.o-poem')
        if len(poem_tag) > 0:
            for line in poem_tag[0].select('div'):
                if line.attrs != {}: 
                    if 'class' not in line.attrs \
                        and 'font-style:italic;' not in line.attrs.get('style') and \
                            line.get_text().strip() != '':
                        lines.append(line.get_text().strip().replace('\xa0',''))
        return lines

    def get_author_from_html(self, html):
        """ 
        Helper method to parse author from HTML when scraping a poem.
        """
        author_tag = html.select('div.c-feature-sub')
        if len(author_tag) > 0:
            return author_tag[0].select('.c-txt')[0].get_text().replace('By ','').strip()
        
    def get_all_authors(self):
        """
        Iterate through the Author column of the CSV file of scraped data and 
        compiles a set of all authors whose poems were scraped. Then returns 
        the set as a list. 
        """
        unique_authors = set()
        with open(self.filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            try:
                for row in reader:
                    if 'Author' in row:
                        author = row['Author']
                        unique_authors.add(author)
            except: # edge case when reading exceeded
                return list(unique_authors)
            
        return list(unique_authors)
    
    def query_exists(self, filename, query):
        """
        Iterates through CSV file of scraped data and returns whether the query
        has been made and recorded already. 
        """
        if not os.path.isfile(filename):
            return False

        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Query'] == query: # has been found!
                    return True
                
        return False
    
    def append_poem_data_to_csv(self, results, filename):
        """
        Save scraping results by appending to a CSV file. Results parameter is
        a list of poems and associated data and must be formatted to have a the
        query that returned the poem, the author who wrote it, the title of the
        poem, the lines of poetry, and the link where the poem was found. 
        """
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Query', 'Author', 'Title', 'Poem', 'Link'] # headers
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # check first if file is empty
            if not file_exists or os.stat(filename).st_size == 0:
                writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'Query': result['query'], 
                    'Author': result['author'],
                    'Title': result['title'],
                    'Poem': result['poem'],
                    'Link': result['link']
                })

        csvfile.close()

    def convert_csv_to_frequencies(self, query):
        """ 
        Finds poems scraped using matching query and adds that text to 
        the POS sequence handled by a POSManager object. 
        """
        with open(self.filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                if 'Query' in row and 'Poem' in row:  
                    if row['Query'].lower() == query.lower():
                        self.pos_sequence.add_text(row['Poem'], existing=True)