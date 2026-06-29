from registry import register
from . import logic
from . import display


@register("overview", "Process memory overview from /proc/<pid>/status")
def feature_overview(pid: int) -> None:
    data = logic.fetch(pid)
    display.render(data)
