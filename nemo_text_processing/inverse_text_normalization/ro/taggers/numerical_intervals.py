import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_extra_space
from nemo_text_processing.inverse_text_normalization.ro.taggers.cardinal import CardinalFst

class NumericalIntervalFst(GraphFst):
    def __init__(self, cardinal: GraphFst):
        super().__init__(name="numerical_interval", kind="classify")

        digit_cardinal = pynini.union(
            pynini.cross("zero", "0"),
            pynini.cross("unu", "1"), pynini.cross("una", "1"),
            pynini.cross("doi", "2"),
            pynini.cross("trei", "3"),
            pynini.cross("patru", "4"),
            pynini.cross("cinci", "5"),
            pynini.cross("șase", "6"),
            pynini.cross("șapte", "7"),
            pynini.cross("opt", "8"),
            pynini.cross("nouă", "9"),
            pynini.cross("zece", "10")
        )

        tagged_cardinal = (
            pynutil.delete("cardinal { integer: \"")
            + pynini.closure(pynini.union(*"0123456789"), 1)
            + pynutil.delete("\" }")
        )

        rest_cardinals = pynini.compose(cardinal.fst, tagged_cardinal)
        full_cardinal = (digit_cardinal | rest_cardinals).optimize()

        conj = pynini.union(
            pynini.cross("la", "la"),
            pynini.cross("spre", "spre")
        )

        interval_graph = (
            pynutil.insert("interval { first: \"")
            + full_cardinal
            + pynutil.insert("\"")
            + delete_extra_space
            + pynutil.insert(" conj: \"")
            + conj
            + pynutil.insert("\"")
            + delete_extra_space
            + pynutil.insert(" second: \"")
            + full_cardinal
            + pynutil.insert("\" }")
        )

        self.fst = interval_graph.optimize()
