import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_space


class OrdinalFst(GraphFst):
    def __init__(self):
        super().__init__(name="ordinal", kind="classify")

        roman_ordinal_map = {
            "a doua": "II-a",
            "al doilea": "II-lea",
            "a treia": "III-a",
            "al treilea": "III-lea",
            "a patra": "IV-a",
            "al patrulea": "IV-lea",
            "a cincea": "V-a",
            "al cincilea": "V-lea",
            "a șasea": "VI-a",
            "al șaselea": "VI-lea",
            "a șaptea": "VII-a",
            "al șaptelea": "VII-lea",
            "a opta": "VIII-a",
            "al optulea": "VIII-lea",
            "a noua": "IX-a",
            "al nouălea": "IX-lea",
            "a zecea": "X-a",
            "al zecelea": "X-lea",
            "a douăzeci și cincea": "XXV-a",
            "al nouăsprezecelea": "XIX-lea",
        }

        triggers = ["clasa", "secolul", "Elisabeta"]

        trigger_graph = pynini.union(*triggers)

        name_graph = (
            pynutil.insert("tokens { name: \"") +
            trigger_graph +
            pynutil.insert("\" }")
        )

        ordinal_graph = pynini.string_map([
            (k, f'tokens {{ ordinal {{ integer: "{v}" }} }}') for k, v in roman_ordinal_map.items()
        ])

        graph = (
            name_graph +
            delete_space +
            ordinal_graph
        )

        self.fst = graph.optimize()
