from bs4 import BeautifulSoup
import requests

def get_google_search_results(query):
    """
    For a query search, return the number of search hits that Google returns 
    for such a query. If there are no search results or an error occurs, return
    None. 
    """
    url = 'https://www.google.com/search?q={}'.format(query)
    headers = {
        'User-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    } # need headers to get results, found on StackExchange 

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # find the element containing the search result count
        result_stats = soup.find('div', {'id': 'result-stats'})
        
        if result_stats:
            # extract number from the text
            if 'About' in result_stats.text: # number will be second word
                result_count_text = result_stats.text.split()[1]
            else: # without 'About', the number is the first word
                result_count_text = result_stats.text.split()[0]
            try: # set up try/except in case not a number
                result_count = int(result_count_text.replace(',', ''))
            except: 
                return None # edge case for no results
            return result_count
        else:
            alternative_result_stats = soup.find('div', {'id': 'search'})
            if alternative_result_stats:
                # extract number from the text using another element
                result_count_text = alternative_result_stats.text.split()[3]  
                result_count = int(result_count_text.replace(',', ''))
                return result_count
            else:
                return None
    else:
        return None
    
def compare_search_results(search1, search2):
    """
    For two search queries, get the number of searchs returned by Google, then
    return the search query that generated more results. 
    """
    results1 = get_google_search_results(search1)
    results2 = get_google_search_results(search2)

    # check edge casess
    if results1 is None:
        return search2
    if results2 is None: 
        return search1
    
    # return whichever search got more results
    if results1 >= results2: 
        return search1
    else: 
        return search2
    
def get_next_word(root, word1, word2): 
    """
    Determine which word will generate more search results when concatenated
    with the root parameter and return that word. Uses compare_search_results() 
    and get_google_search_results() functions above.
    """
    return compare_search_results('{} {}'.format(root,word1),
                                  '{} {}'.format(root,word2)
                                  ).removeprefix('{} '.format(root))
