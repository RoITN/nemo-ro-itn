import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst
from nemo_text_processing.inverse_text_normalization.ro.graph_utils import delete_space


class OrdinalFst(GraphFst):
    def __init__(self):
        super().__init__(name="ordinal", kind="verbalize")

        name = (
            pynutil.delete("tokens")
            + delete_space
            + pynutil.delete("{")
            + delete_space
            + pynutil.delete("name:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(
                pynini.difference(pynini.union(*"abcdefghijklmnopqrstuvwxyzăâîșțABCDEFGHIJKLMNOPQRSTUVWXYZ "), '"'), 1
            ).optimize()
            + pynutil.delete('"')
            + delete_space
            + pynutil.delete("}")
        )

        ordinal = (
            pynutil.delete("tokens")
            + delete_space
            + pynutil.delete("{")
            + delete_space
            + pynutil.delete("ordinal")
            + delete_space
            + pynutil.delete("{")
            + delete_space
            + pynutil.delete("integer:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(
                pynini.difference(pynini.union(*"IVXLCDM-aeiouăâșț "), '"'), 1
            ).optimize()
            + pynutil.delete('"')
            + delete_space
            + pynutil.delete("}")
            + delete_space
            + pynutil.delete("}")
        )

        graph = name + pynutil.insert(" ") + ordinal

        self.fst = graph.optimize()
