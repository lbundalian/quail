from .core import _TASKS,_CHECKS
def build_dot()->str:
    lines=["digraph quail {","  rankdir=LR;"]
    def add(n,kind):
        shape="box" if kind=="task" else "oval"
        lines.append(f'  "{n}" [shape={shape}];')
    for n in _TASKS: add(n,"task")
    for n in _CHECKS: add(n,"check")
    for n,fn in {**_TASKS,**_CHECKS}.items():
        for d in fn.__qmeta__["requires"]: lines.append(f'  "{d}" -> "{n}";')
    lines.append("}"); return "\n".join(lines)
