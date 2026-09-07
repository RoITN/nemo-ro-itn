import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst

class TimeFst(GraphFst):
    def __init__(self):
        super().__init__(name="time", kind="verbalize")

        hours_vals = pynini.union(*[f"{i:02d}" for i in range(24)])
        minutes_vals = pynini.union(*[f"{i:02d}" for i in range(60)])

        delete_space = pynutil.delete(pynini.closure(pynini.accep(" "), 0))

        optional_prefix = pynini.closure(
            delete_space +
            pynutil.delete("prefix:") +
            delete_space +
            pynutil.delete('"') + pynini.closure(pynini.difference(pynini.union("la ora", "ora", "până la ora", "în jurul orei", "după ora", "după orele", "de la ora", "ora locală"), ""), 1) + pynutil.delete('"') +
            pynini.accep(" "), 0, 1
        )

        hours = (
            delete_space +
            pynutil.delete("hours:") +
            delete_space +
            pynutil.delete('"') + hours_vals + pynutil.delete('"')
        )

        minutes = (
            delete_space +
            pynutil.delete("minutes:") +
            delete_space +
            pynutil.delete('"') + pynutil.insert(":") + minutes_vals + pynutil.delete('"')
        )

        time_expr = optional_prefix + hours + minutes

        self.fst = (
            pynutil.delete("time") +
            delete_space +
            pynutil.delete("{") +
            delete_space +
            time_expr +
            delete_space +
            pynutil.delete("}")
        ).optimize()
