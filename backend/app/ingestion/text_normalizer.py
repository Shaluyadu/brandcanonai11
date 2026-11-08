import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Deterministic text normalization preserving paragraph structure and original semantic meaning.
    - Normalizes Unicode (NFC)
    - Replaces non-breaking and irregular spaces with standard space
    - Normalizes typographer quotes/dashes to standard characters
    - Prunes excessive empty lines while preserving paragraph boundaries
    """
    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Standardize quotation marks and dashes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("—", " - ").replace("–", " - ")

    # Replace irregular whitespace with standard space
    text = re.sub(r"[\r\t\f\v]", " ", text)
    text = text.replace("\xa0", " ")

    # Collapse horizontal whitespace
    text = re.sub(r"[ ]{2,}", " ", text)

    # Clean multiple consecutive line breaks (preserve max double newline for paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

