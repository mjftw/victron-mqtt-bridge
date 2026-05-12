from collections.abc import Mapping

# Maps a relative Victron topic path (the segment after N/<serial>/) to the
# full topic to publish on the downstream broker.
#
# Leaf mapping  – exact path:   "system/0/Dc/Battery/Soc" -> "victron/battery/soc"
# Branch mapping – trailing '/': "system/0/Dc/Battery/"    -> "victron/battery/"
#   All paths under the branch are forwarded with the suffix appended to the
#   downstream prefix, e.g. system/0/Dc/Battery/Soc -> victron/battery/Soc.
type TopicMapping = Mapping[str, str]


def resolve_topic(relative_path: str, mapping: TopicMapping) -> str | None:
    """Resolve a relative Victron path to a downstream topic.

    Tries exact match first, then longest-prefix match for mapping keys that
    end with '/' (branch mappings). When multiple branch keys match, the
    longest (most specific) one wins.
    """
    if (exact := mapping.get(relative_path)) is not None:
        return exact

    best_key: str | None = None
    for key in mapping:
        if key.endswith("/") and relative_path.startswith(key):
            if best_key is None or len(key) > len(best_key):
                best_key = key

    if best_key is None:
        return None

    return mapping[best_key] + relative_path[len(best_key):]
