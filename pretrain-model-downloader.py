#!/User/local/bin/python3
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


print('Pre-downloading DistilBERT model...')

cache_dir = 'models/distilbert-sentiment'
os.makedirs(cache_dir, exist_ok=True)

# Download the default sentiment analysis model
pipeline('sentiment-analysis', 
         model='distilbert-base-uncased-finetuned-sst-2-english',
         cache_dir=cache_dir,
         return_all_scores=True)
print('DistilBERT model pre-downloaded successfully!')
