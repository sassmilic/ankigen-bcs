# Prompt for generating definitions
DEFINITION_PROMPT = """
Word: {word}

Please provide a clear, natural-sounding definition of this word in Bosnian/Croatian/Serbian (ijekavian variant) using these rules:
- For simple, concrete words (e.g. "jabuka", "jezikoslovlje"), write a single concise sentence.
- For abstract, polysemous, or emotionally rich words (e.g. "obasjati", "beskonačnost"), give a more detailed definition covering literal and figurative senses.
- Enclose only the target word in cloze format: {{c1::riječ}}.
- Do not add headings, bullet lists, synonyms, or extra formatting—just the definition.

Examples:   
Input: "jabuka"  
Output: {{c1::Jabuka}} je plod voćke koji je hrskav, sočan i raste na drvetu.

Input: "jezikoslovlje"  
Output: {{c1::Jezikoslovlje}} je nauka koja proučava strukturu, upotrebu i razvoj jezika.

Input: "obasjati"  
Output: {{c1::Obasjati}} znači osvetliti nešto sjajnom svjetlošću, ali i preneseno označava ispuniti nečiju dušu radošću ili nadahnućem.

Input: "beskonačnost"  
Output: {{c1::Beskonačnost}} označava svojstvo nečega što nema granica ili kraja, poput beskonačnog niza brojeva ili neprekidnog prostora. U prenesenom smislu opisuje vječnost, neograničene mogućnosti ili neiscrpnu količinu ideja.
"""

# Prompt for generating example sentences
EXAMPLES_PROMPT = """
Word: {word}

Please provide 2–5 example sentences in Bosnian/Croatian/Serbian (ijekavian variant)
showing different meanings and usage of this word. Provide more examples if the word
is abstract or has multiple meanings.

- If the word is abstract, polysemous, or emotionally rich, generate **more** (up to 5) sentences
  covering its different uses—literal, figurative, idiomatic, emotional, social, etc.
- If, however, the word is simple and concrete, generate **less** (up to 3) sentences.
- Show the word in **different grammatical forms**:  
    - For verbs: use varied conjugations (tenses, moods, persons).  
    - For nouns: use different cases.
- Wrap only the target word in cloze formatting (`{{c1::…}}`) in each sentence.  
- Each sentence should be positive and life-affirming when appropriate.
- Avoid overly complex or unnatural phrasing.
- **Every sentence must appear on its own line**, with **no** numbering, bullet points, or commentary.  
- **Reminder:** cloze brackets require two left braces (`{{`) and two right braces (`}}`).  

Example:
Input: "čin"
Output:
{{c1::Čin}} hrabrosti je prepoznat i nagrađen.  
Njegov {{c1::čin}} nije prošao nezapaženo u zajednici.  
Svaki {{c1::čin}} ima svoje posljedice, bilo dobre ili loše.
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
Create a clear, simple image that visually represents the meaning of the BCS (Bosnian/Croatian/Serbian) word: "{word}"

Important:
- NO text in the image. DO NOT INCLUDE ANY TEXT IN THE IMAGE.
""" 