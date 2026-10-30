from pathlib import Path

import pandas as pd
import pytest
from pandas.errors import MergeError

from load_data import load_merged

ORDER_DATES = ["order_approved_at", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date"]


def write_raw(dir_: Path, products=None):
    """Tiny dataset: 4 item rows, 3 orders, one product with no category."""
    pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3"],
        "order_item_id": [1, 2, 1, 1],
        "product_id": ["p1", "p2", "p3", "p4"],
        "seller_id": ["s1"] * 4,
        "shipping_limit_date": ["2017-01-10 10:00:00"] * 4,
        "price": [10.0, 20.0, 30.0, 40.0],
        "freight_value": [1.0, 2.0, 3.0, 4.0],
    }).to_csv(dir_ / "olist_order_items_dataset.csv", index=False)

    if products is None:
        products = pd.DataFrame({
            "product_id": ["p1", "p2", "p3", "p4"],
            "product_category_name": ["cama_mesa_banho", "beleza_saude", None, "pc_gamer"],
        })
    products.to_csv(dir_ / "olist_products_dataset.csv", index=False)

    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered", "canceled", "delivered"],
        "order_purchase_timestamp": ["2017-01-05 09:00:00", "2017-02-01 09:00:00",
                                     "2017-03-01 09:00:00"],
    })
    for col in ORDER_DATES:
        orders[col] = "2017-03-20 09:00:00"
    orders.to_csv(dir_ / "olist_orders_dataset.csv", index=False)

    # NEW: customers file (u1 = same person, two orders)
    pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u1", "u2"],
        "customer_zip_code_prefix": [1000, 1000, 2000],
        "customer_city": ["a", "a", "b"],
        "customer_state": ["SP", "SP", "RJ"],
    }).to_csv(dir_ / "olist_customers_dataset.csv", index=False)

    pd.DataFrame({
        "product_category_name": ["cama_mesa_banho", "beleza_saude"],
        "product_category_name_english": ["bed_bath_table", "health_beauty"],
    }).to_csv(dir_ / "product_category_name_translation.csv", index=False)


@pytest.fixture
def raw(tmp_path):
    write_raw(tmp_path)
    return tmp_path


def test_returns_dataframe(raw):
    assert isinstance(load_merged(raw), pd.DataFrame)


def test_row_count_equals_item_rows(raw):
    assert len(load_merged(raw)) == 4          # joins must not add or drop rows


def test_expected_columns_present(raw):
    expected = {"order_id", "order_item_id", "product_id", "price", "freight_value",
                "order_status", "order_purchase_timestamp",
                "product_category_name", "product_category_name_english",
                "customer_unique_id"}
    assert expected <= set(load_merged(raw).columns)


def test_grain_is_one_row_per_order_item(raw):
    df = load_merged(raw)
    assert not df.duplicated(subset=["order_id", "order_item_id"]).any()


def test_identifiers_never_missing(raw):
    df = load_merged(raw)
    assert df[["order_id", "product_id", "order_status"]].notna().all().all()


def test_every_item_has_a_category_label(raw):
    df = load_merged(raw).set_index("product_id")
    assert df["product_category_name_english"].notna().all()
    assert df.loc["p3", "product_category_name_english"] == "unknown"   # blank source
    assert df.loc["p4", "product_category_name_english"] == "pc_gamer"  # manual mapping
    assert df.loc["p1", "product_category_name_english"] == "bed_bath_table"


def test_purchase_timestamp_is_datetime(raw):
    assert pd.api.types.is_datetime64_any_dtype(
        load_merged(raw)["order_purchase_timestamp"])


def test_price_totals_preserved(raw):
    assert load_merged(raw)["price"].sum() == pytest.approx(100.0)


def test_duplicate_product_ids_are_rejected(tmp_path):
    dup = pd.DataFrame({
        "product_id": ["p1", "p1", "p2", "p3", "p4"],
        "product_category_name": ["cama_mesa_banho"] * 2 + ["beleza_saude", None, "pc_gamer"],
    })
    write_raw(tmp_path, products=dup)
    with pytest.raises(MergeError):             # a fan-out join must fail loudly
        load_merged(tmp_path)


def test_missing_file_gives_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="olist_order_items_dataset.csv"):
        load_merged(tmp_path)


def test_customer_unique_id_never_missing(raw):
    assert load_merged(raw)["customer_unique_id"].notna().all()


def test_same_person_can_own_several_orders(raw):
    df = load_merged(raw).drop_duplicates("order_id")
    per_person = df.groupby("customer_unique_id")["order_id"].nunique()
    assert per_person["u1"] == 2 and per_person["u2"] == 1


def test_duplicate_customer_ids_are_rejected(tmp_path):
    write_raw(tmp_path)
    pd.DataFrame({
        "customer_id": ["c1", "c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u1", "u1", "u2"],
    }).to_csv(tmp_path / "olist_customers_dataset.csv", index=False)
    with pytest.raises(MergeError):
        load_merged(tmp_path)


# ---- Real data: skipped when the CSVs are not present ----
REAL = Path("data/raw")


@pytest.mark.skipif(not (REAL / "olist_order_items_dataset.csv").exists(),
                    reason="Olist CSVs not in data/raw/")
def test_real_data_matches_verified_figures():
    df = load_merged()
    assert len(df) == 112_650
    assert df["product_category_name_english"].nunique() == 74
    assert (df["product_category_name_english"] == "unknown").sum() == 1_603
    w = df[(df["order_status"] == "delivered")
           & (df["order_purchase_timestamp"] >= "2017-01-01")
           & (df["order_purchase_timestamp"] < "2018-09-01")]
    assert w["price"].sum() == pytest.approx(13_181_027.13, abs=0.005)