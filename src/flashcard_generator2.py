import argparse
import base64
import csv
import json
import logging
import os
import re
import threading
import time
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import openai
import requests
from PIL import Image
from dotenv import load_dotenv

from prompts import (
    IMAGE_GENERATION_PROMPT,
    PROMPT_WORD_METADATA,
    PROMPT_WORD_DEFINITION,
    PROMPT_EXAMPLE_SENTENCES,
)

# Import the new config module
import config

# Helper function to ensure a directory exists
def _ensure_dir_exists(file_path: str):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

# Ensure essential directories exist before logging or other operations
_ensure_dir_exists(config.LOG_FILE_PATH)
_ensure_dir_exists(config.HISTORY_FILE_PATH)
if config.ANKI_COLLECTION_FILE_PATH: # ANKI_COLLECTION_FILE_PATH is a directory itself
    os.makedirs(config.ANKI_COLLECTION_FILE_PATH, exist_ok=True)


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HISTORY_FILE = "../output/flashcard_history.jsonl" # Moved to config

def load_history() -> Dict[str, Dict]:
    if not os.path.exists(config.HISTORY_FILE_PATH):
        return {}
    with open(config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
        return {entry['canonical_form']: entry for entry in map(json.loads, f)}

def save_history_entry(entry: Dict):
    with open(config.HISTORY_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + "\n")

class FlashcardGenerator:
    def __init__(self, output_dir: str = None, simple_nouns: bool = False):
        self.api_key = config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        self.output_dir = output_dir if output_dir is not None else config.DEFAULT_OUTPUT_DIR
        self.simple_nouns = simple_nouns
        
        # Rate limiting for image generation
        self.image_rate_limit = config.IMAGE_API_RATE_LIMIT
        self.image_rate_period = config.IMAGE_API_RATE_PERIOD
        self.image_lock = threading.Lock()
        self.last_image_timestamps = []

        # Ensure the specific output_dir for CSVs exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory for CSVs: {self.output_dir}")

    def read_words(self, filepath: str) -> List[str]:
        with open(filepath, 'r', encoding='utf-8') as file:
            return [word.strip() for word in file.readlines() if word.strip() and not word.strip().startswith('#')]

    def api_request(self, model: str, messages: list, temperature: float, max_tokens: int = None):
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            except openai.error.RateLimitError as e:
                logger.warning(f"Rate limit exceeded, waiting {config.API_RETRY_DELAY} seconds: {e}")
                time.sleep(config.API_RETRY_DELAY)
            except Exception as e:
                logger.error(f"API error: {e}")
                return None

    def _make_api_call_and_parse(self, prompt_content: str, model: str, temperature: float, word_count: int) -> Optional[List[Dict]]:
        """Helper function to make an API call and parse its JSON response.
        
        Makes an API request with the given prompt and parses the JSON response.
        Logs debug information about the request and response.
        
        Args:
            prompt_content: The prompt text to send to the API
            model: The model name to use for the request
            temperature: The temperature setting for response generation
            word_count: Number of words being processed (for logging)
            
        Returns:
            List of dictionaries parsed from the JSON response, or None if parsing fails
            
        Raises:
            JSONDecodeError: If the response cannot be parsed as valid JSON
            ValueError: If the parsed JSON is not a list as expected
        """
        logger.debug(f"Sending API request with prompt content:\n{prompt_content[:500]}...") # Log beginning of prompt
        response = self.api_request(
            model=model,
            messages=[{"role": "user", "content": prompt_content}],
            temperature=temperature
            # max_tokens could be set here if needed, e.g., based on word_count and prompt type
        )

        if not response or not response.choices:
            logger.error("API request returned empty or invalid response for a sub-prompt.")
        
        content = response.choices[0].message.content
        logger.debug(f"Raw API response content for sub-prompt:\n{content}")

        try:
            # The prompt asks for raw JSON array, so no need to strip ```json ... ```
            parsed_json = json.loads(content)
            if not isinstance(parsed_json, list):
                logger.error(f"Parsed JSON is not a list as expected. Content: {content}")
            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from sub-prompt response: {e}\nContent was: {content}")

    def batch_process_words(self, words: List[str]) -> List[Dict]:
        if not words:
            return []
            
        word_list_str = ", ".join(f'"{w}"' for w in words) # Ensure words are quoted if they contain spaces/special chars for the list
        model = config.GPT_MODEL 
        temperature = config.GPT_TEMPERATURE

        merged_data = {word: {"word": word} for word in words}
        
        # --- 1. Structural Data ---
        logger.info(f"Requesting structural data for {len(words)} words...")
        prompt_structural_content = PROMPT_WORD_METADATA.format(word_list=word_list_str)
        structural_results = self._make_api_call_and_parse(prompt_structural_content, model, temperature, len(words))
        
        if structural_results:
            for item in structural_results:
                original_word = item.get("word")
                if original_word and original_word in merged_data:
                    merged_data[original_word].update(item)
                elif original_word:
                    logger.warning(f"Word '{original_word}' from structural response not in original batch: {words}")
                else:
                    logger.warning(f"Item from structural response missing 'word' key: {item}")
        else:
            logger.error(f"Failed to get structural data for batch starting with '{words[0] if words else 'N/A'}'. This batch will be skipped.")
            return []

        # --- 2. Semantic Data (Definition) ---
        if not self.simple_nouns:
            logger.info(f"Requesting semantic data (definitions) for {len(words)} words...")
            prompt_semantic_content = PROMPT_WORD_DEFINITION.format(word_list=word_list_str)
            semantic_results = self._make_api_call_and_parse(prompt_semantic_content, model, temperature, len(words))

            if semantic_results:
                for item in semantic_results:
                    original_word = item.get("word")
                    if original_word and original_word in merged_data:
                        merged_data[original_word].update(item)
                    elif original_word:
                        logger.warning(f"Word '{original_word}' from semantic response not in original batch: {words}")
                    else:
                        logger.warning(f"Item from semantic response missing 'word' key: {item}")
            else:
                logger.error(f"Failed to get semantic data for batch starting with '{words[0] if words else 'N/A'}'. This batch will be skipped.")
                return []
        else:
            logger.info(f"Skipping definition generation for {len(words)} simple nouns...")
        
        # --- 3. Stylistic Data (Examples) ---
        if not self.simple_nouns:
            logger.info(f"Requesting stylistic data (example sentences) for {len(words)} words...")
            prompt_stylistic_content = PROMPT_EXAMPLE_SENTENCES.format(word_list=word_list_str)
            stylistic_results = self._make_api_call_and_parse(prompt_stylistic_content, model, temperature, len(words))

            if stylistic_results:
                for item in stylistic_results:
                    original_word = item.get("word")
                    if original_word and original_word in merged_data:
                        merged_data[original_word].update(item)
                    elif original_word:
                        logger.warning(f"Word '{original_word}' from stylistic response not in original batch: {words}")
                    else:
                        logger.warning(f"Item from stylistic response missing 'word' key: {item}")
            else:
                logger.error(f"Failed to get stylistic data for batch starting with '{words[0] if words else 'N/A'}'. This batch will be skipped.")
                return []
        else:
            logger.info(f"Skipping example sentence generation for {len(words)} simple nouns...")

        # Assemble final results for the batch, ensuring all parts are present
        final_batch_results = []
        for word_str in words:
            data = merged_data.get(word_str)
            # Check for essential keys from each prompt's contribution
            # The 'word' key is already used for merging and is implicitly required.
            if data and \
               all(k in data for k in ["canonical_form", "part_of_speech", "word_type", "translation"]):
                
                # For simple nouns, we don't need definition and example_sentences
                if self.simple_nouns:
                    # Add empty definition and example_sentences for simple nouns
                    data["definition"] = ""
                    data["example_sentences"] = []
                else:
                    # For complex words, require definition and example_sentences
                    if "definition" not in data or "example_sentences" not in data:
                        logger.warning(f"Word '{word_str}' is missing definition or example_sentences and will be skipped. Collected data: {data}")
                        continue
                
                # Log the word and its translation
                canonical_form = data.get("canonical_form", word_str) # Use canonical_form if available
                translation = data.get("translation")
                if translation:
                    logger.info(f"Processed: '{canonical_form}' -> Translation: '{translation}'")
                else:
                    logger.info(f"Processed: '{canonical_form}' (No translation found in data)")
                final_batch_results.append(data)
            else:
                logger.warning(f"Word '{word_str}' is missing some data after merging and will be skipped. Collected data: {data}")
        
        if final_batch_results:
            logger.info(f"Successfully processed and merged data for {len(final_batch_results)} out of {len(words)} words in the batch.")
        elif words: # If words were provided but no results, it means all failed or were incomplete
             logger.warning(f"No words from batch starting with '{words[0]}' could be fully processed.")


        return final_batch_results

    def process_words_in_batches(self, words: List[str], batch_size: int = config.DEFAULT_BATCH_SIZE) -> List[Dict]:
        """Process words in batches of specified size."""
        results = []
        total_words = len(words)
        
        for i in range(0, total_words, batch_size):
            batch = words[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_words + batch_size - 1)//batch_size}: {len(batch)} words")
            batch_results = self.batch_process_words(batch)
            results.extend(batch_results)
            
            # Add a small delay between batches to avoid rate limiting
            if i + batch_size < total_words:
                logger.info(f"Waiting {config.INTER_BATCH_DELAY} seconds before next batch...")
                time.sleep(config.INTER_BATCH_DELAY)
                
        return results

    def get_image(self, word: str, word_type: str, translation: str, word_obj: Dict = None) -> Optional[str]:
        if word_obj is None:
            word_obj = {
                "canonical_form": word,
                "translation": translation,
                "word_type": word_type
            }
        
        if word_type == "SIMPLE":
            return self._get_web_image(word, translation)
        else:
            # Find existing image files for this word and determine the next number
            image_dir = config.ANKI_COLLECTION_FILE_PATH
            if not image_dir:
                logger.error("ANKI_COLLECTION_FILE_PATH is not set in config. Cannot save AI generated images.")
                return None
            existing_files = [f for f in os.listdir(image_dir) if f.startswith(f"{word}_image")]
            
            # Get the numbers from existing files
            numbers = []
            for file in existing_files:
                # Check for numbered image files
                match = re.search(r'_image_(\d+)\.png$', file)
                if match:
                    numbers.append(int(match.group(1)))
                # Check for the base image file without number
                elif file == f"{word}_image.png":
                    numbers.append(0)  # Treat base filename as number 0
            
            # Determine next number
            next_num = 1 if not numbers else max(numbers) + 1
            
            # Create the new filename
            if next_num == 1 and f"{word}_image.png" not in existing_files:
                new_filename = f"{word}_image.png"
            else:
                new_filename = f"{word}_image_{next_num}.png"
            
            image_path = os.path.join(image_dir, new_filename)
            return self._generate_image(word, image_path, word_obj)

    def _get_web_image(self, word: str, translation: str) -> Optional[str]:
        try:
            api_url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": config.PEXELS_API_KEY}
            params = {"query": translation, "per_page": 1}
            response = requests.get(api_url, headers=headers, params=params)
            data = response.json()
            if not data['photos']:
                return None
            image_url = data['photos'][0]['src']['original']
            image_path = os.path.join(config.ANKI_COLLECTION_FILE_PATH, f"{word}_image.png")
            if not config.ANKI_COLLECTION_FILE_PATH:
                logger.error("ANKI_COLLECTION_FILE_PATH is not set in config. Cannot save Pexels image.")
                return None
            img = Image.open(BytesIO(requests.get(image_url).content))
            img.save(image_path)
            return image_path
        except Exception as e:
            logger.error(f"Pexels image error for '{word}': {e}")
            return None

    def _generate_image(self, word: str, image_path: str, word_obj: Dict) -> Optional[str]:
        try:
            # Get the required parameters from the word object
            gloss = word_obj.get("translation", word)
            pos = word_obj.get("part_of_speech")
            
            logger.info(f"Generating AI image for '{word}'")
            
            # Use the updated IMAGE_GENERATION_PROMPT
            prompt = IMAGE_GENERATION_PROMPT.format(word=word, gloss=gloss, pos=pos)
            
            response = self.client.images.generate(
                model=config.IMAGE_GENERATION_MODEL,
                prompt=prompt,
                size=config.IMAGE_SIZE,
                quality=config.IMAGE_QUALITY
            )
            
            # Get the base64 encoded image data
            if response.data[0].b64_json:
                image_base64 = response.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                
                logger.info(f"Successfully generated image for '{word}', saving...")
                
                # Save the image to a file
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                    
                logger.info(f"Saved image for '{word}' to {image_path}")
                return image_path
            else:
                logger.warning(f"Invalid or empty response from API for '{word}'")
                return None
                
        except Exception as e:
            logger.error(f"AI image generation failed for '{word}': {e}")
            return None

    def create_anki_cards(self, word_obj: Dict, image_path: str) -> List[Dict]:
        cards = []
        word = word_obj["canonical_form"]

        if self.simple_nouns:
            # For simple nouns, only create image-to-word cards
            cards.append({"front": word, "back": f'<img src="{image_path}">', "type": "basic"})
        else:
            # For complex words, create all card types
            cards.append({"word": word, "text": word_obj["definition"], "type": "cloze"})
            examples_text = "<ul>" + "".join(["<li>" + ex + "</li>" for ex in word_obj["example_sentences"]]) + "</ul>"
            cards.append({"word": word, "text": examples_text, "type": "cloze"})
            cards.append({"front": word, "back": f'<img src="{image_path}">', "type": "basic"})
        
        return cards

    def generate_flashcards(self, words_file: str, batch_size: int = config.DEFAULT_BATCH_SIZE) -> None:
        words = self.read_words(words_file)
        all_cards = []
        
        if self.simple_nouns:
            logger.info(f"Processing {len(words)} simple concrete nouns in batches of {batch_size} (image-to-word cards only)")
        else:
            logger.info(f"Processing {len(words)} words in batches of {batch_size}")
        
        results = self.process_words_in_batches(words, batch_size)
        
        logger.info(f"Creating flashcards for {len(results)} processed words")

        history = load_history()
        
        # Filter out words that are already in history
        new_word_objects = [word_obj for word_obj in results 
                           if word_obj.get("canonical_form") and word_obj.get("canonical_form") not in history]
        
        if not new_word_objects:
            logger.info("No new words to process")
            return
            
        logger.info(f"Generating images for {len(new_word_objects)} new words")
        
        # Process images one at a time instead of in parallel
        word_to_image = {}
        for word_obj in new_word_objects:
            word = word_obj.get("canonical_form")
            word_type = word_obj.get("word_type")
            translation = word_obj.get("translation", word)
            
            # For simple nouns mode, treat all words as SIMPLE type for image generation
            if self.simple_nouns:
                word_type = "SIMPLE"
            
            # Find existing image files for this word and determine the next number
            if word_type != "SIMPLE":
                if not config.ANKI_COLLECTION_FILE_PATH:
                    logger.warning(f"ANKI_COLLECTION_FILE_PATH not set. Skipping AI image for {word}")
                    image_path = None
                else:
                    image_dir = config.ANKI_COLLECTION_FILE_PATH
                    existing_files = [f for f in os.listdir(image_dir) if f.startswith(f"{word}_image")]
                    
                    # Get the numbers from existing files
                    numbers = []
                    for file in existing_files:
                        # Check for numbered image files
                        match = re.search(r'_image_(\d+)\.png$', file)
                        if match:
                            numbers.append(int(match.group(1)))
                        # Check for the base image file without number
                        elif file == f"{word}_image.png":
                            numbers.append(0)  # Treat base filename as number 0
                    
                    # Determine next number
                    next_num = 1 if not numbers else max(numbers) + 1
                    
                    # Create the new filename
                    if next_num == 1 and f"{word}_image.png" not in existing_files:
                        new_filename = f"{word}_image.png"
                    else:
                        new_filename = f"{word}_image_{next_num}.png"
                    
                    image_path = self.get_image(word, word_type, translation, word_obj)
            else:
                image_path = self.get_image(word, word_type, translation, word_obj)
            
            if image_path:
                word_to_image[word] = image_path
                logger.info(f"Successfully processed image for '{word}'")
            else:
                logger.warning(f"Failed to get image for '{word}'")
        
        # Create flashcards for words with successful image generation
        for word_obj in new_word_objects:
            word = word_obj.get("canonical_form")
            if word not in word_to_image:
                continue
                
            image_path = word_to_image[word]
            cards = self.create_anki_cards(word_obj, os.path.basename(image_path))
            all_cards.extend(cards)
            
            save_history_entry({
                "canonical_form": word,
                "translation": word_obj.get("translation", word),
                "image_path": os.path.basename(image_path),
                "anki_created": True
            })
            
        self.write_to_csv(all_cards)

    def write_to_csv(self, cards: List[Dict]) -> None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.output_dir, f"flashcards_{timestamp}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            file.write(f'#separator:{config.CSV_SEPARATOR}\n')
            file.write(f'#html:{str(config.CSV_HTML_ENABLED).lower()}\n')
            file.write(f'#notetype column:{config.CSV_NOTETYPE_COLUMN}\n')
            fieldnames = ['type', '2', '3']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=config.CSV_SEPARATOR)
            for card in cards:
                if card["type"] == "basic":
                    writer.writerow({"type": "Basic", "2": card["front"], "3": card["back"]})
                    writer.writerow({"type": "Basic", "2": card["back"], "3": card["front"]})
                elif card["type"] == "cloze":
                    writer.writerow({"type": "Cloze", "2": card["text"]})
        logger.info(f"Wrote {len(cards)} flashcards to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate Anki flashcards from BCS words.')
    parser.add_argument('--words', type=str, default=config.DEFAULT_WORDS_FILE, help='Path to the input words file')
    parser.add_argument('--output', type=str, default=config.DEFAULT_OUTPUT_DIR, help='Output directory for CSV flashcards')
    parser.add_argument('--batch-size', type=int, default=config.DEFAULT_BATCH_SIZE, help='Number of words to process in each batch')
    parser.add_argument('--simple-nouns', action='store_true', help='Skip definition and example sentence generation for simple nouns')
    args = parser.parse_args()
    generator = FlashcardGenerator(output_dir=args.output, simple_nouns=args.simple_nouns)
    generator.generate_flashcards(args.words, args.batch_size)

if __name__ == "__main__":
    main()
