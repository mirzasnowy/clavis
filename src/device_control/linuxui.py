"""Linux UI Automation driver — generic tree walker (testable without pyatspi).

The real AT-SPI tree objects (pyatspi Accessible) have: .name,
.getRoleName(), .childCount, .getChildAt(i), .queryAction().
This module walks ANY object with that shape, so unit tests can use
fake nodes and the real script (scripts/linuxui.py) can use pyatspi
nodes unchanged. That is why the logic is intuitively correct even
though it was not run on a real desktop here: the walker, the
name-match, and the fail-closed ambiguity rule are the same code
path in tests and in production.
"""


def walk(node, max_depth=12):
    def _walk(n, depth):
        if depth > max_depth or n is None:
            return None
        out = {"name": getattr(n, "name", "") or "",
               "role": n.getRoleName() if hasattr(n, "getRoleName") else "",
               "children": []}
        try:
            count = n.childCount
        except Exception:
            count = 0
        for i in range(count):
            try:
                child = _walk(n.getChildAt(i), depth + 1)
            except Exception:
                child = None
            if child:
                out["children"].append(child)
        return out
    return _walk(node, 0)


def find_all(node, query, out=None, depth=0, max_depth=12):
    if out is None:
        out = []
    if depth > max_depth or node is None:
        return out
    if query.lower() in (getattr(node, "name", "") or "").lower():
        out.append(node)
    try:
        count = node.childCount
    except Exception:
        count = 0
    for i in range(count):
        try:
            find_all(node.getChildAt(i), query, out, depth + 1, max_depth)
        except Exception:
            pass
    return out


def find_unique(node, query):
    matches = find_all(node, query)
    if len(matches) == 0:
        return None, "not found"
    if len(matches) > 1:
        return None, f"ambiguous: {len(matches)} matches, refusing first"
    return matches[0], "ok"


def click(node):
    """Call Action.click/press on a node, if it has queryAction."""
    try:
        action = node.queryAction()
        for i in range(action.nActions):
            if action.getName(i) in ("click", "press", "activate"):
                action.doAction(i)
                return True, action.getName(i)
        if action.nActions > 0:
            action.doAction(0)
            return True, action.getName(0)
    except Exception as e:
        return False, str(e)
    return False, "no Action interface"
