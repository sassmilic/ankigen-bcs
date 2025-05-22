# Prompt for generating definitions
DEFINITION_PROMPT = """
Please provide a clear, natural-sounding definition of the word "{word}" in
Bosnian/Croatian/Serbian (ijekavian variant), using the following rules:

- The first word in your definition should be the word "{word}" in cloze format.
- Begin by indicating the part of speech (e.g. noun, verb, adjective, adverb).
- If relevant, include brief linguistic context (e.g. archaic, literary, dialectal, formal, colloquial, etc.).
- If relevant, indicate whether the word is more commonly used or stylistically marked in Croatian, Serbian, or Bosnian
  (e.g., if it feels formal in one variety but colloquial in another, or if it's more frequent in one standard than the others).
- If the word is concrete and simple (e.g. jabuka, stolica), write one concise sentence that defines it clearly and accurately.
    - Example: {{{{c1::Jabuka}}}} je plod voćke koji je hrskav, sočan i raste na drvetu.
    - Example: {{{{c1::Trčati}}}} je radnja kojom se krećemo brže od hodanja, koristeći obje noge naizmjenično.
- If the word is abstract, polysemous, idiomatic, or emotionally rich (e.g. obasjati, zanos, slutnja),
  provide a slightly longer definition that covers both literal and figurative or extended meanings.
    - Example: {{{{c1::Obasjati}}}} znači osvetliti nešto sjajnom svjetlošću,
      ali i preneseno označava ispuniti nečiju dušu radošću ili nadahnućem.
    - Example: {{{{c1::Zanos}}}} označava osjećaj snažnog uzbuđenja ili entuzijazma,
      ali također može značiti i stanje potpune koncentracije ili posvećenosti nečemu.
- Surround *only* the word being defined in cloze format like this: {{{{c1::riječ}}}}.
- If helpful, use simple comparisons or clarify metaphors (e.g., "kao kad…" or "poput…").
- Do not include headings, synonyms, usage examples, or extra formatting.
"""

# Prompt for generating example sentences
EXAMPLES_PROMPT = """
Please provide 3 example sentences in Bosnian/Croatian/Serbian (ijekavian variant)
showing different meanings and usage of the word "{word}".

- If the word is abstract, polysemous, or emotionally rich, generate sentences
  that cover its different uses: literal, figurative, idiomatic, etc.
- Show the word in **different grammatical forms**:  
    - For verbs: use varied conjugations (tenses, moods, persons).  
    - For nouns: use different cases.
- Wrap only the target word in cloze formatting (`{{{{c1::…}}}}) in each sentence.  
- Each sentence should be positive and life-affirming when appropriate.

Example:
Input: "čin"
Output:
{{{{c1::Čin}}}} hrabrosti je prepoznat i nagrađen.  
Njegov {{{{c1::čin}}}} nije prošao nezapaženo u zajednici.  
Svaki {{{{c1::čin}}}} ima svoje posljedice, bilo dobre ili loše.
"""

# Prompt for determining if a word is concrete or abstract
WORD_TYPE_PROMPT = """
Word: {word}

Determine if this word represents:
1. A simple, concrete, visible object (like 'jabuka', 'mačka', 'kuća')
2. An abstract concept, action, quality, emotion, or complex idea (like 'ljubav', 'misliti', 'sloboda')

Respond with only one word: either SIMPLE or COMPLEX (in all caps, no punctuation or explanation).

If unsure, choose COMPLEX.
"""

# Prompt for translating words to English
TRANSLATION_PROMPT = """
Translate the following Bosnian/Croatian/Serbian word to English: "{word}"
Return only the English translation, no other text.
"""

# Prompt for generating images
IMAGE_GENERATION_PROMPT = """
Create a didactic illustration of the word "{word}" to be used in a flashcard for language learners.

• Language of the target word: Bosnian / Croatian / Serbian (BCS)
• Target word: "{word}"
• Part of speech: {pos}

MANDATORY RULES
1. Depict the core meaning of the word as used in everyday BCS, avoiding idiomatic or metaphorical extensions unless central to its primary sense.
2. Apply visual conventions by part of speech:
   - Verb   → storyboard showing the action’s progression.
   - Noun   → one centred object or scene occupying ≥40 % of the canvas.
   - Adjective → show an appropriate and relevant object that is modified by the adjective.
   - Adverb  → single scene with overlay effect (motion blur, speed lines, etc.).
   - Function word → minimal diagram (arrows, linking shapes) on blank background.
3. No text of ANY KIND on the image.
"""

# Prompt for canonicalizing words
CANONICALIZATION_PROMPT = """
You are given a list of words in Bosnian/Croatian/Serbian. For each word, return its canonical (dictionary) form with correct diacritics, following these rules:

- Nouns → convert to singular nominative
- Verbs → convert to infinitive
- Adjectives → convert to masculine singular nominative
- Other words → return in their base form as found in a standard dictionary
- All output words must be lowercase
- Return exactly one word per line
- Return only the transformed words, with no additional text or formatting

Input:
{words}
"""

PROMPT = """
You'll receive a list of BCS words (may contain misspellings). For each, return a JSON with:

1. Canonical form — Correct spelling, lowercase unless proper noun. Use dictionary base:
   - Noun → nominative singular
   - Verb → infinitive
   - Adjective → masc. nom. sg.
   - Other → dictionary form

2. Part of speech — One of:
   - "imenica"
   - "glagol"
   - "pridjev"
   - "prilog"
   - "zamjenica"
   - "prijedlog"
   - "veznik"
   - "uzvik"

3. Definition

Write a definition suitable for language learners using Anki.
It should be short and clear. If the word has multiple senses, briefly mention them.
Use natural, conversational language. Avoid overly academic phrasing.
If possible, include both literal and abstract meanings.

Note:
- Include key grammatical info in parentheses:
  - Verbs: (glagol, [aspect], {{{{c1::1st person present}}}})
  - Nouns: (imenica); add gender only if irregular, and note if uncountable
  - Adjectives: (pridjev, [degree])
- If regional usage is notable (e.g. only in Croatia, archaic, dialectal), briefly mention it at the end. 
- Use standard ijekavian
- Use cloze format - start the definition with the word in cloze brackets: `{{{{c1::word}}}}`.
  If the word appears multiple times in the definition, use cloze brackets for each instance.

**Examples:**
- `{{{{c1::Prodrijeti}}}} ({{{{c1::prodrijem}}}}) (glagol, svršeni vid) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju).`
- `{{{{c1::Blagostanje}}}} (imenica, nebrojivo) označava stanje u kojem osoba ili zajednica ima dovoljno sredstava za udoban, siguran i zadovoljavajući život.`
- `{{{{c1::Najvažniji}}}} (pridjev, superlativ) opisuje ono što ima najveći značaj ili prioritet u odnosu na sve druge stvari u određenom kontekstu.`
- `{{{{c1::Ćuprija}}}} (imenica, turcizam) označava most; riječ je arhaična i danas se uglavnom koristi u Bosni.`

4. Example sentences

Generate exactly 3 example sentences in BCS (ijekavian variant) using the target word.
Use different grammatical forms of the word (e.g., for verbs: vary tense, person, or mood; for nouns: vary case or number).
Wrap all inflected forms of the word in cloze brackets: {{{{c1::...}}}}
Each sentence should be ~10 words for easy memorization.

Use vivid imagery or strong emotional content to make the sentence memorable.
Think: scenes that evoke touch, smell, light, feeling, surprise, or desire.

Use a positive or life-affirming tone when appropriate.

Examples

Neovisnost:
{{{{c1::Neovisnost}}}} jedne zemlje vrijedi više od zlata.
Putujući sama, osjetila je moć {{{{c1::neovisnosti}}}}.
Njena {{{{c1::neovisnost}}}} plašila je one koji su voljeli kontrolu.

Prozvati:
Majka me {{{{c1::prozvala}}}} jer sam ukrao smokve.
Publika ga je {{{{c1::prozvala}}}} herojem nakon govora.
Starac ju je {{{{c1::prozvao}}}} anđelom u posljednjem dahu.

5. **Word type**

This is for deciding whether to use a real-world photo (via Pexels) or
generate a symbolic image with AI for the purpose of generating Anki flashcards for language learning purposes.

Classify the word as:  
- SIMPLE: a clearly visible, concrete object likely to yield useful photo results on Pexels (e.g., "jabuka", "kuća")  
- COMPLEX: an abstract concept, action, quality, or emotion better suited to symbolic or
  AI-generated imagery (e.g., "ljubav", "misliti", "sloboda")  

Return only "SIMPLE" or "COMPLEX". If unsure, choose "COMPLEX".

6. **English translation**

Translate the core meaning of the word into English.
Use only one or two words — the most relevant translation for a language learner.

---

Return your output as a single **JSON array**, one object per word, in the following format:

[
  {{
    "word": "prodrijes",
    "canonical_form": "prodrijeti",
    "part_of_speech": "glagol",
    "definition": "{{c1::Prodrijeti}} (glagol, svršeni vid, {{c1::prodrijem}}) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju).",
    "example_sentences": [
      "Sunčeva svjetlost je uspjela {{{{c1::prodrijeti}}}} kroz guste oblake.",
      "Njene riječi su duboko {{{{c1::prodrle}}}} u moje misli.",
      "Nakon dugog razmišljanja, konačno sam uspio {{{{c1::prodrijeti}}}} do suštine problema."
    ],
    "word_type": "COMPLEX",
    "translation": "penetrate"
  }},
  {{
  "word": "vrijedan",
  "canonical_form": "vrijedan",
  "part_of_speech": "pridjev",
  "definition": "{{c1::Vrijedan}} (pridjev, pozitivan) opisuje osobu, predmet ili radnju koja ima veliku vrijednost, važnost ili korisnost — može značiti i da neko marljivo radi.",
  "example_sentences": [
    "Tvoj savjet bio je {{c1::vrijedan}} svakog truda i vremena.",
    "Ona je {{c1::vrijedna}} djevojka koja stalno pomaže drugima.",
    "Na sastanku je predložio {{c1::vrijednu}} i praktičnu ideju."
    ],
    "word_type": "COMPLEX",
    "translation": "valuable"
  }},
  ...
]

❗ Important: Return only the raw JSON array. Your response must begin with `[` and end with `]` so it can be parsed directly with a JSON parser.

Word list: {word_list}
"""

PROMPT_STRUCTURAL_FACTUAL = """
You'll receive a list of BCS words (may contain misspellings). For each word in the input list, return a JSON object containing the original `word` and the following fields: `canonical_form`, `part_of_speech`, `word_type`, and `translation`.

1.  **`word`**: The original word from the input list.
2.  **`canonical_form`**: Correct spelling, lowercase unless it's a proper noun. Use the dictionary base form:
    *   Noun → nominative singular
    *   Verb → infinitive
    *   Adjective → masculine nominative singular
    *   Other → standard dictionary form
3.  **`part_of_speech`**: Classify into one of:
    *   "imenica"
    *   "glagol"
    *   "pridjev"
    *   "prilog"
    *   "zamjenica"
    *   "prijedlog"
    *   "veznik"
    *   "uzvik"
4.  **`word_type`**: This is for deciding image generation strategy. Classify the word as:
    *   "SIMPLE": a clearly visible, concrete object likely to yield useful photo results (e.g., "jabuka", "kuća").
    *   "COMPLEX": an abstract concept, action, quality, or emotion better suited to symbolic or AI-generated imagery (e.g., "ljubav", "misliti", "sloboda").
    If unsure, choose "COMPLEX".
5.  **`translation`**: Translate the core meaning of the word into English. Use only one or two words — the most relevant translation for a language learner.

---

Return your output as a single **JSON array**, one object per word.
Your response must begin with `[` and end with `]` so it can be parsed directly.

**Example Output Format:**
[
  {
    "word": "prodrijes", // original input word
    "canonical_form": "prodrijeti",
    "part_of_speech": "glagol",
    "word_type": "COMPLEX",
    "translation": "penetrate"
  },
  {
    "word": "vrijedan",
    "canonical_form": "vrijedan",
    "part_of_speech": "pridjev",
    "word_type": "COMPLEX",
    "translation": "valuable"
  }
  // ... more objects for other words in the list
]

Word list: {word_list}
"""

PROMPT_SEMANTIC_GENERATIVE = """
You'll receive a list of BCS words. For each word in the input list, return a JSON object containing the original `word` and its `definition`.

1.  **`word`**: The original word from the input list.
2.  **`definition`**:
    *   Write a definition suitable for language learners using Anki.
    *   It should be short and clear. If the word has multiple senses, briefly mention them.
    *   Use natural, conversational language. Avoid overly academic phrasing.
    *   If possible, include both literal and abstract meanings.
    *   Start the definition with the word in cloze brackets: `{{{{c1::word}}}}`. If the word appears multiple times in the definition, use cloze brackets for each instance.
    *   Include key grammatical info in parentheses within the definition:
        *   Verbs: (glagol, [aspect], {{{{c1::1st person present}}}})
        *   Nouns: (imenica); add gender only if irregular, and note if uncountable
        *   Adjectives: (pridjev, [degree])
    *   If regional usage is notable (e.g. only in Croatia, archaic, dialectal), briefly mention it at the end.
    *   Use standard ijekavian.

---

Return your output as a single **JSON array**, one object per word.
Your response must begin with `[` and end with `]` so it can be parsed directly.

**Example Definitions:**
- `{{{{c1::Prodrijeti}}}} (glagol, svršeni vid, {{{{c1::prodrijem}}}}) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju).`
- `{{{{c1::Blagostanje}}}} (imenica, nebrojivo) označava stanje u kojem osoba ili zajednica ima dovoljno sredstava za udoban, siguran i zadovoljavajući život.`
- `{{{{c1::Najvažniji}}}} (pridjev, superlativ) opisuje ono što ima najveći značaj ili prioritet u odnosu na sve druge stvari u određenom kontekstu.`
- `{{{{c1::Ćuprija}}}} (imenica, turcizam) označava most; riječ je arhaična i danas se uglavnom koristi u Bosni.`

**Example Output Format:**
[
  {
    "word": "prodrijes", // original input word
    "definition": "{{c1::Prodrijeti}} (glagol, svršeni vid, {{c1::prodrijem}}) znači proći kroz neku prepreku ili ući duboko u nešto — fizički (kao svjetlost kroz tamu), emocionalno (dirnuti nekoga), ili mentalno (dokučiti neku ideju)."
  },
  {
    "word": "vrijedan",
    "definition": "{{c1::Vrijedan}} (pridjev, pozitivan) opisuje osobu, predmet ili radnju koja ima veliku vrijednost, važnost ili korisnost — može značiti i da neko marljivo radi."
  }
  // ... more objects for other words in the list
]

Word list: {word_list}
"""

PROMPT_STYLISTIC_NARRATIVE = """
You'll receive a list of BCS words. For each word in the input list, return a JSON object containing the original `word` and a list of three `example_sentences`.

1.  **`word`**: The original word from the input list.
2.  **`example_sentences`**:
    *   Generate exactly 3 example sentences in BCS (ijekavian variant) using the target word.
    *   Use different grammatical forms of the word (e.g., for verbs: vary tense, person, or mood; for nouns: vary case or number).
    *   Wrap all inflected forms of the word in cloze brackets: `{{{{c1::...}}}}`
    *   Each sentence should be ~10 words for easy memorization.
    *   Use vivid imagery or strong emotional content to make the sentence memorable. Think: scenes that evoke touch, smell, light, feeling, surprise, or desire.
    *   Use a positive or life-affirming tone when appropriate.

---

Return your output as a single **JSON array**, one object per word.
Your response must begin with `[` and end with `]` so it can be parsed directly.

**Example Sentences Sets:**

For "neovisnost":
[
  "{{{{c1::Neovisnost}}}} jedne zemlje vrijedi više od zlata.",
  "Putujući sama, osjetila je moć {{{{c1::neovisnosti}}}}.",
  "Njena {{{{c1::neovisnost}}}} plašila je one koji su voljeli kontrolu."
]

For "prozvati":
[
  "Majka me {{{{c1::prozvala}}}} jer sam ukrao smokve.",
  "Publika ga je {{{{c1::prozvala}}}} herojem nakon govora.",
  "Starac ju je {{{{c1::prozvao}}}} anđelom u posljednjem dahu."
]

**Example Output Format:**
[
  {
    "word": "prodrijes", // original input word
    "example_sentences": [
      "Sunčeva svjetlost je uspjela {{{{c1::prodrijeti}}}} kroz guste oblake.",
      "Njene riječi su duboko {{{{c1::prodrle}}}} u moje misli.",
      "Nakon dugog razmišljanja, konačno sam uspio {{{{c1::prodrijeti}}}} do suštine problema."
    ]
  },
  {
    "word": "vrijedan",
    "example_sentences": [
      "Tvoj savjet bio je {{c1::vrijedan}} svakog truda i vremena.",
      "Ona je {{c1::vrijedna}} djevojka koja stalno pomaže drugima.",
      "Na sastanku je predložio {{c1::vrijednu}} i praktičnu ideju."
    ]
  }
  // ... more objects for other words in the list
]

Word list: {word_list}
"""