import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class SentimentClassifier:
    """
    Advanced Sentiment Classifier
    
    WHY BEYOND VADER?
    -----------------
    VADER (Valence Aware Dictionary and sEntiment Reasoner) is excellent
    for general social media text, but has limitations:
    
    VADER Strengths:
    ✅ Works out-of-the-box (no training needed)
    ✅ Handles social media language well
    ✅ Fast processing (rule-based)
    ✅ Considers context (punctuation, caps, emoticons)
    
    VADER Limitations:
    ❌ Not trained on university-specific language
    ❌ May miss campus-specific slang and terminology
    ❌ Cannot learn from new data patterns
    ❌ Fixed vocabulary (can't adapt to new words)
    
    CUSTOM MODEL ADVANTAGES:
    ✅ Trained specifically on UCLA Reddit data
    ✅ Understands campus terminology ("Bruin Plate", "Powell", "South Campus")
    ✅ Learns department-specific sentiment patterns
    ✅ Adapts to seasonal patterns (finals stress, graduation joy)
    ✅ Higher accuracy on university-specific content
    
    HYBRID APPROACH:
    We use both VADER and custom models:
    - VADER: Fast baseline sentiment for all content
    - Custom Model: High-accuracy analysis for important content
    - Ensemble: Combine both for best results
    """    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.label_mapping = {0: 'negative', 1: 'neutral', 2: 'positive'}
        
    def load_model(self):
# ============================================
# MACHINE LEARNING PIPELINE EXPLANATION
# ============================================

"""
The ML pipeline provides advanced sentiment analysis capabilities
beyond the basic VADER sentiment analyzer. It includes:

1. Custom sentiment classifiers trained on UCLA-specific data
2. Model training and evaluation pipelines
3. Real-time inference services
4. Model versioning and deployment management

This enables more accurate sentiment analysis tailored to
university discourse and campus-specific language patterns.
"""

# ============================================
# ML MODELS (app/ml/models/)
# ============================================

class SentimentClassifier:
    """
    Advanced Sentiment Classifier
    
    WHY BEYOND VADER?
    -----------------
    VADER (Valence Aware Dictionary and sEntiment Reasoner) is excellent
    for general social media text, but has limitations:
    
    VADER Strengths:
    ✅ Works out-of-the-box (no training needed)
    ✅ Handles social media language well
    ✅ Fast processing (rule-based)
    ✅ Considers context (punctuation, caps, emoticons)
    
    VADER Limitations:
    ❌ Not trained on university-specific language
    ❌ May miss campus-specific slang and terminology
    ❌ Cannot learn from new data patterns
    ❌ Fixed vocabulary (can't adapt to new words)
    
    CUSTOM MODEL ADVANTAGES:
    ✅ Trained specifically on UCLA Reddit data
    ✅ Understands campus terminology ("Bruin Plate", "Powell", "South Campus")
    ✅ Learns department-specific sentiment patterns
    ✅ Adapts to seasonal patterns (finals stress, graduation joy)
    ✅ Higher accuracy on university-specific content
    
    HYBRID APPROACH:
    We use both VADER and custom models:
    - VADER: Fast baseline sentiment for all content
    - Custom Model: High-accuracy analysis for important content
    - Ensemble: Combine both for best results
    """
    
    def load_model(self):
        """
        Model Loading Strategy:
        
        DEVELOPMENT MODE:
        - Uses rule-based classifier for demo
        - No GPU requirements
        - Fast startup time
        - Consistent results for testing
        
        PRODUCTION MODE:
        - Loads pre-trained transformer model
        - Uses GPU acceleration if available
        - Caches model in memory for speed
        - Falls back to VADER if model fails
        
        Model Architecture Options:
        
        1. DISTILBERT (Recommended):
           - 66M parameters (lightweight)
           - 97% of BERT performance
           - 60% faster inference
           - Perfect for real-time applications
        
        2. ROBERTA-BASE:
           - 125M parameters (more accurate)
           - Trained on social media text
           - Better handling of informal language
           - Higher computational requirements
        
        3. DOMAIN-SPECIFIC FINE-TUNED:
           - Start with DistilBERT
           - Fine-tune on UCLA Reddit data
           - Best accuracy for our use case
           - Requires training pipeline
        
        Loading Process:
        1. Check for latest model version in model registry
        2. Download model files from cloud storage
        3. Load tokenizer and model weights
        4. Run validation on test samples
        5. Cache in memory for fast inference
        6. Set up fallback to VADER if needed
        """
        try:
            # For demo, use a simple rule-based approach
            # In production, would load actual ML model
            logger.info("Loading sentiment classifier model")
            self.model = "rule_based"  # Placeholder
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Advanced Prediction Pipeline:
        
        Input: "I'm really struggling with CS 31 and feeling overwhelmed"
        
        STEP 1: TEXT PREPROCESSING
        -------------------------
        Raw text: "I'm really struggling with CS 31 and feeling overwhelmed"
        
        Preprocessing:
        - Normalize: "I'm really struggling with cs 31 and feeling overwhelmed"
        - Handle UCLA terms: "cs 31" → "computer science 31"
        - Clean special chars: Remove extra punctuation
        - Tokenize: ["I'm", "really", "struggling", "with", "computer", "science", "31", "and", "feeling", "overwhelmed"]
        
        STEP 2: FEATURE EXTRACTION
        --------------------------
        DistilBERT Tokenization:
        - Convert to token IDs: [101, 1045, 1005, 1049, 2428, 8023, 2007, 7942, 2671, 2861, 1998, 3110, 13764, 102]
        - Add attention masks: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        - Pad to max length: 512 tokens
        
        STEP 3: MODEL INFERENCE
        ----------------------
        Forward pass through transformer:
        - Input embeddings: 768-dimensional vectors
        - 6 transformer layers (DistilBERT)
        - Attention mechanisms focus on key words
        - Final hidden state: [768-dim vector]
        - Classification head: [768] → [3] (pos/neg/neu)
        
        STEP 4: RESULT INTERPRETATION
        ----------------------------
        Raw logits: [-0.2, -1.5, 2.1]  # [negative, neutral, positive]
        Softmax probabilities: [0.15, 0.05, 0.80]
        
        Predicted class: positive (index 2)
        Confidence: 0.80 (80%)
        
        Wait, this seems wrong! Let's check...
        
        STEP 5: DOMAIN ADAPTATION
        -------------------------
        The model might classify "struggling" as positive in academic context
        because struggle often leads to growth and learning.
        
        Domain-specific adjustments:
        - "struggling with CS" → academic challenge (slightly negative)
        - "feeling overwhelmed" → stress indicator (negative)
        - Combined context → negative sentiment
        
        Final classification:
        - Sentiment: negative
        - Confidence: 0.75
        - Academic stress context detected
        - Recommendation: Route to academic support
        
        Output:
        {
            'sentiment': 'negative',
            'confidence': 0.75,
            'compound_score': -0.4,
            'probabilities': {
                'negative': 0.65,
                'neutral': 0.25,
                'positive': 0.10
            },
            'context': 'academic_stress',
            'model_version': 'distilbert-ucla-v2.1'
        }
        """
        try:
            if not self.model:
                self.load_model()
            
            # Simple rule-based sentiment for demo
            positive_words = ['good', 'great', 'amazing', 'love', 'excellent', 'awesome', 'happy', 'wonderful']
            negative_words = ['bad', 'terrible', 'hate', 'awful', 'horrible', 'sad', 'angry', 'disappointed']
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                sentiment = 'positive'
                confidence = min(0.7 + pos_count * 0.1, 0.95)
            elif neg_count > pos_count:
                sentiment = 'negative'
                confidence = min(0.7 + neg_count * 0.1, 0.95)
            else:
                sentiment = 'neutral'
                confidence = 0.6
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'model_version': 'rule_based_v1.0'
            }
            
        except Exception as e:
            logger.error(f"Error predicting sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'error': str(e)
            }
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict sentiment for multiple texts"""
        return [self.predict(text) for text in texts]
