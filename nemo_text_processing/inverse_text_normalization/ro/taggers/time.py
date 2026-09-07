import pynini
from pynini.lib import pynutil
from nemo_text_processing.text_normalization.en.graph_utils import GraphFst
from nemo_text_processing.inverse_text_normalization.ro.utils import get_abs_path
from nemo_text_processing.text_normalization.en.graph_utils import INPUT_LOWER_CASED

insert_space = pynini.accep(" ")

class TimeFst(GraphFst):
    def __init__(self, input_case: str = INPUT_LOWER_CASED):
        super().__init__(name="time", kind="classify")

        hours_graph = pynini.string_file(get_abs_path("data/time/time_to.tsv"))
        minutes_graph = pynini.string_file(get_abs_path("data/time/minutes.tsv"))

        trigger_phrases = pynini.union(
            "la ora", "ora", "până la ora", "în jurul orei",
            "după ora", "după orele", "de la ora", "ora locală"
        )
        trigger = (
            pynutil.insert("prefix: \"") + trigger_phrases + pynutil.insert("\"") +
            pynini.closure(pynini.accep(" "), 1)
        )

        hour = pynutil.insert("hours: \"") + hours_graph + pynutil.insert("\"")

        optional_connector = pynini.closure(
            pynini.union(
                pynutil.delete(pynini.closure(pynini.accep(" "), 0) + "și" + pynini.closure(pynini.accep(" "), 1)),
                insert_space
            ),
            0, 1
        )

        minute = minutes_graph + pynini.closure(
            pynutil.delete(pynini.closure(pynini.accep(" "), 0) + pynini.union("minute", "de minute")),
            0, 1
        )

        explicit_minute = pynutil.insert(" minutes: \"") + minute + pynutil.insert("\"")
        default_minute = pynutil.insert(" minutes: \"00\"")

        part_of_day = pynutil.delete(
            pynini.union("dimineața", "seara", "noaptea", "după-amiaza")
        ) + pynini.closure(pynini.accep(" "), 0, 1)


        graph_hour_minute = trigger + hour + optional_connector + explicit_minute + pynini.closure(insert_space + part_of_day, 0, 1)
        graph_hour_only = trigger + hour + default_minute + pynini.closure(insert_space + part_of_day, 0, 1)

        morning = pynutil.delete("dimineața")
        night = pynutil.delete("noaptea")
        afternoon = pynutil.delete("după-amiaza")
        evening = pynutil.delete("seara")

        hour_am = pynini.string_file(get_abs_path("data/time/time_am.tsv"))
        hour_pm = pynini.string_file(get_abs_path("data/time/time_pm.tsv"))

        implicit_morning = (
            pynutil.insert("hours: \"") + hour_am + pynutil.insert("\"") +
            insert_space + (morning | night) +
            default_minute
        )

        implicit_evening = (
            pynutil.insert("hours: \"") + hour_pm + pynutil.insert("\"") +
            insert_space + (evening | afternoon) +
            default_minute
        )

        midnight_case = (
            pynutil.insert("hours: \"00\"") +
            insert_space + night +
            default_minute
        )

        noon_case = (
            pynutil.insert("hours: \"12\"") +
            insert_space + afternoon +
            default_minute
        )

        implicit_time = implicit_morning | implicit_evening | midnight_case | noon_case

        graph = graph_hour_minute | graph_hour_only | implicit_time

        self.fst = self.add_tokens(graph).optimize()
