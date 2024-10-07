import nltk
from API.schemas import Product
from rake_nltk import Rake
from typing import List
from deep_translator import GoogleTranslator
from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

def extract_keywords(text: str, top_n: int=5) -> List[str]:
    stop_words = stopwords.words('english') + stopwords.words('spanish')

    rake = Rake(stopwords=stop_words)
    rake.extract_keywords_from_text(text)
    ranked_phrases_with_scores = rake.get_ranked_phrases_with_scores()

    keywords = [phrase for score, phrase in ranked_phrases_with_scores[:top_n]]
    return keywords

def describe_product(product: Product) -> str | None:
    if product.read_category is not None and product.read_category.strip():
        return product.read_category
    elif product.title.strip():
        full_text = f"{product.title} - {product.description}"
        keywords = extract_keywords(full_text, 1)
        if keywords:
            return keywords[0]
        else:
            return product.title
    return None

def translate_to_english(text):
    translator = GoogleTranslator(source='auto', target='en')
    translation = translator.translate(text)
    return translation