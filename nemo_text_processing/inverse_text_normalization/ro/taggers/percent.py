import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import GraphFst
from nemo_text_processing.inverse_text_normalization.ro.graph_utils import capitalized_input_graph

from nemo_text_processing.inverse_text_normalization.ro.graph_utils import delete_space


class PercentFst(GraphFst):
    """
    Clasificator pentru expresii procentuale și permille:
        - zece la sută → 10%
        - 25 la sută → 25%
        - zero virgulă nouă la mie → 0,9‰
    """

    def __init__(self, cardinal: GraphFst, decimal: GraphFst):
        super().__init__(name="percent", kind="classify")

        short_percent_map = pynini.string_map([
            ("unu", "1"), ("una", "1"), ("un", "1"),
            ("doi", "2"), ("două", "2"), ("doua", "2"),
            ("trei", "3"), ("patru", "4"), ("cinci", "5"),
            ("șase", "6"), ("sase", "6"), ("șapte", "7"),
            ("sapte", "7"), ("opt", "8"), ("nouă", "9"),
            ("noua", "9"), ("zece", "10")
        ]).optimize()


        ties = {
            "douăzeci": 20, "douazeci": 20, "treizeci": 30, "patruzeci": 40, "cincizeci": 50,
            "șaizeci": 60, "saizeci": 60, "șaptezeci": 70, "saptezeci": 70,
            "optzeci": 80, "nouăzeci": 90, "nouazeci": 90
        }
        units = {
            "unu": 1, "o": 1, "una": 1, "un": 1, "doi": 2, "două": 2, "doua": 2,
            "trei": 3, "patru": 4, "cinci": 5, "șase": 6, "sase": 6,
            "șapte": 7, "sapte": 7, "opt": 8, "nouă": 9, "noua": 9
        }
        connectors = [" și ", " si "]

        pairs = []
        for tie_word, tie_val in ties.items():
            for unit_word, unit_val in units.items():
                for conj in connectors:
                    expr = f"{tie_word}{conj}{unit_word}"
                    result = str(tie_val + unit_val)
                    pairs.append((expr, result))

        def capitalize_first_word(expr: str):
            words = expr.split()
            if not words:
                return expr
            words[0] = words[0].capitalize()
            return " ".join(words)

        capitalized_first_only_pairs = [
            (capitalize_first_word(k), v) for k, v in pairs
        ]

        tens_then_unit_graph = pynini.string_map(pairs + capitalized_first_only_pairs).optimize()

        percent_cardinal_graph = short_percent_map | tens_then_unit_graph | cardinal.graph_no_exception
        percent_cardinal_graph |= capitalized_input_graph(cardinal.graph_no_exception).optimize()


        decimal_graph = decimal.graph

        percent_suffix = pynini.union("la sută", "la suta", "de procente", "procent", "procente", "%")
        permille_suffix = pynini.union("la mie", "‰")

        hundred_percent = pynini.union("sută la sută", "suta la suta", "la sută la sută")
        hundred_graph = (
            pynutil.insert('number: "100"')
            + delete_space
            + pynutil.delete(hundred_percent)
        )

        percent_graph = (
            (decimal_graph | percent_cardinal_graph)
            + delete_space
            + percent_suffix
        )
        percent_graph = (
            pynutil.insert('number: "')
            + (decimal_graph | percent_cardinal_graph)
            + pynutil.insert('"')
            + delete_space
            + pynutil.delete(percent_suffix)
        )

        permille_graph = (
            pynutil.insert('permille: "')
            + (decimal_graph | percent_cardinal_graph) 
            + pynutil.insert('"')
            + delete_space
            + pynutil.delete(permille_suffix)
        )

        final = self.add_tokens(hundred_graph | percent_graph | permille_graph)
        self.fst = final.optimize()

    