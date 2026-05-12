from collections.abc import Iterable

# Recursive type for the nested topic tree structure
type TopicTree = dict[str, TopicTree]


def build_topic_tree(paths: Iterable[str]) -> TopicTree:
    """Build a nested dict tree from a flat collection of slash-delimited paths."""
    tree: TopicTree = {}
    for path in sorted(paths):
        node = tree
        for part in path.split("/"):
            if part not in node:
                node[part] = {}
            node = node[part]
    return tree


def render_topic_tree(tree: TopicTree, prefix: str = "") -> list[str]:
    """Render a topic tree as ASCII art lines suitable for logging."""
    lines: list[str] = []
    items = list(tree.items())
    for i, (key, subtree) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{key}")
        if subtree:
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(render_topic_tree(subtree, child_prefix))
    return lines
