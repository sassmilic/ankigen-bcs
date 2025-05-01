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

### Preparing Word List

Create a `words.txt` file with one word per line that you want to generate flashcards for.

### Running the Script

Run the flashcard generator script:

## TODO

- deal with duplicates (i.e. don't regenerate)
- parallelize requests
- consider just using a single prompt per word (mono-prompt hehe)
- organize output files /& directories
