from registry import register
from . import logic
from . import display


@register("pressure", "Memory pressure via PSI (/proc/pressure/memory) + meminfo heuristics")
def feature_pressure(pid: int) -> None:
    data = logic.fetch()
    display.render(data)
