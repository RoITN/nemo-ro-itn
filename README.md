# NeMo Romanian ITN (Inverse Text Normalization)

WFST-based Inverse Text Normalization (ITN) grammars for the Romanian language. These rules are designed to be integrated directly into the official **NVIDIA NeMo Text Processing** toolkit.

## Integration Guide

Because NeMo relies on internal package imports, the most reliable way to use these rules is to add them directly into the official NeMo repository source code.

### 1. Clone the Repositories
First, clone the official NVIDIA NeMo text processing repository and this Romanian language repository:

```bash
# Clone the official NeMo repository
git clone https://github.com/NVIDIA/NeMo-text-processing.git

# Clone this Romanian ITN repository
git clone https://github.com/RoITN/nemo-ro-itn.git
```

### 2. Copy the Romanian Rules
Copy the `ro` folder from this repository into the NeMo source tree:

```bash
cp -r nemo-ro-itn/nemo_text_processing/inverse_text_normalization/ro NeMo-text-processing/nemo_text_processing/inverse_text_normalization/
```

### 3. Update the NeMo Core File
Open the `NeMo-text-processing/nemo_text_processing/inverse_text_normalization/inverse_normalize.py` file in a text editor and make two small additions:

**Add the Romanian imports:**
Inside the `__init__` method of the `InverseNormalizer` class, add the `elif lang == 'ro':` block before the final `else:` statement:

```python
        elif lang == 'ro':  # Romanian
            from nemo_text_processing.inverse_text_normalization.ro.taggers.tokenize_and_classify import ClassifyFst
            from nemo_text_processing.inverse_text_normalization.ro.verbalizers.verbalize_final import VerbalizeFinalFst
            self.tagger = ClassifyFst(cache_dir=cache_dir, overwrite_cache=overwrite_cache)
            self.verbalizer = VerbalizeFinalFst()
```

**Update the language arguments:**
In the `parse_args()` function at the bottom of the same file, add `'ro'` to the `choices` list:

```python
    parser.add_argument(
        "--language",
        help="language",
        choices=['en', 'de', 'es', 'pt', 'ru', 'fr', 'sv', 'vi', 'ar', 'es_en', 'zh', 'hi', 'hy', 'mr', 'ja', 'ro'],
        default="en",
        type=str,
    )
```

### 4. Install the Modified NeMo Package
Navigate into the official NeMo repository and install it locally so your Python environment registers the new files:

```bash
cd NeMo-text-processing
pip install -e .
```

## Usage

Once installed, you can run NeMo's official inference scripts using the `--language ro` flag from inside the `NeMo-text-processing` directory:

```bash
python nemo_text_processing/inverse_text_normalization/inverse_normalize.py \
    --language ro \
    --text "o sută douăzeci de lei"
```

You can also use it programmatically in your Python scripts:

```python
from nemo_text_processing.inverse_text_normalization.inverse_normalize import InverseNormalizer

normalizer = InverseNormalizer(lang='ro')
print(normalizer.inverse_normalize("două mii douăzeci și șase"))
# Output: 2026
```
