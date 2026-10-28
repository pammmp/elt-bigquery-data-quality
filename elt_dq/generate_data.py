"""Gerador de dados 100% fictícios, com defeitos plantados e contados.

Os defeitos existem para que as checagens tenham algo a encontrar. A função
devolve também quantos defeitos de cada tipo foram plantados, e os testes
conferem se as checagens encontram exatamente esses números.
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SUPPLIERS = [
    ("S01", "Alfa Embalagens", "BR"),
    ("S02", "Beta Polímeros", "BR"),
    ("S03", "Gama Metais", "BR"),
    ("S04", "Delta Químicos", "BR"),
    ("S05", "Épsilon Logística", "BR"),
    ("S06", "Zeta Componentes", "AR"),
    ("S07", "Eta Borrachas", "BR"),
    ("S08", "Teta Insumos", "CL"),
]
STATUSES = ["aberto", "aprovado", "entregue", "cancelado"]
PERIOD_START = date(2026, 1, 1)
PERIOD_DAYS = 180  # 2026-01-01 a 2026-06-29

DEFECT_COUNTS = {
    "duplicate_orders": 15,   # linhas repetidas em orders (a staging deduplica)
    "null_supplier": 5,       # pedido sem fornecedor
    "orphan_supplier": 4,     # fornecedor que não existe em suppliers
    "invalid_status": 2,      # status fora da lista aceita
    "messy_status": 6,        # status com caixa/espaços (a staging normaliza)
    "total_mismatch": 4,      # total do pedido diferente da soma dos itens
    "negative_quantity": 3,   # item com quantidade negativa
}


def generate(n_orders: int = 400, seed: int = 42, defects: bool = True):
    """Devolve (tabelas, defeitos_plantados).

    tabelas = {"suppliers": [...], "orders": [...], "order_items": [...]},
    cada uma como lista de dicionários com valores em texto (como chegariam
    de um arquivo ou de uma API).
    """
    rng = random.Random(seed)

    suppliers = [
        {"supplier_id": sid, "name": name, "country": country, "active": "true"}
        for sid, name, country in SUPPLIERS
    ]
    suppliers[-1]["active"] = "false"

    orders = []
    items = []
    item_seq = 1
    for n in range(1, n_orders + 1):
        order_date = PERIOD_START + timedelta(days=rng.randrange(PERIOD_DAYS))
        orders.append(
            {
                "order_id": f"PO-{n:05d}",
                "supplier_id": rng.choice(SUPPLIERS)[0],
                "order_date": order_date.isoformat(),
                "status": rng.choice(STATUSES),
                "total_amount": "0",
                "updated_at": f"{order_date.isoformat()} 09:00:00",
            }
        )
        for _ in range(rng.randint(1, 4)):
            items.append(
                {
                    "item_id": f"IT-{item_seq:06d}",
                    "order_id": f"PO-{n:05d}",
                    "sku": f"SKU-{rng.randint(100, 140)}",
                    "quantity": str(rng.randint(1, 100)),
                    "unit_price": f"{rng.uniform(5, 500):.2f}",
                }
            )
            item_seq += 1

    planted = {k: 0 for k in DEFECT_COUNTS}

    if defects:
        for it in rng.sample(items, DEFECT_COUNTS["negative_quantity"]):
            it["quantity"] = str(-int(it["quantity"]))
            planted["negative_quantity"] += 1

    # total do pedido = soma dos itens (já com a quantidade negativa, se houver)
    by_order: dict[str, float] = {}
    for it in items:
        by_order[it["order_id"]] = by_order.get(it["order_id"], 0.0) + int(
            it["quantity"]
        ) * float(it["unit_price"])
    for o in orders:
        o["total_amount"] = f"{by_order[o['order_id']]:.2f}"

    if defects:
        # amostra única e disjunta, para cada pedido ter no máximo um defeito
        # no cabeçalho e as contagens esperadas serem exatas
        header_kinds = [
            "null_supplier",
            "orphan_supplier",
            "invalid_status",
            "messy_status",
            "total_mismatch",
        ]
        need = sum(DEFECT_COUNTS[k] for k in header_kinds)
        sample = rng.sample(range(len(orders)), need + DEFECT_COUNTS["duplicate_orders"])
        cursor = 0
        for kind in header_kinds:
            for idx in sample[cursor : cursor + DEFECT_COUNTS[kind]]:
                o = orders[idx]
                if kind == "null_supplier":
                    o["supplier_id"] = ""
                elif kind == "orphan_supplier":
                    o["supplier_id"] = "S99"
                elif kind == "invalid_status":
                    o["status"] = "pendente??"
                elif kind == "messy_status":
                    o["status"] = f"  {o['status'].upper()} "
                elif kind == "total_mismatch":
                    o["total_amount"] = f"{float(o['total_amount']) + 10:.2f}"
                planted[kind] += 1
            cursor += DEFECT_COUNTS[kind]

        dup_rows = []
        for idx in sample[cursor:]:
            copy = dict(orders[idx])
            ts = datetime.fromisoformat(copy["updated_at"]) + timedelta(days=1)
            copy["updated_at"] = ts.strftime("%Y-%m-%d %H:%M:%S")
            dup_rows.append(copy)
            planted["duplicate_orders"] += 1
        orders.extend(dup_rows)

    return {"suppliers": suppliers, "orders": orders, "order_items": items}, planted


def write_csvs(tables: dict, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return out
