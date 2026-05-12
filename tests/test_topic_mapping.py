import pytest

from victron_mqtt_bridge.topic_mapping import resolve_topic

# ---------------------------------------------------------------------------
# Exact (leaf) mappings
# ---------------------------------------------------------------------------


def test_exact_match_returns_mapped_topic() -> None:
    mapping = {"system/0/Dc/Battery/Soc": "victron/battery/soc"}
    assert resolve_topic("system/0/Dc/Battery/Soc", mapping) == "victron/battery/soc"


def test_exact_match_returns_none_for_unknown_path() -> None:
    mapping = {"system/0/Dc/Battery/Soc": "victron/battery/soc"}
    assert resolve_topic("system/0/Dc/Battery/Voltage", mapping) is None


def test_exact_match_is_tried_before_prefix_match() -> None:
    mapping = {
        "system/0/Dc/Battery/Soc": "victron/battery/soc-exact",
        "system/0/Dc/Battery/": "victron/battery/",
    }
    assert resolve_topic("system/0/Dc/Battery/Soc", mapping) == "victron/battery/soc-exact"


# ---------------------------------------------------------------------------
# Branch (prefix) mappings
# ---------------------------------------------------------------------------


def test_branch_mapping_forwards_suffix_to_downstream_prefix() -> None:
    mapping = {"system/0/Dc/Battery/": "victron/battery/"}
    assert resolve_topic("system/0/Dc/Battery/Soc", mapping) == "victron/battery/Soc"
    assert resolve_topic("system/0/Dc/Battery/Voltage", mapping) == "victron/battery/Voltage"


def test_branch_mapping_does_not_match_sibling_subtree() -> None:
    mapping = {"system/0/Dc/Battery/": "victron/battery/"}
    assert resolve_topic("system/0/Dc/Charger/Current", mapping) is None


def test_branch_mapping_longest_prefix_wins() -> None:
    mapping = {
        "system/0/Dc/": "victron/dc/",
        "system/0/Dc/Battery/": "victron/battery/",
    }
    assert resolve_topic("system/0/Dc/Battery/Soc", mapping) == "victron/battery/Soc"
    assert resolve_topic("system/0/Dc/Charger/Current", mapping) == "victron/dc/Charger/Current"


def test_branch_mapping_with_empty_downstream_prefix() -> None:
    mapping = {"system/0/": ""}
    assert resolve_topic("system/0/Dc/Battery/Soc", mapping) == "Dc/Battery/Soc"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_mapping_returns_none() -> None:
    assert resolve_topic("system/0/Dc/Battery/Soc", {}) is None


@pytest.mark.parametrize(
    "path",
    [
        "system/0/Dc/Battery",   # matches branch key prefix string but NOT the trailing-slash rule
        "system/0/Dc/Batter",    # partial segment name
    ],
)
def test_branch_mapping_does_not_match_partial_segment(path: str) -> None:
    mapping = {"system/0/Dc/Battery/": "victron/battery/"}
    assert resolve_topic(path, mapping) is None
