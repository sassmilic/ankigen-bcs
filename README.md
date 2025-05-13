# ankigen-bcs

auto-generate anki cards for language learning

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
- parallelize requests
- consider just using a single prompt per word (mono-prompt hehe)
- organize output files /& directories
- consider widening the types of words that can be represented with simple online images, i.e. don't need to be generated.
