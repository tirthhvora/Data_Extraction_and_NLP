"""
Section 1: Importing important libraries

"""


import requests                 # For making HTTP requests and retrieving HTML content from website
from bs4 import BeautifulSoup   # I am personally use BeautifulSoup for web scraping
import pandas as pd
import re                       # Regular expressions
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


stop_words = set() # Stores stopwords

for file_name in stop_words_files:

    try:

        with open(file_name, 'r', encoding='utf-8') as f:
            stop_words.update(word.strip() for word in f.readlines())  # Read each line, clean each word and update the set

    except UnicodeDecodeError:
      
        try:
            with open(file_name, 'r', encoding='latin-1') as f:
                stop_words.update(word.strip() for word in f.readlines())

        except UnicodeDecodeError as e:  # If both don't work, log which file is causing error.
            print(f"Error decoding {file_name}: {e}")
            continue

# Read positive and negative words from the provided master dictionary files
positive_words = set()
with open('positive-words.txt', 'r', encoding='utf-8') as f:
    positive_words.update(word.strip() for word in f.readlines())

negative_words = set()
with open('negative-words.txt', 'r', encoding='latin-1') as f:
    negative_words.update(word.strip() for word in f.readlines())



# Load the Excel file
df = pd.read_excel('input.xlsx')
list_of_urls = df['URL'].tolist()   # Extracting the 'URL' column from the DataFrame and converting it to a list named 'list_of_urls'.


result_data = []    # will appdend all the text analysis data here

"""
Section 3: Extracting text from URLs, and text analysis


Note: In Text analysis part, I followed the logic from text_analysis.docx given by you. 
      I faced ZeroDivisionError a lot, hence had to add many if statements in between

      Article 11668, 17671.4 not found.
"""


# Looping through URL ID and URL simultaneously
for url_id, url in zip(df['URL_ID'], list_of_urls):

    response = requests.get(url)                    #sending a get request to URl and returning the response object.

    soup = BeautifulSoup(response.content, 'html.parser')  # The content attribute of the response contains raw HTML content.
    # soup variable stores the parsed HTML content


    article_text = ""                  # will store all the paragraph text in this.
    article = soup.find('article')   # Find article tag in the HTML document

    if article:

        paragraphs = article.find_all('p')   # finds all occurrences of <p> tags

        for p in paragraphs:
            article_text += p.get_text() + '\n'
    
    if article_text:  # Checking if article text was successfully extracted
        blob = TextBlob(article_text)
        
        positive_score = sum(1 for word in blob.words if word.lower() in positive_words and word.lower() not in stop_words)
        negative_score = sum(1 for word in blob.words if word.lower() in negative_words and word.lower() not in stop_words)
        polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
        subjectivity_score = (positive_score + negative_score) / (len(blob.words) + 0.000001)
        
        # Checking if there are sentences before calculating averages
        if blob.sentences:
            avg_sentence_length = sum(len(sentence.words) for sentence in blob.sentences) / len(blob.sentences)
            avg_words_per_sentence = len(blob.words) / len(blob.sentences)
        else:
            avg_sentence_length = 0
            avg_words_per_sentence = 0
        
        # Checking if there are words before calculating percentages
        if blob.words:
            complex_words = [word for word in blob.words if syllables.estimate(word) > 2]
            percentage_complex_words = (len(complex_words) / len(blob.words)) * 100
        else:
            percentage_complex_words = 0


        #Calculating Variables    
        
        fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)
        complex_word_count = len(complex_words)
        word_count = len(blob.words)
        syllable_per_word = sum(syllables.estimate(word) for word in blob.words) / len(blob.words)
        personal_pronouns = sum(1 for word in blob.words if re.match(r'\b(?:I|me|my|mine|we|us|our|ours)\b', word, re.IGNORECASE))
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

result_df.to_excel('final_output.xlsx', index=False)
