from registry import register
from . import logic
from . import display


@register("meminfo", "System-wide memory from /proc/meminfo")
def feature_meminfo(pid: int) -> None:
    data = logic.fetch()
    display.render(data)
