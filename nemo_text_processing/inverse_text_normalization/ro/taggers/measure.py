import pynini
from pynini.lib import pynutil
from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path
from nemo_text_processing.inverse_text_normalization.ro.taggers.percent import PercentFst
from nemo_text_processing.text_normalization.en.graph_utils import (
    GraphFst,
    INPUT_LOWER_CASED,
    TO_LOWER,
    NEMO_SIGMA,
    convert_space,
    delete_space,
    delete_extra_space,
)


class MeasureFst(GraphFst):
    def __init__(self, cardinal: GraphFst, decimal: GraphFst, input_case: str = INPUT_LOWER_CASED):
        super().__init__(name="measure", kind="classify")

        cardinal_graph = cardinal.graph_no_exception
        percent = PercentFst(cardinal, decimal)

        casing_graph = pynini.closure(TO_LOWER | NEMO_SIGMA).optimize()

        graph_unit_singular = pynini.invert(
            pynini.string_file(get_abs_path("data/measures/measurements_singular.tsv"))
        )
        graph_unit_plural = pynini.invert(
            pynini.string_file(get_abs_path("data/measures/measurements_plural.tsv"))
        )
        graph_unit_singular = pynini.compose(casing_graph, graph_unit_singular).optimize()
        graph_unit_plural = pynini.compose(casing_graph, graph_unit_plural).optimize()

        unit_singular = convert_space(graph_unit_singular)
        unit_plural = convert_space(graph_unit_plural)
        unit_misc = pynutil.insert("/") + pynutil.delete("pe") + delete_space + convert_space(graph_unit_singular)

        minus = pynini.cross("-", "\"true\"") | pynini.cross("minus", "\"true\"")
        optional_sign = pynini.closure(pynutil.insert("negative: ") + minus + delete_extra_space, 0, 1)

        unit_singular_tag = (
            pynutil.insert('units: "')
            + (unit_singular | unit_misc | pynutil.add_weight(unit_singular + delete_space + unit_misc, 0.01))
            + pynutil.insert('"')
        )

        unit_plural_tag = (
            pynutil.insert('units: "')
            + (unit_plural | unit_misc | pynutil.add_weight(unit_plural + delete_space + unit_misc, 0.01))
            + pynutil.insert('"')
        )

        unit_plural_tag_decimal = unit_plural_tag


        unit_singular_to_plural_list = [
            ("an", "ani"),
            ("tonă", "tone"),
            ("lună", "luni"),
            ("oră", "ore"),
            ("metru", "m"),
            ("milion", "milioane"),
            ("punct", "puncte"),
        ]

        unit_singular_to_plural = pynini.string_map(unit_singular_to_plural_list)
        singular_unit = pynini.union(*[pynini.accep(u) for u, _ in unit_singular_to_plural_list])

        # DELETE un/o
        half_prefix = pynini.union(
            pynutil.delete("un"),
            pynutil.delete("o")
        ) + delete_space

        half_measure = (
            half_prefix
            + pynutil.insert('measure { number: "1,5" units: "')
            + (singular_unit @ unit_singular_to_plural)
            + pynutil.insert('" }')
            + delete_space
            + pynutil.delete(pynini.union("și", "si"))
            + delete_space
            + pynutil.delete("jumătate")
        ).optimize()

        scale_tag = pynutil.insert('scale: "') + pynini.union(
            "milion", "milioane", "miliard", "miliarde"
        ) + pynutil.insert('"') + delete_extra_space
        optional_scale_tag = pynini.closure(scale_tag, 0, 1)


        subgraph_decimal = (
            optional_scale_tag
            + optional_sign
            + decimal.final_graph_wo_negative
            + delete_extra_space
            + unit_plural_tag_decimal
        )


        singular_one = pynini.union(
            pynini.cross("un", "1"),
            pynini.cross("una", "1"),
            pynini.cross("o", "1"),
        )
        subgraph_singular_one = (
            pynutil.insert('cardinal { integer: "')
            + singular_one
            + pynutil.insert('" }')
            + delete_extra_space
            + unit_singular_tag
        )

        subgraph_cardinal = (
            pynutil.insert("cardinal { ")
            + optional_sign
            + pynutil.insert('integer: "')
            + cardinal_graph
            + pynutil.insert('" }')
            + delete_extra_space
            + unit_plural_tag
        ) | subgraph_singular_one

        subgraph_cardinal_half = self.build_half_expression(cardinal_graph, unit_plural)

        subgraph_percent = (
            percent.fst
            + delete_extra_space
            + unit_plural_tag_decimal
        )

        final_graph = (
            half_measure
            | subgraph_cardinal_half
            | subgraph_percent
            | subgraph_decimal
            | subgraph_cardinal
        )

        final_graph = self.add_tokens(final_graph)
        self.fst = final_graph.optimize()

    def build_half_expression(self, cardinal_graph, unit_graph):
        return (
            pynutil.insert('measure { number: "')
            + cardinal_graph
            + pynutil.insert(',5" units: "')
            + delete_space
            + unit_graph
            + pynutil.insert('" }')
            + delete_extra_space
            + pynutil.delete(pynini.union("și", "si"))
            + delete_extra_space
            + pynutil.delete("jumătate")
        ).optimize()
