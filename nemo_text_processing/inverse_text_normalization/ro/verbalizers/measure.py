import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import (
    NEMO_CHAR,
    GraphFst,
    delete_extra_space,
    delete_space,
)


class MeasureFst(GraphFst):
    """
    Verbalizes measures like:
        measure { cardinal { integer: "12" } units: "kg" } -> 12 kg
        measure { cardinal: "2,5" units: "ore" } -> 2,5 ore
        measure { decimal { ... } units: "..." } -> ... ...
        measure { number: "3,5" units: "m" } -> 3,5 m (ex. "trei metri și jumătate")
    """

    def __init__(self, decimal: GraphFst, cardinal: GraphFst):
        super().__init__(name="measure", kind="verbalize")

        optional_sign = pynini.closure(
            pynini.cross('negative: "true"', "-") + delete_space, 0, 1
        )

        unit = (
            pynutil.delete("units:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_CHAR - " ", 1)
            + pynutil.delete("\"")
        )

        integer_part = (
            pynutil.delete('integer_part:')
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
        )

        separator = (
            pynutil.delete('morphosyntactic_features:')
            + delete_space
            + pynutil.delete('"')
            + pynini.union(",", ".")
            + pynutil.delete('"')
        )

        fractional_part = (
            pynutil.delete('fractional_part:')
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
        )

        graph_structured_decimal = (
            pynutil.delete("decimal {")
            + delete_space
            + optional_sign
            + integer_part
            + delete_space
            + separator
            + delete_space
            + fractional_part
            + delete_space
            + pynutil.delete("}")
        )

        graph_flat_decimal = (
            pynutil.delete("decimal:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
        )

        graph_decimal = graph_structured_decimal | graph_flat_decimal

        graph_flat_cardinal = (
            optional_sign
            + pynutil.delete("cardinal:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
        )

        graph_structured_cardinal = (
            pynutil.delete("cardinal {")
            + delete_space
            + optional_sign
            + pynutil.delete("integer:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
            + delete_space
            + pynutil.delete("}")
        )

        graph_number = (
            optional_sign
            + pynutil.delete("number:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(pynini.difference(NEMO_CHAR, '"'), 1)
            + pynutil.delete('"')
        )

        graph_cardinal = graph_structured_cardinal | graph_flat_cardinal | graph_number

        graph_measure = (
            pynutil.delete("measure {")
            + delete_space
            + (graph_cardinal | graph_decimal)
            + delete_space
            + pynutil.insert(" ")
            + unit
            + delete_space
            + pynutil.delete("}")
        )

        graph = graph_measure | (
            (graph_cardinal | graph_decimal)
            + delete_space
            + pynutil.insert(" ")
            + unit
        )

        self.fst = self.delete_tokens(graph).optimize()
