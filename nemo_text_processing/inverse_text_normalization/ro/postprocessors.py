import re
from nemo_text_processing.inverse_text_normalization.ro.taggers.cardinal import CardinalFst
from pynini.lib import rewrite

cardinal_verbalizer_fst = CardinalFst().fst

word_to_digit = {
    "zero": "0", "unu": "1", "una": "1", "o": "1",
    "doi": "2", "două": "2", "trei": "3", "patru": "4",
    "cinci": "5", "șase": "6", "sase": "6", "șapte": "7", "sapte": "7",
    "opt": "8", "nouă": "9", "noua": "9", "zece": "10"
}

pattern = re.compile(
    r"\b(?:(?:[Dd]rumul?\s+[Nn]ațional(?:ului)?)|DN)\s*"
    r"(?:(zero|unu|una|o|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece)|(\d+))"
    r"\s*([A-Za-z])?\b",
    flags=re.IGNORECASE
)


def repl(m):
    if m.group(1):  # forma verbală
        num = word_to_digit[m.group(1).lower()]
    else:           # forma numerică
        num = m.group(2)
    letter = (m.group(3) or "").upper()
    return f"DN{num}{letter}"

def normalize_drum_national(text: str) -> str:
    return pattern.sub(repl, text)

pattern_autostrada = re.compile(
    r"\b(?:A|[Aa]utostrada)\s+"
    r"(zero|unu|una|o|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece|\d+)\b"
)


def postprocess_highway(text: str) -> str:
    def repl(m):
        val = m.group(1).lower()
        digit = word_to_digit.get(val, val)
        return f"A{digit}"
    return pattern_autostrada.sub(repl, text)

pattern_sectoare_enum = re.compile(
    r"\b(sectoarele|sectorul|sector|sectorului|sectoarelor|etaj|etajul|top)\s+("
    r"(?:\d+|zero|unu|una|o|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece)"
    r"(?:\s*,\s*(?:\d+|zero|unu|una|o|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece))*"
    r"(?:\s*(?:și|si)\s*(?:\d+|zero|unu|una|o|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece))?"
    r")\b",
    flags=re.IGNORECASE,
)

def repl_sectoare_enum(m):
    prefix = m.group(1)            
    seq = m.group(2)              
    parts = re.split(r",\s*|\s*(?:și|si)\s*", seq)
    mapped = [word_to_digit.get(p.lower(), p) for p in parts]
    if len(mapped) > 1:
        body = ", ".join(mapped[:-1]) + " și " + mapped[-1]
    else:
        body = mapped[0]
    return f"{prefix} {body}"


def postprocess_output(text: str, itn_category: str = "") -> str:
    """
    ! S-au folosit doar exemple cunoscute din setul de antrenare.
    Aplică:
    1. Separator de mii pentru numere >= 1000, dar NU pentru ani (ex: anul 2000).
    2. Elimină spațiile în exces înaintea semnelor de punctuație.
    3. Transcrie expresii de tipul 'model trei' în 'model 3'.
    4. Păstrează cifra în context urban/admin: 'sectorul patru' → 'sectorul 4'
    5. Elimină spațiul înainte de simboluri ca %, ‰, °C etc.
    """

    def should_skip(match):
        start = match.start()
        prefix = text[max(0, start - 6):start].lower()
        return "anul " in prefix

    def format_thousands(match):
        num_str = match.group(0)
        if should_skip(match):
            return num_str
        return "{:,}".format(int(num_str)).replace(",", ".")

    def replace_named_number(match):
        prefix = match.group(1)
        word = match.group(2).lower()
        digit = word_to_digit.get(word, word)
        return f"{prefix} {digit}"

    # 0. Normalizează drum național
    text = normalize_drum_national(text)

    text = postprocess_highway(text)

    # 1. Format numere mari (comentat dacă nu e nevoie)
    if itn_category.lower() != "date":
        text = re.sub(r"\b\d{4,}\b", format_thousands, text)

    # 2. Spații înainte de semne de punctuație
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)

    # 3. Fără spațiu înainte de %
    text = re.sub(r"(\d+)\s+%", r"\1%", text)

    # 3.5 Elimină spațiul între număr și °C (grade Celsius)
    text = re.sub(r"(\d+)\s+°", r"\1°", text)

    # 3.6 Elimină spațiul între zecimal sau întreg și %/‰
    text = re.sub(r"(\d+,\d+|\d+)\s+(%|‰)", r"\1\2", text)

    # 4. Cazuri de nume tehnice
    naming_keywords = r"(model|nota|versiunea|magnitudine|magnitudinea|calibru|calibrul|etaj|etajul|seria|tipul|gradul|varianta)\s+(zero|unu|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece)"
    text = re.sub(rf"\b{naming_keywords}\b", replace_named_number, text, flags=re.IGNORECASE)

    # 5. Cazuri administrative
    admin_keywords = r"(sectorul|sectoarele|secția|numărul)\s+(zero|unu|doi|două|trei|patru|cinci|șase|sase|șapte|sapte|opt|nouă|noua|zece)"
    text = re.sub(rf"\b{admin_keywords}\b", replace_named_number, text, flags=re.IGNORECASE)

    # 6. Enumerații cu sectoare
    text = pattern_sectoare_enum.sub(repl_sectoare_enum, text)

    return text.strip()
