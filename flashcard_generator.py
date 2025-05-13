import argparse
import csv
import logging
import os
import sys
import time
from io import BytesIO
from typing import List, Dict, Optional

import openai
import requests
from PIL import Image
from dotenv import load_dotenv

# Import prompts
from prompts import (
    DEFINITION_PROMPT,
    EXAMPLES_PROMPT,
    WORD_TYPE_PROMPT,
    TRANSLATION_PROMPT,
    IMAGE_GENERATION_PROMPT,
    CANONICALIZATION_PROMPT
)

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Define global variable for Anki collection path
ANKI_COLLECTION_FILE_PATH = os.path.expanduser(os.environ.get("ANKI_COLLECTION_FILE_PATH"))

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

class FlashcardGenerator:
    def __init__(self, output_dir: str = "output"):
        """Initialize the flashcard generator with OpenAI API key and output directory."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
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
    
    def api_request(self, model: str, messages: list, temperature: float, max_tokens: int):
        """Wrapper for OpenAI API requests with error handling and retry logic."""
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                # Respect API rate limits
                time.sleep(0.12)  # Wait 120 milliseconds to ensure no more than 500 requests per minute
                return response
            
            except openai.error.RateLimitError as e:
                if e.http_status == 429 and e.error.code == 'insufficient_quota':
                    logger.error("Insufficient quota. Exiting program.")
                    sys.exit(1)
                else:
                    logger.warning(f"Rate limit error: {e}. Retrying in 0.12 seconds.")
                    time.sleep(0.12)  # Wait before retrying
            
            except Exception as e:
                logger.error(f"Error during API request: {e}")
                return None

    def generate_definition(self, word: str) -> str:
        """
        Generate a definition for a word using OpenAI API.
        
        Precondition: The word is spelled correctly (including diacritics)
        and in canonical form (nominative case if noun and infinitive if verb).
        """

        prompt = DEFINITION_PROMPT.format(word=word)

        response = self.api_request(
            model="o4-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        if response:
            definition = response.choices[0].message.content.strip()
            logger.info(f"Generated definition for '{word}'")
            return definition
        else:
            logger.error(f"Failed to generate definition for '{word}'")
            return ""
    
    def generate_examples(self, word: str) -> List[str]:
        """Generate example sentences using OpenAI API."""
        try:
            prompt = EXAMPLES_PROMPT.format(word=word)
            
            response = self.client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Process the response to extract examples
            examples = []
            for line in content.strip().split('\n'):
                # Log the line for debugging
                logger.debug("Processing example line: " + line)
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
        or generated with AIfor abstract concepts."""
        try:
            # First, have GPT determine if the word is concrete or abstract
            prompt = WORD_TYPE_PROMPT.format(word=word)

            response = self.client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            word_type = response.choices[0].message.content.strip().upper()
            logger.info(f"Word '{word}' classified as: {word_type}")
            
            # For simple concrete words, fetch from the web
            if "SIMPLE" in word_type:
                return self._get_web_image(word)
            # For complex abstract words, generate image with AI
            else:
                image_path = os.path.join(ANKI_COLLECTION_FILE_PATH, f"{word}_image.png")
                return self._generate_image(word, image_path)
            
        except Exception as e:
            logger.error(f"Error getting image for '{word}': {e}")
            return None

    def _get_web_image(self, word: str) -> Optional[str]:
        """Get an image from the Pexels API for concrete objects."""
        try:
            # First, translate the word to English using ChatGPT
            translation_prompt = TRANSLATION_PROMPT.format(word=word)
            translation_response = self.api_request(
                model="o4-mini",
                messages=[{"role": "user", "content": translation_prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            if translation_response:
                translated_word = translation_response.choices[0].message.content.strip()
                logger.info(f"Translated '{word}' to '{translated_word}'")
            else:
                logger.error(f"Failed to translate '{word}'")
                return None

            # Pexels API endpoint and headers
            api_url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": PEXELS_API_KEY
            }
            
            # Search for images using the translated word
            params = {
                "query": translated_word,
                "per_page": 1  # Get only one image
            }
            
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the response to get the image URL
            data = response.json()
            if not data['photos']:
                logger.warning(f"No images found for '{translated_word}' on Pexels.")
                return None
            
            image_url = data['photos'][0]['src']['original']
            logger.info(f"Found image URL for '{translated_word}': {image_url}")
            
            # Define the image path
            image_path = os.path.join(ANKI_COLLECTION_FILE_PATH, f"{word}_image.png")
            
            # Download and save the image
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            logger.info(f"Saving image to {image_path}")
            img.save(image_path)
            
            logger.info(f"Retrieved Pexels image for '{word}' to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error getting Pexels image for '{word}': {e}")
            return None

    def _generate_image(self, word: str, image_path: str) -> Optional[str]:
        """Generate an image using AI for abstract concepts."""
        try:
            prompt = IMAGE_GENERATION_PROMPT.format(word=word)

            logger.info(f"Generating image for '{word}'")
            response = self.client.images.generate(
                model="dall-e-3", # TODO: change to "gpt-image-1"
                prompt=prompt,
            )
            
            image_url = response.data[0].url
            
            # Download and save the image
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img.save(image_path)
            
            logger.info(f"Generated and saved image for '{word}' to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error generating image for '{word}': {e}")
            return None
    
    def create_anki_cards(self, word: str, definition: str, examples: List[str], image_path: str) -> List[Dict]:
        """Create Anki flashcards for a word with definition, examples, and image."""
        cards = []
        
        # Card 1: Definition cloze
        definition_card = {
            "word": word,
            "text": definition,
            "type": "cloze"
        }
        cards.append(definition_card)
        
        # Card 2: Examples cloze
        examples_text = "<ul>" + "".join(["<li>" + example + "</li>" for example in examples]) + "</ul>"
        examples_card = {
            "word": word,
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
    
    def preprocess_words(self, words: List[str]) -> List[str]:
        """Preprocess words to ensure they are in canonical form with correct diacritics."""
        try:
            logger.info(f"Preprocessing {len(words)} words to canonical form")
            
            # Join the words into a single string for the prompt
            words_text = "\n".join(words)
            
            # Create the prompt with the words
            prompt = CANONICALIZATION_PROMPT.format(words=words_text)
            
            # Send to language model
            response = self.api_request(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            if not response:
                logger.error("Failed to preprocess words, using original words")
                return words
            
            # Process the response to get canonicalized words
            processed_content = response.choices[0].message.content.strip()
            canonicalized_words = [word.strip() for word in processed_content.split('\n') if word.strip()]
            
            logger.info(f"Preprocessed {len(words)} words to {len(canonicalized_words)} canonical forms")
            
            # Log the changes for review
            for original, canonical in zip(words, canonicalized_words):
                if original != canonical:
                    logger.info(f"Word changed: '{original}' → '{canonical}'")
            
            return canonicalized_words
            
        except Exception as e:
            logger.error(f"Error preprocessing words: {e}")
            logger.warning("Using original words due to preprocessing error")
            return words
    
    def generate_flashcards(self, words_file: str) -> None:
        """Generate flashcards for all words in the input file."""
        raw_words = self.read_words(words_file)
        if not raw_words:
            logger.error("No words found in input file.")
            return
        
        # Preprocess words to canonical form
        words = self.preprocess_words(raw_words)
        logger.info(f"Starting flashcard generation for {len(words)} preprocessed words")
        
        all_cards = []
        successful_words = []
        skipped_words = {}  # Dictionary to track skipped words and reasons

        for word in words:
            try:
                logger.info(f"Processing word: {word}")
                
                # Generate definition
                definition = self.generate_definition(word)
                if not definition:
                    logger.warning(f"Skipping word '{word}' due to missing definition")
                    skipped_words[word] = "missing definition"
                    continue
                
                # Generate examples
                examples = self.generate_examples(word)
                if not examples:
                    logger.warning(f"Skipping word '{word}' due to missing examples")
                    skipped_words[word] = "missing examples"
                    continue
                
                # Get appropriate image (web or AI-gen)
                image_path = self.get_image(word)
                if not image_path:
                    logger.warning(f"Skipping word '{word}' due to missing image")
                    skipped_words[word] = "missing image"
                    continue
                
                # Create Anki cards
                cards = self.create_anki_cards(word, definition, examples, os.path.basename(image_path))
                all_cards.extend(cards)
                successful_words.append(word)
                
            except Exception as e:
                logger.error(f"Error processing word '{word}': {e}")
                skipped_words[word] = f"error: {str(e)}"
                continue
        
        # Write all cards to CSV
        self.write_to_csv(all_cards)
        
        # Log summary
        card_count = len(all_cards)
        logger.info("=" * 50)
        logger.info(f"FLASHCARD GENERATION SUMMARY:")
        logger.info(f"Successfully processed {len(successful_words)} words")
        logger.info(f"Generated {card_count} flashcards")
        
        if skipped_words:
            logger.info(f"Skipped {len(skipped_words)} words:")
            for word, reason in skipped_words.items():
                logger.info(f"  - '{word}': {reason}")
        logger.info("=" * 50)
    
    def write_to_csv(self, cards: List[Dict]) -> None:
        """Write flashcards to a CSV file for Anki import."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            csv_path = os.path.join(self.output_dir, f"flashcards_{timestamp}.csv")
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as file:
                # Write headers for Anki import
                file.write('#separator:Tab\n')
                file.write('#html:true\n')
                file.write('#notetype column:1\n')
                
                # Define the fieldnames for the CSV
                fieldnames = ['type', '2', '3']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
                #writer.writeheader()
                
                # IMPORTANT: According to Anki documentation:
                # "Anki determines the number of fields in the file by looking at the first (non-commented) line.
                # If some of the later records in the file contain fewer fields, Anki will treat the missing fields
                # as if they were blank. If some of your records contain extra fields, the extra content will not
                # be imported."
                #
                # Therefore, we must put the card type with more fields (basic) first to ensure all fields are properly
                # recognized during import.
                for card in cards:
                    # Map the card dictionary to the CSV format
                    if card["type"] == "basic":
                        writer.writerow({
                            'type': "Basic",
                            '2': card.get('front'),
                            '3': card.get('back')
                        })
                        writer.writerow({
                            'type': "Basic",
                            '2': card.get('back'),
                            '3': card.get('front')
                        })
                    elif card["type"] == "cloze":
                        writer.writerow({
                            'type': "Cloze",
                            '2': card.get('text'),
                        })
            
            logger.info(f"Wrote {len(cards) * 4/3} flashcards to {csv_path}")
        
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate Anki flashcards from BCS words.')
    parser.add_argument('--words', type=str, default='words.txt', help='Path to the input words file')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    
    args = parser.parse_args()
    
    generator = FlashcardGenerator(output_dir=args.output)
    generator.generate_flashcards(args.words)

if __name__ == "__main__":
    main() 