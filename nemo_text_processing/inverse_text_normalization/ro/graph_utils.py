# from the root of your NeMo-text-processing clone
# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import string
import pynini
from pynini import union, closure
from pynini.lib import pynutil, utf8

from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path


NEMO_CHAR = utf8.VALID_UTF8_CHAR
# Digits rămân aceleași
NEMO_DIGIT = pynini.union(*[str(d) for d in range(10)])
# Litere românești cu diacritice
ROM_LOWER = pynini.union(
    *list("aăâbcdefghiîjklmnopqrsștțuvwxyz")
).optimize()
ROM_UPPER = pynini.union(
    *list("AĂÂBCDEFGHIÎJKLMNOPQRSȘTȚUVWXYZ")
).optimize()
RO_MINUS = pynini.union("minus", "Minus", "MINUS").optimize()
NEMO_ALPHA = pynini.union(ROM_LOWER, ROM_UPPER).optimize()
NEMO_ALNUM = pynini.union(NEMO_DIGIT, NEMO_ALPHA).optimize()
NEMO_SPACE = " "
NEMO_CHAR = utf8.VALID_UTF8_CHAR
NEMO_SIGMA = union(NEMO_CHAR, NEMO_SPACE).optimize()
NEMO_SIGMA_STAR = closure(NEMO_SIGMA)
NEMO_WHITE_SPACE = pynini.union(" ", "\t", "\n", "\r", "\u00A0").optimize()
delete_space = pynutil.delete(pynini.closure(NEMO_WHITE_SPACE, 1))
delete_zero_or_one_space = pynutil.delete(pynini.closure(NEMO_WHITE_SPACE, 0, 1))
insert_space = pynutil.insert(" ")

def capitalized_input_graph(graph: "pynini.FstLike") -> "pynini.FstLike":
    """Permite input cu majusculă la început."""
    to_lower = pynini.cross(ROM_UPPER, ROM_LOWER)
    cap = to_lower + graph
    return graph | cap

def convert_space_nbsp(fst):
    """Schimbă numai spațiile obișnuite (U+0020) în non-breaking (U+00A0)."""
    rewrite = pynini.cdrewrite(
        pynini.cross(" ", "\u00A0"),
        "",  # context stânga liber
        "",  # context dreapta liber
        NEMO_CHAR  # alfabetul sub care aplici regula
    ).optimize()
    return (fst @ rewrite).optimize()


# Sigma = orice literă românească sau spațiu
SIGMA = (NEMO_ALPHA | NEMO_SPACE).closure()

# Măsurători diacritice variante la forma canonică
DIACRITIC_MAPPINGS = pynini.union(
    pynini.cross("ş", "ș"),  # U+015F -> U+0219
    pynini.cross("Ş", "Ș"),  # U+015E -> U+0218
    pynini.cross("ţ", "ț"),  # U+0163 -> U+021B
    pynini.cross("Ţ", "Ț"),  # U+0162 -> U+021A
)

# Înlocuiește spațiul non-breaking cu spațiu normal
NBSP_MAPPING = pynini.cross("\u00A0", " ")

# Transducer unificat de normalizare a input-ului
NORMALIZE = pynini.cdrewrite(
    DIACRITIC_MAPPINGS | NBSP_MAPPING,
    "",
    "",
    SIGMA
).optimize()

# Exemplu de utilizare:
#   normalized = pynini.compose(input_string, NORMALIZE).string()

