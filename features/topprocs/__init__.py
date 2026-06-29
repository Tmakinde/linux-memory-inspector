from registry import register
from . import logic
from . import display


@register("topprocs", "Top 15 processes by RSS from /proc/[0-9]*/status")
def feature_topprocs(pid: int) -> None:
    data = logic.fetch()
    display.render(data)
