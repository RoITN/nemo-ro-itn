import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import (
    NEMO_NOT_QUOTE,
    GraphFst,
    delete_space,
)


class DecimalFst(GraphFst):
    """
    FST de verbalizare pentru decimale în română:
      - decimal { negative: "true" integer_part: "1"
                  morphosyntactic_features: ","  fractional_part: "26" }
        -> -1,26

      - decimal { negative: "false" integer_part: "1"
                  morphosyntactic_features: ","  fractional_part: "26"
                  scale: "milioane" }
        -> 1,26 milioane

      - decimal { negative: "false" integer_part: "2" scale: "milion" }
        -> 2 milion
    """

    def __init__(self):
        super().__init__(name="decimal", kind="verbalize")

        optional_sign = pynini.closure(
            pynini.cross('negative: "true"', "-") + delete_space,
            0,
            1,
        )

        integer = (
            pynutil.delete("integer_part:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        optional_integer = pynini.closure(integer + delete_space, 0, 1)

        decimal_point = pynini.cross(
            'morphosyntactic_features: ","',
            ",",
        )

        fractional = (
            decimal_point
            + delete_space
            + pynutil.delete("fractional_part:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        optional_fractional = pynini.closure(fractional + delete_space, 0, 1)

        scale = (
            pynutil.delete("scale:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.union("milion", "milioane", "miliard", "miliarde")
            + pynutil.delete("\"")
        )
        optional_scale = pynini.closure(pynutil.insert(" ") + scale + delete_space, 0, 1)

        graph = optional_integer + optional_fractional + optional_scale
        self.numbers = graph
        graph = optional_sign + graph

        self.fst = self.delete_tokens(graph).optimize()
