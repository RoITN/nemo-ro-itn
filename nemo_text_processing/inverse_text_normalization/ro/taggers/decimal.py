import pynini
from pynini.lib import pynutil
from nemo_text_processing.inverse_text_normalization.ro.taggers.cardinal import CardinalFst
from nemo_text_processing.inverse_text_normalization.ro.graph_utils import delete_space
from nemo_text_processing.text_normalization.en.graph_utils import (
    GraphFst,
    NEMO_DIGIT,
    NEMO_SIGMA,
    TO_LOWER,
    MIN_NEG_WEIGHT,
    INPUT_LOWER_CASED,
    INPUT_CASED,
)


class DecimalFst(GraphFst):
    """
    FST pentru clasificarea numerelor zecimale în română.
    Exemple acceptate: "1,07", "unu virgulă șapte", "unu virgulă zero cinci", "douăzeci și trei virgulă optsprezece", "unu virgulă patru milioane"
    """
    def __init__(self, cardinal: CardinalFst, input_case: str = INPUT_LOWER_CASED):
        super().__init__(name="decimal", kind="classify")

        opt_sign = pynini.closure(
            pynutil.insert('negative: "true"') + delete_space,
            0, 1
        )

        digit  = NEMO_DIGIT
        digits = digit.plus
        base_numeric = (
            opt_sign
            + pynutil.insert('integer_part: "')
            + digits
            + pynutil.delete(",")
            + pynutil.insert('" ')
            + pynutil.insert('morphosyntactic_features: "," ')
            + pynutil.insert('fractional_part: "')
            + digit ** (1, 2)
            + pynutil.insert('" ')
        )


        graph_integer = (
            pynutil.insert('integer_part: "')
            + cardinal.graph_no_exception
            + pynutil.insert('" ')
        )
        decimal_point = pynini.union(
            pynini.cross("virgulă", 'morphosyntactic_features: "," '),
            pynini.cross("virgula", 'morphosyntactic_features: "," ')
        )
        if input_case == INPUT_CASED:
            decimal_point |= pynini.cross("Virgulă", 'morphosyntactic_features: "," ')

        digit_map = pynini.string_map([
            ("zero", "0"), ("unu", "1"), ("doi", "2"), ("două", "2"), ("doua", "2"),
            ("trei", "3"), ("patru", "4"), ("cinci", "5"), ("șase", "6"), ("sase", "6"),
            ("șapte", "7"), ("sapte", "7"), ("opt", "8"), ("nouă", "9"), ("noua", "9"),
        ])
        if input_case == INPUT_CASED:
            digit_map |= pynini.string_map([
                ("Zero", "0"), ("Unu", "1"), ("Doi", "2"), ("Trei", "3"),
                ("Patru", "4"), ("Cinci", "5"), ("Șase", "6"), ("Sase", "6"),
                ("Șapte", "7"), ("Sapete", "7"), ("Opt", "8"), ("Nouă", "9"), ("Noua", "9"),
            ])
        one_digit   = digit_map
        two_digits  = digit_map + delete_space + digit_map
        cardinal_two= cardinal.graph_no_exception @ (NEMO_DIGIT ** 2)
        two_digit_graph = two_digits | cardinal_two | one_digit
        graph_frac = (
            pynutil.insert('fractional_part: "')
            + two_digit_graph
            + pynutil.insert('"')
        )

        base_spelled = (
            opt_sign
            + graph_integer + delete_space
            + decimal_point + delete_space
            + graph_frac
        )

        scale_map = [
            ("milion", "milion"), ("milioane", "milioane"),
            ("miliard", "miliard"), ("miliarde", "miliarde"),
        ]
        scale_graph = pynini.union(*[
            pynini.cross(inp, f' scale: "{tok}" ')
            for inp, tok in scale_map
        ]).optimize()

        scale_suffix = (
            delete_space
            + pynini.closure(pynutil.delete("de") + delete_space, 0, 1)
            + scale_graph
        )
       
        numeric_decimal = base_numeric.optimize()
        spelled_decimal = base_spelled.optimize()

        final_graph_wo_negative = self.add_tokens(numeric_decimal | spelled_decimal).optimize()
        self.final_graph_wo_negative = final_graph_wo_negative

        weighted_lower = pynutil.add_weight(
            pynini.compose(TO_LOWER + NEMO_SIGMA, final_graph_wo_negative),
            MIN_NEG_WEIGHT
        )

        self.fst = (final_graph_wo_negative | weighted_lower).optimize()
        self.verbalizable_graph = (
            pynini.cross("zero", "0") | cardinal.graph_no_exception
        ) + delete_space + pynini.union(
                pynini.cross("virgulă", ","),
                pynini.cross("virgula", ",")
            ) + delete_space + two_digit_graph
        self.graph = self.verbalizable_graph.optimize()



