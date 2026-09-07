from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_space
import pynini


class DigitSequenceFst(GraphFst):
    """
    Verbalizer pentru sequence — extrage valoarea din integer: "..." și elimină tokens.
    """

    def __init__(self):
        super().__init__(name="cardinal", kind="verbalize")

        # Extrage doar conținutul câmpului integer
        delete_token = lambda s: pynutil.delete(s) + delete_space

        graph = (
            delete_token("tokens {")
            + delete_token("cardinal {")
            + delete_token("integer: \"")
            + pynini.closure(pynini.union(*"0123456789"), 1)
            + pynutil.delete("\"") + delete_space
            + pynutil.delete("}") + delete_space
            + pynutil.delete("}")
        )

        self.fst = graph.optimize()
