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
Create an image that visually captures the meaning of the BCS (Bosnian/Croatian/Serbian) word: "{word}".

Use the following rules:

1. **Interpretation style**:
   - If the word is abstract, emotional, or polysemous, illustrate it using a recognizable situation, character, or emotional metaphor.
      - Show a **human figure, natural setting, or object in context** that evokes the feeling or concept.
      - Prefer narrative or emotional metaphor (e.g., a person walking alone under stars for “sloboda”), not visual abstraction.
   - If the word is concrete, simple, or object-based, depict it literally and clearly.

2. **Visual clarity**:
   - The image must be **distinctive and unambiguous**, so a language learner can associate it confidently with this word.
   - Avoid scenes that could plausibly represent other common vocabulary.

3. **No text**:
   - Do NOT include any written language or labels in the image.

4. **Stylistic consistency by part of speech**:
   Apply these visual conventions based on the part of speech (if known or inferable from the word):

   - **Verb**: Depict action or transformation over time. Use a comic strip, storyboard, or a subject in dynamic motion across a sequence.
   - **Noun**: Show a centered object or scene, clearly framed.
   - **Adjective**: 
      - Show a person or character with a facial expression that clearly conveys the adjective's emotional or descriptive quality.
      - Use the background environment, color palette, or visual texture to reinforce the mood or tone — e.g., stormy skies for “tužan”, vibrant flowers for “vedar”, rigid geometric patterns for “strogi”.
      - The figure should be visually dominant, but the background must add symbolic weight to the meaning.
   - **Adverb**: Show a scene with overlay effects (e.g., motion blur, shadows, symbols of time or intensity).
   - **Function word** (e.g., preposition, pronoun): Use abstract diagrams, arrows, or mirrored/reflexive imagery to illustrate relationships or directionality.
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