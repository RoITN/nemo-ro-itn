import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import (
    NEMO_NOT_QUOTE,
    GraphFst,
    delete_extra_space,
    delete_space,
)


class DateFst(GraphFst):
    """
    Verbalizer for Romanian date, e.g.
        date { day: "2" month: "octombrie" preserve_order: true } -> 2 octombrie
        date { year: "2023" preserve_order: true } -> anul 2023
    """

    def __init__(self):
        super().__init__(name="date", kind="verbalize")

        day = (
            pynutil.delete("day:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )

        month = (
            pynutil.delete("month:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )

        year_plain = (
            pynutil.delete("year:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete('"')
        )

        year_with_anul = pynutil.insert("anul ") + year_plain

        optional_preserve_order = pynini.closure(
            delete_space
            + pynutil.delete("preserve_order:")
            + delete_space
            + pynutil.delete("true"),
            0,
            1,
        )

        # Combinări posibile
        graph_dmy = day + pynini.accep(" ") + month + pynini.accep(" ") + year_plain
        graph_dm = day + pynini.accep(" ") + month
        graph_my = month + pynini.accep(" ") + year_plain
        graph_y = year_with_anul

        graph = graph_dmy | graph_dm | graph_my | graph_y
        graph += optional_preserve_order

        self.fst = self.delete_tokens(graph).optimize()
