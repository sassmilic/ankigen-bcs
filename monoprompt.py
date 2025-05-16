PROMPT = """
You will receive a list of BCS words (misspellings are possible). For each word, return a JSON object with the following fields:

1. **Canonical form**

Convert the word to its canonical (dictionary) form with correct diacritics:
- Nouns → singular nominative
- Verbs → infinitive
- Adjectives → masculine singular nominative
- Other words → base dictionary form
- All output words must be lowercase

2. **Definition**

Define the word in Bosnian/Croatian/Serbian (ijekavian variant) using cloze format.

- Start the definition with the word in cloze brackets: `{{{{c1::word}}}}`
- Follow it with grammatical info in parentheses:
  - Verbs: (glagol, aspect, 1st person singular present) — the present form must also be in cloze, e.g. `(glagol, svršeni vid, {{{{c1::prodrijem}}}})`
  - Nouns: (imenica, gender), and note if uncountable
  - Adjectives: (pridjev, degree), e.g., pozitiv, komparativ, superlativ
- Include dialectal or stylistic notes only if relevant (e.g., mostly used in Bosnia)
- For concrete words, write a one-sentence definition
- For abstract, polysemous, or emotional words, include both literal and figurative meanings
- Use comparisons if helpful (e.g., "kao kad...", "poput...")

**Examples:**
- `{{{{c1::Prodrijeti}}}} (glagol, svršeni vid, {{{{c1::prodrijem}}}}) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju).`
- `{{{{c1::Blagostanje}}}} (imenica, srednji rod, nebrojivo) označava stanje u kojem osoba ili zajednica ima dovoljno sredstava za udoban, siguran i zadovoljavajući život — materijalno, emocionalno i duhovno.`
- `{{{{c1::Najvažniji}}}} (pridjev, superlativ) opisuje ono što ima najveći značaj ili prioritet u odnosu na sve druge stvari u određenom kontekstu.`

3. **Example sentences**

Generate **exactly 3 sentences** in BCS (ijekavian variant) using the word.

- If the word is abstract or polysemous, include literal, figurative, or idiomatic uses
- Use the word in **different grammatical forms**:
  - Verbs: vary tense, person, or mood
  - Nouns: use different cases
- Wrap **all inflected forms** of the target word in cloze brackets: `{{{{c1::...}}}}`
- Use a positive or life-affirming tone when appropriate
- Each sentence should appear on its own line with no numbering or extra formatting

4. **Word type**

Classify the word as either:
- SIMPLE: a concrete, visible object (e.g., "jabuka", "kuća")
- COMPLEX: an abstract concept, quality, action, or emotion (e.g., "ljubav", "misliti", "sloboda")

Return only `"SIMPLE"` or `"COMPLEX"`. If unsure, choose `"COMPLEX"`.

5. **English translation**

Translate the core meaning of the word into English. Use only one or two words — the most relevant translation for a language learner.

---

Return your output as a single **JSON array**, one object per word, in the following format:

[
  {{
    "word": "prodrijeti",
    "canonical_form": "prodrijeti",
    "definition": "{{c1::Prodrijeti}} (glagol, svršeni vid, {{c1::prodrijem}}) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju).",
    "example_sentences": [
      "Sunčeva svjetlost je uspjela {{{{c1::prodrijeti}}}} kroz guste oblake.",
      "Njene riječi su duboko {{{{c1::prodrle}}}} u moje misli.",
      "Nakon dugog razmišljanja, konačno sam uspio {{{{c1::prodrijeti}}}} do suštine problema."
    ],
    "word_type": "COMPLEX",
    "translation": "penetrate"
  }},
  ...
]

❗ Important: Return only the raw JSON array.
- Do NOT include any headings, commentary, preambles (like “Here is the JSON array…”), or explanations.
- Do NOT wrap the output in markdown formatting (such as ```json or ```).
- Your response must begin with `[` and end with `]` so it can be parsed directly with a JSON parser.

Word list: {word_list}
"""