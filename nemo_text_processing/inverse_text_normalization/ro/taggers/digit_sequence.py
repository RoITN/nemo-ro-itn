from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_space
import pynini

class DigitSequenceFst(GraphFst):
    def __init__(self):
        super().__init__(name="cardinal", kind="classify") 

        digits = {
            "zero": "0", "unu": "1", "doi": "2", "trei": "3", "patru": "4",
            "cinci": "5", "șase": "6", "sase": "6", "șapte": "7", "sapte": "7",
            "opt": "8", "nouă": "9", "noua": "9"
        }

        graph_digit = pynini.union(*[pynini.cross(k, v) for k, v in digits.items()]).optimize()
        digit_sequence = graph_digit + pynini.closure(delete_space + graph_digit, 1)

        integer_graph = pynutil.insert("integer: \"") + digit_sequence + pynutil.insert("\"")
        
        self.fst = self.add_tokens(integer_graph).optimize()
