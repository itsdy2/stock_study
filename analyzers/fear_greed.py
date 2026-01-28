# -*- coding: utf-8 -*-
# analyzers/fear_greed.py

def analyze(P):
    """
    Fear & Greed Analysis
    Returns a dict with 'type', 'title', 'data'
    """
    # Placeholder logic
    result = {
        'kospi': {'score': 50, 'status': 'Neutral'},
        'kosdaq': {'score': 45, 'status': 'Neutral'}
    }
    
    return {
        'key': 'fear_greed', # Unique key for this analyzer
        'type': 'card_pair', # Custom type for F&G layout
        'title': 'Fear & Greed Index (Beta)',
        'data': result,
        'order': 2 
    }
