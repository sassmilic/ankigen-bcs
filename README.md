# ankigen-bcs

This tool generates Anki flashcards for learning Bosnian/Croatian/Serbian (BCS) vocabulary from a given list of words.

For each word, it creates four types of flashcards:

1. Definition (cloze deletion) – a definition in BCS with the target word hidden.
2. Example sentences (cloze deletion) – 3–5 sentences using the word in context, with the word hidden.
3. Image-to-word
4. Word-to-image

Images are either retrieved from Pexels or AI-generated, depending on the word type.

The output is a CSV file formatted for batch importing into Anki.

## Usage

### Setup

1. Clone this repository
2. Copy `.env-example` to `.env` and fill in your configuration details
3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `words.txt` file with one word per line that you want to generate flashcards for.
5. Run the flashcard generator script:

```
python flashcard_generator.py
```

## TODO

- deal with duplicates (i.e. don't regenerate)
- ~~parallelize requests~~
- ~~consider just using a single prompt per word (mono-prompt hehe)~~
- organize output files /& directories
- consider widening the types of words that can be represented with simple online images, i.e. don't need to be generated.
- cut costs
  - ~~batch generation (i.e. send all words with one prompt)~~
  - ~~shorten/compress prompts~~
  - leverage pexel more; generate fewer images
