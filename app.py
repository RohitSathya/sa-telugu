from flask import Flask, render_template, request
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
from deep_translator import GoogleTranslator
from youtube_transcript_api import YouTubeTranscriptApi
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk

import re


app = Flask(__name__)

# Download NLTK Vader lexicon (if not already downloaded)
nltk.download('vader_lexicon')

# Predefined list of angry words
angry_words = ['kill', 'fail']
def extract_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.match(regex, url)
    if match:
        return match.group(1)
    else:
        return None




@app.route('/')
def index():
    return render_template('t.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form['text']
    file = request.files['file']  # Get the uploaded file
    url = request.form['url']  # Get the YouTube URL from the form

    if text or file or url:
        if file:
            # Read the text content of the uploaded file
            text = file.read().decode('utf-8')
        if url:
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



        # Translate text to English if it's not in English
        if not text.isascii():
            translated_text = GoogleTranslator(source='te', target='en').translate(text)
        else:
            translated_text = text

        # Initialize the sentiment analyzer
        sia = SentimentIntensityAnalyzer()
        # Get sentiment scores
        scores = sia.polarity_scores(translated_text)
        # Determine sentiment label based on compound score
        angry_word_count = 0
        angry_words_list = []

        # Determine sentiment label based on compound score
        if scores['compound'] >= 0.2:
            sentiment = 'Positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'Negative'

            for word in translated_text.lower().split():
                print('hi')
                angry_word_count += 1
                angry_words_list.append(word)



        else:
            sentiment = 'Neutral'

        # Construct result string
        result = {
            'sentiment': sentiment,
            'angry_word_count': angry_word_count,
            'angry_words': angry_words_list,
            'original_text': text,
            'translated_text': translated_text  # Add translated text to result
        }

        return render_template('t.html', result=result)
    else:
        return 'Please provide some text, upload a file, or enter a YouTube URL.'
if __name__ == '__main__':
    app.run()
