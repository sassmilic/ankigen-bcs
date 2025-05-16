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

from monoprompt import PROMPT

load_dotenv()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANKI_COLLECTION_FILE_PATH = os.path.expanduser(os.environ.get("ANKI_COLLECTION_FILE_PATH"))

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
        self.api_key = OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        self.output_dir = output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

    def read_words(self, filepath: str) -> List[str]:
        with open(filepath, 'r', encoding='utf-8') as file:
            return [word.strip() for word in file.readlines() if word.strip()]

    def api_request(self, model: str, messages: list, temperature: float, max_tokens: int = None):
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                time.sleep(0.12)
                return response
            except openai.error.RateLimitError as e:
                logger.warning(f"Rate limit exceeded, waiting 30 seconds: {e}")
                time.sleep(30)
            except Exception as e:
                logger.error(f"API error: {e}")
                return None

    def batch_process_words(self, words: List[str]) -> List[Dict]:
        word_list = ", ".join(words)
        prompt = PROMPT.format(word_list=word_list)
        
        logger.info(f"Sending batch request to OpenAI API for {len(words)} words...")
        logger.info(f"This may take a moment, please wait...")
        
        response = self.api_request(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            #max_tokens=400 * len(words) # TODO: put tokens per word in config
        )
        
        logger.info(f"Received response from OpenAI API")

        print("--------------------------------")
        print(response.choices[0].message.content)
        print("--------------------------------")

        if not response:
            logger.error("API request returned empty response")
            return []

        try:
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return []

    def process_words_in_batches(self, words: List[str], batch_size: int = 10) -> List[Dict]:
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
                logger.info(f"Waiting 3 seconds before next batch...")
                time.sleep(3)
                
        return results

    def get_image(self, word: str, word_type: str, translation: str) -> Optional[str]:
        if word_type == "SIMPLE":
            return self._get_web_image(word, translation)
        else:
            image_path = os.path.join(ANKI_COLLECTION_FILE_PATH, f"{word}_image.png")
            return self._generate_image(word, image_path)

    def _get_web_image(self, word: str, translation: str) -> Optional[str]:
        try:
            api_url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": translation, "per_page": 1}
            response = requests.get(api_url, headers=headers, params=params)
            data = response.json()
            if not data['photos']:
                return None
            image_url = data['photos'][0]['src']['original']
            image_path = os.path.join(ANKI_COLLECTION_FILE_PATH, f"{word}_image.png")
            img = Image.open(BytesIO(requests.get(image_url).content))
            img.save(image_path)
            return image_path
        except Exception as e:
            logger.error(f"Pexels image error for '{word}': {e}")
            return None

    def _generate_image(self, word: str, image_path: str) -> Optional[str]:
        try:
            prompt = f"Create a symbolic image representing the word: '{word}'"
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024"
            )
            image_url = response.data[0].url
            img = Image.open(BytesIO(requests.get(image_url).content))
            img.save(image_path)
            return image_path
        except Exception as e:
            logger.error(f"AI image generation failed for '{word}': {e}")
            return None

    def create_anki_cards(self, word_obj: Dict, image_path: str) -> List[Dict]:
        cards = []
        word = word_obj["canonical_form"]

        cards.append({"word": word, "text": word_obj["definition"], "type": "cloze"})
        examples_text = "<ul>" + "".join(["<li>" + ex + "</li>" for ex in word_obj["example_sentences"]]) + "</ul>"
        cards.append({"word": word, "text": examples_text, "type": "cloze"})
        cards.append({"front": word, "back": f'<img src="{image_path}">', "type": "basic"})
        return cards

    def generate_flashcards(self, words_file: str, batch_size: int = 10) -> None:
        words = self.read_words(words_file)
        all_cards = []
        
        logger.info(f"Processing {len(words)} words in batches of {batch_size}")
        results = self.process_words_in_batches(words, batch_size)
        
        logger.info(f"Creating flashcards for {len(results)} processed words")
        for word_obj in results:
            word = word_obj.get("canonical_form")
            if not word:
                continue
            translation = word_obj.get("translation", word)
            logger.info(f"Processing word '{word}' with translation '{translation}'")
            image_path = self.get_image(word, word_obj.get("word_type"), translation)
            if not image_path:
                continue
            cards = self.create_anki_cards(word_obj, os.path.basename(image_path))
            all_cards.extend(cards)

        self.write_to_csv(all_cards)

    def write_to_csv(self, cards: List[Dict]) -> None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.output_dir, f"flashcards_{timestamp}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            file.write('#separator:Tab\n')
            file.write('#html:true\n')
            file.write('#notetype column:1\n')
            fieldnames = ['type', '2', '3']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
            for card in cards:
                if card["type"] == "basic":
                    writer.writerow({"type": "Basic", "2": card["front"], "3": card["back"]})
                    writer.writerow({"type": "Basic", "2": card["back"], "3": card["front"]})
                elif card["type"] == "cloze":
                    writer.writerow({"type": "Cloze", "2": card["text"]})
        logger.info(f"Wrote {len(cards)} flashcards to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate Anki flashcards from BCS words.')
    parser.add_argument('--words', type=str, default='words.txt', help='Path to the input words file')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of words to process in each batch')
    args = parser.parse_args()
    generator = FlashcardGenerator(output_dir=args.output)
    generator.generate_flashcards(args.words, args.batch_size)

if __name__ == "__main__":
    main()
