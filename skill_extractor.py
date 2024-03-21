import spacy
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from collections import Counter
from indeed_scraper import scrape_jobs

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def preprocess(text):
    # Create a document object
    doc = nlp(text)
    # Lemmatize, lower case and remove stop words and punctuation
    return [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and not token.is_space]

def main(job_title, location):
    df = scrape_jobs(job_title, location)

    # Preprocess the job descriptions
    df['processed_descriptions'] = df['description'].apply(preprocess)

    # Create a dictionary and corpus needed for topic modeling
    dictionary = corpora.Dictionary(df['processed_descriptions'])
    corpus = [dictionary.doc2bow(text) for text in df['processed_descriptions']]

    # Apply LDA topic modeling
    lda = LdaModel(corpus, num_topics=5, id2word=dictionary, passes=15)
    topics = lda.print_topics(num_words=5)

    # Counting the most common terms across all job descriptions
    # Flatten the list of processed descriptions and count occurrences
    all_words = [word for desc in df['processed_descriptions'] for word in desc]
    word_freq = Counter(all_words)
    most_common_words = word_freq.most_common(10)

    # Print the most common terms and the topics found by LDA
    print("Most Common Terms:\n", most_common_words)
    print("\nLDA Topics:\n", topics)

    # Save the DataFrame to a CSV file, including the processed descriptions
    df.to_csv('job_listings_with_processed.csv', index=False)

if __name__ == "__main__":
    main("data intern", "Mississauga, ON")
