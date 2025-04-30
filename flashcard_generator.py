import os
import csv
import time
import logging
import argparse
import requests
from typing import List, Dict, Tuple, Optional
import openai
from io import BytesIO
from PIL import Image
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/flashcard_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PEXELS_API_KEY = "YOUR_PEXELS_API_KEY"  # Replace with your Pexels API key

class FlashcardGenerator:
    def __init__(self, api_key: str, output_dir: str = "output"):
        """Initialize the flashcard generator with OpenAI API key and output directory."""
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
    
    def read_words(self, filepath: str) -> List[str]:
        """Read words from a text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                words = [word.strip() for word in file.readlines() if word.strip()]
            logger.info(f"Read {len(words)} words from {filepath}")
            return words
        except Exception as e:
            logger.error(f"Error reading words from {filepath}: {e}")
            return []
    
    def generate_definition(self, word: str) -> str:
        """Generate a definition for a word using OpenAI API."""
        try:
            prompt = f"""
            Word: {word}

            Please provide a clear, natural-sounding definition of this word in Bosnian/Croatian/Serbian (ijekavian variant).

            If the word is not in its canonical form, convert it to the canonical form (nominative for nouns,
            infinitive for verbs) before defining it.

            The definition can be one or more sentences, depending on the complexity or abstractness of the word.

            Use cloze formatting around only the word being defined, like {{c1::riječ}}.

            Use everyday, idiomatic language — do not sound like a dictionary. Do not include headings, synonyms,
            bullet points, or extra formatting. Just the definition.

            Example:
            Input: "činom"
            Output: {{c1::Čin}} je radnja ili djelo koje neko namjerno izvrši. Može biti dobar, loš, svjestan ili nepromišljen.
            """

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            definition = response.choices[0].message.content.strip()
            logger.info(f"Generated definition for '{word}'")
            return definition
        
        except Exception as e:
            logger.error(f"Error generating definition for '{word}': {e}")
            return ""
    
    def generate_examples(self, word: str) -> List[str]:
        """Generate example sentences using OpenAI API."""
        try:
            prompt = f"""
            Word: {word}

            Please provide 2–5 example sentences in Bosnian/Croatian/Serbian (ijekavian variant)
            showing different meanings and usage of this word. Provide more examples if the word
            is abstract or has multiple meanings.

            Use the word in its canonical form (e.g., nominative for nouns, infinitive for verbs), even
            if the input is in a different form.

            Use cloze formatting ({{c1::...}}) around only the word being defined in each sentence.

            Each sentence should be natural, idiomatic, and positive or life-affirming when appropriate.
            Avoid overly complex or unnatural phrasing.

            Do not include any numbering, bullet points, or explanations — just a list of clean
            example sentences, each on a new line.

            Example:
            Input: "čin"
            Output:
            {{c1::Čin}} hrabrosti je prepoznat i nagrađen.  
            Njegov {{c1::čin}} nije prošao nezapaženo u zajednici.  
            Svaki {{c1::čin}} ima svoje posljedice, bilo dobre ili loše.
            """

            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Process the response to extract examples
            examples = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                examples.append(line)
            
            logger.info(f"Generated {len(examples)} examples for '{word}'")
            return examples
        
        except Exception as e:
            logger.error(f"Error generating examples for '{word}': {e}")
            return []
    
    def get_image(self, word: str) -> Optional[str]:
        """Get an appropriate image for the word - either from web sources for concrete nouns
        or generated with DALL-E for abstract concepts."""
        try:
            # First, have GPT determine if the word is concrete or abstract
            prompt = f"""
            Word: {word}

            Determine if this word represents:
            1. A simple, concrete, visible object (like 'jabuka', 'mačka', 'kuća')
            2. An abstract concept, action, quality, emotion, or complex idea (like 'ljubav', 'misliti', 'sloboda')

            Respond with only one word: either SIMPLE or COMPLEX (in all caps, no punctuation or explanation).

            If unsure, choose COMPLEX.
            """

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            word_type = response.choices[0].message.content.strip().upper()
            logger.info(f"Word '{word}' classified as: {word_type}")
            
            image_path = os.path.join(self.output_dir, f"{word}_image.png")
            
            # For simple concrete words, fetch from the web
            if "SIMPLE" in word_type:
                return self._get_web_image(word, image_path)
            # For complex abstract words, generate with DALL-E
            else:
                return self._generate_dalle_image(word, None, image_path)
            
        except Exception as e:
            logger.error(f"Error getting image for '{word}': {e}")
            return None

    def _get_web_image(self, word: str, image_path: str) -> Optional[str]:
        """Get an image from the Pexels API for concrete objects."""
        try:
            # Pexels API endpoint and headers
            api_url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": PEXELS_API_KEY
            }
            
            # Search for images using the word
            params = {
                "query": word,
                "per_page": 1  # Get only one image
            }
            
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the response to get the image URL
            data = response.json()
            if not data['photos']:
                logger.warning(f"No images found for '{word}' on Pexels.")
                return None
            
            image_url = data['photos'][0]['src']['original']
            logger.info(f"Found image URL for '{word}': {image_url}")
            
            # Download and save the image
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            img.save(image_path)
            
            logger.info(f"Retrieved Pexels image for '{word}' to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error getting Pexels image for '{word}': {e}")
            return None

    def _generate_dalle_image(self, word: str, image_path: str) -> Optional[str]:
        """Generate an image using DALL-E for abstract concepts."""
        try:
            # Create a detailed prompt for DALL-E based on the word
            prompt = f"""
            Create a clear, simple image that visually represents the meaning of the BCS (Bosnian/Croatian/Serbian) word: "{word}"
            
            Important:
            - NO English words in the image
            - Do not include the word being defined in the image
            - Focus on the core meaning, not literal translation.
            - If the word is abstract, express the *feeling* or symbolic meaning creatively
            - If the word has multiple meanings, try to represent them all in a single image
            - If the word is a verb or implies time-based action, consider a multi-panel (comic strip) layout to show sequence
            """
            
            logger.info(f"Generating DALL-E image for '{word}'")
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download and save the image
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img.save(image_path)
            
            logger.info(f"Generated and saved DALL-E image for '{word}' to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error generating DALL-E image for '{word}': {e}")
            return None
    
    def create_anki_cards(self, word: str, definition: str, examples: List[str], image_path: str) -> List[Dict]:
        """Create Anki flashcards for a word with definition, examples, and image."""
        cards = []
        
        # Card 1: Definition cloze
        definition_card = {
            "text": f"{{{{c1::{word}}}}} - {definition}",
            "type": "cloze"
        }
        cards.append(definition_card)
        
        # Card 2: Examples cloze
        examples_text = "\n".join([f"• {example.replace(word, f'{{{{c1::{word}}}}}')}" for example in examples])
        examples_card = {
            "text": examples_text,
            "type": "cloze"
        }
        cards.append(examples_card)
        
        # Card 3: Word to image
        image_card = {
            "front": word,
            "back": f'<img src="{image_path}">',
            "type": "basic"
        }
        cards.append(image_card)
        
        return cards
    
    def generate_flashcards(self, words_file: str) -> None:
        """Generate flashcards for all words in the input file."""
        words = self.read_words(words_file)
        if not words:
            logger.error("No words found in input file.")
            return
        
        all_cards = []
        
        for word in words:
            try:
                logger.info(f"Processing word: {word}")
                
                # Generate definition
                definition = self.generate_definition(word)
                if not definition:
                    logger.warning(f"Skipping word '{word}' due to missing definition")
                    continue
                
                # Generate examples
                examples = self.generate_examples(word)
                if not examples:
                    logger.warning(f"Skipping word '{word}' due to missing examples")
                    continue
                
                # Get appropriate image (web or DALL-E)
                image_path = self.get_image(word)
                if not image_path:
                    logger.warning(f"Skipping word '{word}' due to missing image")
                    continue
                
                # Create Anki cards
                cards = self.create_anki_cards(word, definition, examples, os.path.basename(image_path))
                all_cards.extend(cards)
                
                # Respect API rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing word '{word}': {e}")
                continue
        
        # Write all cards to CSV
        self.write_to_csv(all_cards)
    
    def write_to_csv(self, cards: List[Dict]) -> None:
        """Write flashcards to a CSV file for Anki import."""
        try:
            csv_path = os.path.join(self.output_dir, "flashcards.csv")
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as file:
                # Determine all possible fields from all cards
                fieldnames = set()
                for card in cards:
                    fieldnames.update(card.keys())
                
                fieldnames = list(fieldnames)
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(cards)
            
            logger.info(f"Wrote {len(cards)} flashcards to {csv_path}")
        
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate Anki flashcards from BCS words.')
    parser.add_argument('--words', type=str, default='words.txt', help='Path to the input words file')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    
    args = parser.parse_args()
    
    generator = FlashcardGenerator(api_key=args.api_key, output_dir=args.output)
    generator.generate_flashcards(args.words)

if __name__ == "__main__":
    main() 