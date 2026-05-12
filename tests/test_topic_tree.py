from victron_mqtt_bridge.topic_tree import build_topic_tree, render_topic_tree

# ---------------------------------------------------------------------------
# build_topic_tree
# ---------------------------------------------------------------------------


def test_should_build_nested_tree_when_paths_share_common_prefix() -> None:
    paths = ["battery/0/Soc", "battery/0/Voltage"]
    tree = build_topic_tree(paths)
    assert "battery" in tree
    assert "0" in tree["battery"]
    assert "Soc" in tree["battery"]["0"]
    assert "Voltage" in tree["battery"]["0"]


def test_should_build_separate_branches_when_paths_have_no_common_prefix() -> None:
    paths = ["battery/0/Soc", "grid/L1/Power"]
    tree = build_topic_tree(paths)
    assert "battery" in tree
    assert "grid" in tree


def test_should_return_empty_tree_when_given_no_paths() -> None:
    assert build_topic_tree([]) == {}


def test_should_produce_leaf_nodes_with_empty_dict_when_path_has_no_children() -> None:
    tree = build_topic_tree(["battery/0/Soc"])
    assert tree["battery"]["0"]["Soc"] == {}


def test_should_sort_siblings_alphabetically_when_building_tree() -> None:
    paths = ["system/Voltage", "battery/Soc", "grid/Power"]
    tree = build_topic_tree(paths)
    assert list(tree.keys()) == ["battery", "grid", "system"]


def test_should_merge_shared_ancestors_when_multiple_paths_share_them() -> None:
    paths = ["dc/0/Voltage", "dc/0/Current", "dc/1/Voltage"]
    tree = build_topic_tree(paths)
    assert set(tree["dc"].keys()) == {"0", "1"}
    assert set(tree["dc"]["0"].keys()) == {"Current", "Voltage"}


# ---------------------------------------------------------------------------
# render_topic_tree
# ---------------------------------------------------------------------------


def test_should_render_single_leaf_with_last_connector() -> None:
    tree = build_topic_tree(["Soc"])
    lines = render_topic_tree(tree)
    assert lines == ["└── Soc"]


def test_should_use_branch_connector_for_non_last_siblings() -> None:
    tree = build_topic_tree(["Soc", "Voltage"])
    lines = render_topic_tree(tree)
    assert lines[0] == "├── Soc"
    assert lines[1] == "└── Voltage"


def test_should_indent_children_under_non_last_parent() -> None:
    tree = build_topic_tree(["battery/Soc", "grid/Power"])
    lines = render_topic_tree(tree)
    # battery is non-last → children indented with │
    soc_line = next(line for line in lines if "Soc" in line)
    assert soc_line.startswith("│   ")


def test_should_indent_children_under_last_parent_with_spaces() -> None:
    tree = build_topic_tree(["battery/Soc", "grid/Power"])
    lines = render_topic_tree(tree)
    # grid is last → children indented with spaces, not │
    power_line = next(line for line in lines if "Power" in line)
    assert power_line.startswith("    ")


def test_should_return_empty_list_when_tree_is_empty() -> None:
    assert render_topic_tree({}) == []


def test_should_render_deep_nesting_with_correct_prefix_at_each_level() -> None:
    tree = build_topic_tree(["system/0/Dc/Battery/Soc"])
    lines = render_topic_tree(tree)
    # Every level should be present as a line
    keys = ["system", "0", "Dc", "Battery", "Soc"]
    for key in keys:
        assert any(key in line for line in lines)
