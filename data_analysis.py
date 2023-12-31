"""
Section 1: Importing important libraries

"""


import requests                 # For making HTTP requests and retrieving HTML content from website
from bs4 import BeautifulSoup   # I am personally use BeautifulSoup for web scraping
import pandas as pd
from textblob import TextBlob   # For NLP tasks like sentiment analysis, tokenization, parts-of-speech tagging etc.
import syllables                # To estimate number of syllables in words.
import nltk                     # To download punkt tokenizer

nltk.download('punkt')          # Downloading the 'punkt' tokenizer models



"""
Section 2: Reading StopWords and Master Dictionary words.
Note: 1. used set() because: Fast iteration, handles duplicate words & searches more fast.
      2. I use exception handling more frequently.
      3. In some files, utf-8 encoding worked, in some latin-1 worked.
"""


stop_words_files = ['StopWords_Auditor.txt', 'StopWords_DatesAndNumbers.txt',
                    'StopWords_Generic.txt', 'StopWords_GenericLong.txt', 'StopWords_Geographic.txt',
                    'StopWords_Names.txt']


stop_words = set() # Efficient searching and no repitition

for stop_word_file in stop_words_files:

    try:

        with open(stop_word_file, 'r', encoding='utf-8') as file:
            stop_words.update(word.strip() for word in file.readlines())  # Read each line, clean each word and update the set

    except UnicodeDecodeError:
      
        try:
            with open(stop_word_file, 'r', encoding='latin-1') as file:
                stop_words.update(word.strip() for word in file.readlines())

        except UnicodeDecodeError as e:  # If both don't work, log which file is causing error.
            print(f"Error decoding {stop_word_file}: {e}")
            continue

# Read positive and negative words from the provided master dictionary files
positive_words = set()
with open('positive-words.txt', 'r', encoding='utf-8') as file:
    positive_words.update(word.strip() for word in file.readlines())

negative_words = set()
with open('negative-words.txt', 'r', encoding='latin-1') as file:
    negative_words.update(word.strip() for word in file.readlines())



# Load the Excel file
df = pd.read_excel('input.xlsx')
list_of_urls = df['URL'].tolist()   

result_data = []    # will appdend all the text analysis data here

"""
Section 3: Extracting text from URLs, and text analysis


Note: In Text analysis part, I followed the logic from text_analysis.docx given. 
      I faced ZeroDivisionError a lot, hence had to add many if statements in between

      Article 11668, 17671.4 not found.
"""

for url_id, url in zip(df['URL_ID'], list_of_urls):

    response = requests.get(url)                    

    soup = BeautifulSoup(response.content, 'html.parser')  # The content attribute of the response contains raw HTML content.
                                                           # soup variable stores the parsed HTML content


    article_text = ""                  # will store all the paragraph text in this.
    article = soup.find('article')     # Finds the first occurance of article tag in the HTML document
                                    
    if article:

        paragraphs = article.find_all('p')  # returns a list of paragraph elements
        for p in paragraphs:
            article_text += p.get_text() + '\n'
    
    if article_text:  
        blob = TextBlob(article_text)

        """
        Sentiment Analysis
        """
        
        positive_score = sum(1 for word in blob.words if word.lower() in positive_words and word.lower() not in stop_words)
        
        negative_score = sum(1 for word in blob.words if word.lower() in negative_words and word.lower() not in stop_words)

        polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
        # Overall sentiment of the article (Positive or Negative)

        subjectivity_score = (positive_score + negative_score) / (len(blob.words) + 0.000001)
        # Is the article subjective (emotions and opinions) or objective (facts)?

       
        """
        Readability scores and analysis
        """
       
        # Checking if there are sentences before calculating averages
        # (.) is a delimiter and differenciates sentences.
        if blob.sentences:
            avg_sentence_length = sum(len(sentence.words) for sentence in blob.sentences) / len(blob.sentences)
            avg_words_per_sentence = len(blob.words) / len(blob.sentences)

          
        else:
            avg_sentence_length = 0   
            avg_words_per_sentence = 0
        
        # Avoiding error probabilities

        if blob.words: 
            complex_words = [word for word in blob.words if syllables.estimate(word) > 2]
            # If for a word, syllables > 2, it is a complex word

            percentage_complex_words = (len(complex_words) / len(blob.words)) * 100
        else:
            percentage_complex_words = 0


        #Calculating Variables    
        
        # Higher fog index means complex and hard-to-read text
        fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)
        
        complex_word_count = len(complex_words)
        word_count = len(blob.words)

        # It is an average
        syllable_per_word = sum(syllables.estimate(word) for word in blob.words) / len(blob.words)

        personal_pronouns = sum(1 for word in blob.words if word.lower() in {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'})
        avg_word_length = sum(len(word) for word in blob.words) / len(blob.words)
        
        result_data.append([url_id, url, positive_score, negative_score, polarity_score, subjectivity_score,
                            avg_sentence_length, percentage_complex_words, fog_index, avg_words_per_sentence,
                            complex_word_count, word_count, syllable_per_word, personal_pronouns, avg_word_length])
    else:
        print(f"Article tag text not found for URL_ID {url_id} and URL: ({url})")  



"""
Section 4: Saving ouputs in DataFrame and then to excel file
"""       

result_df = pd.DataFrame(result_data, columns=['URL_ID', 'URL', 'POSITIVE SCORE', 'NEGATIVE SCORE', 'POLARITY SCORE',
                                                'SUBJECTIVITY SCORE', 'AVG SENTENCE LENGTH', 'PERCENTAGE OF COMPLEX WORDS',
                                                'FOG INDEX', 'AVG NUMBER OF WORDS PER SENTENCE', 'COMPLEX WORD COUNT',
                                                'WORD COUNT', 'SYLLABLE PER WORD', 'PERSONAL PRONOUNS', 'AVG WORD LENGTH'])

result_df.to_excel('test    .xlsx', index=False)
