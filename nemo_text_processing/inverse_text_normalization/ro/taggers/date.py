import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import (
    INPUT_CASED,
    INPUT_LOWER_CASED,
    GraphFst,
    capitalized_input_graph,
    delete_extra_space,
    delete_space,
)
from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path
from nemo_text_processing.inverse_text_normalization.es.graph_utils import int_to_roman


class DateFst(GraphFst):
    def __init__(self, cardinal: GraphFst, input_case: str = INPUT_LOWER_CASED):
        super().__init__(name="date", kind="classify")

        graph_day_numeric = pynini.union(*[pynini.accep(str(i)) for i in range(1, 32)])

        graph_1_to_31 = pynini.union(
            pynini.string_file(get_abs_path("data/dates/days_1_to_31.tsv")),  # „doi” etc.
            graph_day_numeric  # „2”
        )
        day_graph = pynutil.insert('day: "') + graph_1_to_31 + pynutil.insert('"')


        graph_month = pynini.string_file(get_abs_path("data/dates/months.tsv"))
        if input_case == INPUT_CASED:
            graph_month |= pynini.string_file(get_abs_path("data/dates/months_cased.tsv"))
        month_graph = pynutil.insert("month: \"") + graph_month + pynutil.insert("\"")

        valid_years = [str(y) for y in range(100, 2101)]
        graph_year_only = cardinal.graph @ pynini.union(*valid_years)
        year_graph = pynutil.insert('year: "') + graph_year_only + pynutil.insert('"')

        optional_de = pynini.closure(delete_space + pynutil.delete("de") + delete_extra_space, 0, 1)

        graph_dm = day_graph + pynutil.insert(" ") + optional_de + delete_space + month_graph
        graph_dmy = graph_dm + pynutil.insert(" ") + delete_space + year_graph
        graph_my = month_graph + pynutil.insert(" ") + delete_space + year_graph
        graph_y = pynutil.delete("anul") + delete_space + year_graph

        roman_numerals = int_to_roman(cardinal.graph)
        roman_centuries = pynini.union("secolul ", "anul ") + roman_numerals
        roman_centuries_graph = pynutil.insert("year: \"") + roman_centuries + pynutil.insert("\"")

        graph_suffix = pynini.string_file(get_abs_path("data/dates/year_suffix.tsv")).invert()
        if input_case == INPUT_CASED:
            graph_suffix |= pynini.string_file(get_abs_path("data/dates/year_suffix_cased.tsv")).invert()
        year_with_suffix = (
            pynutil.insert('year: "') + graph_year_only + pynutil.insert(" ")
            + graph_suffix + pynutil.insert('"')
        )
        year_with_suffix_graph = pynutil.insert("year: \"") + year_with_suffix + pynutil.insert("\"")

        final_graph = graph_dmy | graph_dm | graph_my | graph_y | roman_centuries_graph | year_with_suffix_graph
        final_graph += pynutil.insert(" preserve_order: true")

        if input_case == INPUT_CASED:
            final_graph |= capitalized_input_graph(final_graph)

        self.fst = self.add_tokens(final_graph).optimize()
