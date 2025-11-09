"""
Search routing and decision logic
"""
from difflib import SequenceMatcher

def fuzzy_match(text: str, keywords: list, threshold: float = 0.6) -> bool:
    """Check if any keyword fuzzy matches the text"""
    text_lower = text.lower()
    
    # Exact substring match first
    for keyword in keywords:
        if keyword in text_lower:
            return True
    
    # Fuzzy matching for misspellings
    words = text_lower.split()
    for word in words:
        for keyword in keywords:
            ratio = SequenceMatcher(None, word, keyword).ratio()
            if ratio >= threshold:
                return True
    
    return False

def should_search_products(question: str) -> bool:
    """Check if question is about products"""
    product_keywords = [
        'tumbler', 'cup', 'drinkware', 'bottle', 'price', 'cost', 
        'product', 'item', 'capacity', 'size', 'design', 'color', 'material',
        'recommend', 'suggest', 'best', 'water', 'coffee', 'drink', 'hot', 'cold',
        'all day', 'frozee', 'buddy', 'zus', 'merchandise'
    ]
    return fuzzy_match(question, product_keywords)

def should_search_outlets(question: str) -> bool:
    """Check if question is about outlets/locations"""
    outlet_keywords = [
        'outlet', 'location', 'store', 'shop', 'address', 'where', 'near', 
        'nearest', 'branch', 'city', 'area', 'zone', 'kuala lumpur', 'selangor',
        'mall', 'visit', 'open', 'hours', 'available', 'find', 'buy', 'purchase'
    ]
    return fuzzy_match(question, outlet_keywords)
