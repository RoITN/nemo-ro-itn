import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst
from nemo_text_processing.text_normalization.en.graph_utils import delete_space, NEMO_DIGIT


class PercentFst(GraphFst):
    """
    Verbalizes:
        percent { number: "95" }                 → 95%
        percent { permille: "1,35" }             → 1,35‰
        percent { number: "25" } de procente     → 25%
        percent { number: "10" } la sută         → 10%
    """

    def __init__(self):
        super().__init__(name="percent", kind="verbalize")

        space = pynini.closure(pynini.accep(" "), 0)
        allowed_chars = pynini.union(*"0123456789,.-")

        suffix = pynini.closure(
            pynutil.delete("la sută") |
            pynutil.delete("la suta") |
            pynutil.delete("de procente") |
            pynutil.delete("procente"), 0
        )

        number = (
            pynutil.delete("percent") + space +
            pynutil.delete("{") + space +
            pynutil.delete("number:") + space +
            pynutil.delete('"') +
            pynini.closure(allowed_chars, 1) +
            pynutil.delete('"') + space +
            pynutil.delete("}") +
            pynutil.insert("%")
        )

        decimal_number = pynini.closure(NEMO_DIGIT, 1) + pynini.accep(",") + pynini.closure(NEMO_DIGIT, 1)

        permille = (
            pynutil.delete("percent") + space +
            pynutil.delete("{") + space +
            pynutil.delete("permille:") + space +
            pynutil.delete('"') +
            decimal_number +
            pynutil.delete('"') + space +
            pynutil.delete("}") +
            pynutil.insert("‰")
        )


        graph = pynini.union(number, permille)
        self.fst = graph.optimize()
