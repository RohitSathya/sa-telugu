from flask import Flask, render_template, request
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator
import nltk
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import re
import requests

app = Flask(__name__)

# Download NLTK Vader lexicon (if not already downloaded)
nltk.download('vader_lexicon')

# Initialize the sentiment analyzer
sia = SentimentIntensityAnalyzer()

aw=[]
with open('words.txt', 'r') as file:
    angry_w = file.read().splitlines()
    aw=angry_w
    print(aw)

def extract_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.match(regex, url)
    if match:
        return match.group(1)
    else:
        return None

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for any HTTP error
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        return text.strip()
    except requests.RequestException as e:
        print(f"Request Error: {e}")
        return None
    except Exception as e:
        print(f"Error extracting text from URL: {e}")
        return None

@app.route('/')
def index():
    return render_template('t.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form['text']
    file = request.files['file'] if 'file' in request.files else None
    url = request.form['url']

    if text or file or url:
        if file:
            # Read the text content of the uploaded file
            text = file.read().decode('utf-8')
        if url:
            if "youtube.com" in url:
                video_id = extract_video_id(url)
                if video_id:
                    # Fetch transcript from YouTube using video ID
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id)
                        text = ' '.join([sub['text'] for sub in transcript])
                    except Exception as e:
                        return f'Error: {e}'
                else:
                    return 'Invalid YouTube URL. Please provide a valid URL.'
            else:
                text = extract_text_from_url(url)
                if not text:
                    return 'Error: Unable to extract text from the provided URL.'
                # Truncate the text if it exceeds 5000 characters
                if len(text) > 5000:
                    text = text[:4000]

        # Translate text to English if it's not in English
        if not text.isascii():
            translated_text = GoogleTranslator(source='te', target='en').translate(text)
        else:
            translated_text = text

        # Analyze sentiment for translated text
        scores = sia.polarity_scores(translated_text)
        angry_word_count = 0
        angry_words_list = []

        # Determine sentiment label based on compound score
        if scores['compound'] >= 0.05:
            sentiment = 'Positive'
            for word in translated_text.lower().split():
                if word in aw:
                    angry_word_count += 1
                    angry_words_list.append(word)
        elif scores['compound'] <= -0.02:
            sentiment = 'Negative'
            for word in translated_text.lower().split():
                if word in aw:
                    angry_word_count += 1
                    angry_words_list.append(word)





        else:
            sentiment = 'Neutral'
            for word in translated_text.lower().split():
                if word in aw:
                    angry_word_count += 1
                    angry_words_list.append(word)


        # Count angry words
        words = translated_text.split()
        angry_word_count = sum(1 for word in words if word.lower() in aw)

        # Construct result dictionary
        result = {
            'sentiment': sentiment,
            'angry_word_count': angry_word_count,
            'original_text': text,
            'translated_text': translated_text,
            'angry_words': angry_words_list,
            'Positive': scores['pos'],
            'Negative': scores['neg'],
            'Neutral': scores['neu'],
            'Compound': scores['compound'],

        }

        return render_template('t.html', result=result)
    else:
        return 'Please provide some text, upload a file, or enter a YouTube URL.'

if __name__ == '__main__':
    app.run()
