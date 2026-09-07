import pynini
from pynini.lib import pynutil
from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path
from nemo_text_processing.text_normalization.en.graph_utils import (
    INPUT_CASED,
    INPUT_LOWER_CASED,
    GraphFst,
    insert_space
)
from nemo_text_processing.inverse_text_normalization.ro.graph_utils import (
    NEMO_DIGIT, NEMO_ALPHA, NEMO_CHAR, NEMO_SPACE, RO_MINUS, delete_space,
    capitalized_input_graph
)


class CardinalFst(GraphFst):
    """
    FST pentru clasificarea numerelor cardinale în română,
    până la 10^9 („miliarde”). Convertește „o mie”, „douăzeci și trei”,
    „minus cinci sute” în formă `{ integer: "..." }`.
    """

    def __init__(self, input_case: str = INPUT_LOWER_CASED):
        super().__init__(name="cardinal", kind="classify")
        self.input_case = input_case

        graph_zero      = pynini.string_file(get_abs_path("data/numbers/zero.tsv"))
        graph_digit     = pynini.string_file(get_abs_path("data/numbers/digit.tsv"))
        graph_ties      = pynini.string_file(get_abs_path("data/numbers/ties.tsv"))
        graph_teen      = pynini.string_file(get_abs_path("data/numbers/teen.tsv"))
        graph_hundreds  = pynini.string_file(get_abs_path("data/numbers/hundreds.tsv"))

        graph_digit |= NEMO_DIGIT                                # „0”–„9” din input
        graph_digit |= pynini.cross("un", "1")
        graph_digit |= pynini.cross("una",  "1")               # „una" → 1
        graph_digit |= pynini.cross("două", "2")               # „două"→ 2
        graph_digit |= pynini.cross("o",    "1")               # „o" → 1
        graph_digit = graph_digit.optimize()

        ties = {
            "douăzeci": 20, "douazeci": 20, "treizeci": 30, "patruzeci": 40, "cincizeci": 50,
            "șaizeci": 60, "saizeci": 60, "șaptezeci": 70, "saptezeci": 70, "optzeci": 80, "nouăzeci": 90, "nouazeci": 90
        }
        units = {
            "unu": 1, "o": 1, "una": 1, "un": 1, "doi": 2, "două": 2, "doua": 2, "trei": 3, "patru": 4,
            "cinci": 5, "șase": 6, "sase": 6, "șapte": 7, "sapte": 7, "opt": 8, "nouă": 9, "noua": 9
        }

        connectors = [" și ", " si "]
        pairs = []
        for tie_word, tie_val in ties.items():
            for unit_word, unit_val in units.items():
                for conj in connectors:
                    full_expr = f"{tie_word}{conj}{unit_word}"
                    result = str(tie_val + unit_val)
                    pairs.append((full_expr, result))

        tens_then_unit = pynini.string_map(pairs).optimize()
        tens_only = graph_ties + pynutil.insert("0")
        teen = graph_teen
        numeric_two = NEMO_DIGIT + NEMO_DIGIT
        graph_two_digit = (
            tens_then_unit
            | tens_only
            | teen
            | numeric_two
        ).optimize()

        # graph_hundreds_fallback = (
        #     graph_digit
        #     + delete_space
        #     + (pynutil.delete("sută") | pynutil.delete("sute") | pynutil.delete("suta"))
        # )
        graph_hundreds = graph_hundreds.optimize()

        graph_hundreds_plural = (
            graph_digit
            + delete_space
            + pynutil.delete("sute")
        )
        graph_hundreds_digit = (graph_hundreds | graph_hundreds_plural).optimize()

        hundreds_then_two  = graph_hundreds_digit + delete_space + graph_two_digit
        hundreds_then_unit = graph_hundreds_digit + delete_space + pynutil.insert("0") + graph_digit
        hundreds_only      = graph_hundreds_digit + pynutil.insert("00")

        two_digit_only = graph_two_digit
        unit_only      = graph_digit

        graph_hundred_component = pynini.union(
            hundreds_then_two,
            hundreds_then_unit,
            hundreds_only,
            two_digit_only,
            unit_only,
        ).optimize()

        graph_hundred_component_at_least_one_none_zero_digit = (
            graph_hundred_component
            @ (pynini.closure(NEMO_DIGIT) + (NEMO_DIGIT - "0") + pynini.closure(NEMO_DIGIT))
        ).optimize()


        graph_singular_milion = pynini.cross("un milion", "1 milion")
        if input_case == INPUT_CASED:
            graph_singular_milion |= pynini.cross("Un milion", "1 milion")
        graph_singular_milion = graph_singular_milion.optimize()

        suffix_milioane = pynini.union("milion", "milioane")
        if input_case == INPUT_CASED:
            suffix_milioane |= pynini.union("Milion", "Milioane")
        suffix_milioane = suffix_milioane.optimize()

        graph_millones = (
            graph_singular_milion
            | (
                graph_hundred_component_at_least_one_none_zero_digit
                + insert_space
                + suffix_milioane
            )
        ).optimize()

        graph_miliarde = (
            graph_hundred_component_at_least_one_none_zero_digit
            + delete_space
            + pynini.accep("de") + delete_space
            + (self.delete_word("miliard") | self.delete_word("miliarde"))
        ).optimize()

        base_hundreds = graph_hundred_component_at_least_one_none_zero_digit
        base_unit_o = pynini.cross("o", "1")
        prefix = (base_hundreds | base_unit_o).optimize()

        prefix_mii = (
            prefix
            + delete_space
            + pynini.closure(pynutil.delete("de") + delete_space, 0, 1)
            + (self.delete_word("mie") | self.delete_word("mii"))
        ).optimize()

        suf1 = pynutil.insert("00") + graph_digit
        suf2 = pynutil.insert("0")  + graph_two_digit
        numeric_three = NEMO_DIGIT ** 3
        spelled_hundreds = hundreds_then_two | hundreds_then_unit | hundreds_only
        suf3 = (numeric_three | spelled_hundreds).optimize()

        sufix_pad = (suf1 | suf2 | suf3).optimize()

        graph_thousands_with_remainder = (
            prefix_mii + delete_space + sufix_pad
        ).optimize()

        graph_thousands_only = (
            prefix_mii + pynutil.insert("000")
        ).optimize()

        graph = pynini.union(
            # 1) miliarde + milioane + mii cu rest + sute
            graph_miliarde
            + delete_space + graph_millones
            + delete_space + graph_thousands_with_remainder
            + delete_space + graph_hundred_component,

            # 2) miliarde + milioane + mii fără rest
            graph_miliarde
            + delete_space + graph_millones
            + delete_space + graph_thousands_only,

            # 3) miliarde + milioane
            graph_miliarde
            + delete_space + graph_millones,

            # 4) milioane + mii cu rest + sute
            graph_millones
            + delete_space + graph_thousands_with_remainder
            + delete_space + graph_hundred_component,

            # 5) milioane + mii fără rest
            graph_millones
            + delete_space + graph_thousands_only,

            # 6) milioane pure
            graph_millones,

            # 7) mii cu rest
            graph_thousands_with_remainder,

            # 8) mii fără rest
            graph_thousands_only,

            # 9) sute și mai jos
            graph_hundred_component,

            # 10) zero
            graph_zero,
        ).optimize()

        self.graph_digit = graph_digit

        self.graph_no_exception = graph

        digits_up_to_thousand = NEMO_DIGIT | (NEMO_DIGIT ** 2) | (NEMO_DIGIT ** 3)
        numbers_up_to_thousand = pynini.compose(self.graph_no_exception, digits_up_to_thousand).optimize()
        self.numbers_up_to_thousand = numbers_up_to_thousand.optimize()

        digits_up_to_million = (
            NEMO_DIGIT
            | (NEMO_DIGIT ** 2)
            | (NEMO_DIGIT ** 3)
            | (NEMO_DIGIT ** 4)
            | (NEMO_DIGIT ** 5)
            | (NEMO_DIGIT ** 6)
        )
        numbers_up_to_million = pynini.compose(graph, digits_up_to_million).optimize()
        self.numbers_up_to_million = numbers_up_to_million.optimize()

        if input_case == INPUT_CASED:
            graph |= capitalized_input_graph(graph)
            graph_digit |= capitalized_input_graph(graph_digit)
            graph_zero |= capitalized_input_graph(graph_zero)
            self.graph_no_exception |= capitalized_input_graph(self.graph_no_exception).optimize()
            self.numbers_up_to_thousand |= capitalized_input_graph(self.numbers_up_to_thousand).optimize()

        graph_exception = pynini.project(graph_digit, "input")
        graph_exception = (graph_exception | pynini.accep("zece")).optimize()

        numeric_sequence = NEMO_DIGIT + pynini.closure(NEMO_DIGIT)
        graph_exception = (graph_exception | numeric_sequence).optimize()

        self.graph = ((pynini.project(graph, "input") - graph_exception) @ graph).optimize()

        optional_minus_graph = pynini.closure(
            pynutil.insert("negative: ")
            + pynini.cross(RO_MINUS, "\"-\"")
            + NEMO_SPACE,
            0,
            1,
        )

        final_graph = optional_minus_graph + pynutil.insert("integer: \"") + self.graph + pynutil.insert("\"")
        final_graph = self.add_tokens(final_graph)
        self.fst = final_graph.optimize()

    def delete_word(self, word: str):
        forms = [word]
        if word in {'sută', 'suta', 'mie'}:
            forms.append('o')
        if self.input_case == INPUT_CASED:
            forms = [f.capitalize() for f in forms]
        return pynini.union(*[pynutil.delete(f) for f in forms]).optimize()
