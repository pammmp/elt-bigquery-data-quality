from elt_dq.generate_data import DEFECT_COUNTS, generate


def test_same_seed_same_data():
    a, _ = generate(100, seed=7)
    b, _ = generate(100, seed=7)
    assert a == b


def test_planted_defects_match_the_plan():
    _, planted = generate(400, seed=42, defects=True)
    assert planted == DEFECT_COUNTS


def test_clean_data_has_no_defects():
    tables, planted = generate(400, seed=42, defects=False)
    assert all(v == 0 for v in planted.values())
    assert all(o["supplier_id"] for o in tables["orders"])
    assert all(int(i["quantity"]) > 0 for i in tables["order_items"])
    ids = [o["order_id"] for o in tables["orders"]]
    assert len(ids) == len(set(ids))


def test_header_defects_do_not_overlap():
    tables, _ = generate(400, seed=42, defects=True)
    first = {}
    for o in tables["orders"]:
        first.setdefault(o["order_id"], o)
    broken = [
        o
        for o in first.values()
        if not o["supplier_id"] or o["supplier_id"] == "S99" or o["status"] == "pendente??"
    ]
    assert len(broken) == 5 + 4 + 2
