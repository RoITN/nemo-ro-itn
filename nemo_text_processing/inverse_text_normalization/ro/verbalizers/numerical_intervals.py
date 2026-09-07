import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_extra_space

class VerbalizeIntervalFst(GraphFst):
    def __init__(self):
        super().__init__(name="verbalize_interval", kind="verbalize")

        digit = pynini.union(*"0123456789")
        number = pynini.closure(digit, 1)

        open_outer = pynutil.delete("interval {")
        close_outer = pynutil.delete("}")

        first = (
            delete_extra_space
            + pynutil.delete("first:")
            + delete_extra_space
            + pynutil.delete("\"") + number + pynutil.delete("\"")
        )

        conj_values = pynini.union("la", "spre")
        conj = (
            delete_extra_space
            + pynutil.delete("conj:")
            + delete_extra_space
            + pynutil.delete("\"") + conj_values + pynutil.delete("\"")
        )

        second = (
            delete_extra_space
            + pynutil.delete("second:")
            + delete_extra_space
            + pynutil.delete("\"") + number + pynutil.delete("\"")
        )

        graph = (
            open_outer
            + first
            + conj
            + second
            + delete_extra_space
            + close_outer
        )

        self.fst = graph.optimize()
