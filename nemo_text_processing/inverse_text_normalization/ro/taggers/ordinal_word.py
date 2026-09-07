import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst
from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path


class OrdinalWordFst(GraphFst):
    def __init__(self):
        super().__init__(name="ordinal_word", kind="classify")

        # Load word-based ordinal map from file
        graph = pynini.string_file(get_abs_path("data/ordinals/ordinal_word.tsv"))

        ordinal = (
            pynutil.insert("ordinal { ") +
            pynutil.insert("prefix: \"a\" ") +
            pynutil.insert("integer: \"") + graph + pynutil.insert("\" ") +
            pynutil.insert("}")
        )

        self.fst = ordinal.optimize()
