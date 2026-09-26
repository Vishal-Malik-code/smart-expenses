"""Streamlit UI. Each page is one function; all database work goes through db.py."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db


def show_table(df):
    st.dataframe(df.assign(date=df["date"].dt.date), width="stretch", hide_index=True)


# ---- Pages -------------------------------------------------------------------

def add_page():
    st.subheader("Add an expense")
    with st.form("add", clear_on_submit=True):
        left, right = st.columns(2)
        day = left.date_input("Date", value=date.today())
        amount = left.number_input("Amount", min_value=0.0, step=10.0)
        category = right.selectbox("Category", db.CATEGORIES)
        description = right.text_input("Description")

        if st.form_submit_button("Save"):
            if amount > 0:
                db.add_expense(day, amount, category, description.strip())
                st.success("Expense saved.")
            else:
                st.error("Amount must be greater than zero.")

    st.markdown("#### Recent expenses")
    show_table(db.get_expenses().head(10))


def edit_page():
    st.subheader("Edit or delete an expense")
    expenses = db.get_expenses()
    if expenses.empty:
        st.info("Nothing to edit yet.")
        return

    # Map each expense id to a readable label for the dropdown.
    labels = {
        e.id: f"#{e.id} · {e.date:%d %b %Y} · {e.category} · ₹{e.amount:,.0f} · {e.description}"
        for e in expenses.itertuples()
    }
    expense_id = st.selectbox("Pick an expense", list(labels), format_func=labels.get)
    current = db.get_expense(expense_id)

    # Widget keys include the id so the fields reset when a different expense is picked.
    categories = list(dict.fromkeys(db.CATEGORIES + [current["category"]]))
    left, right = st.columns(2)
    day = left.date_input("Date", date.fromisoformat(current["date"]), key=f"day{expense_id}")
    amount = left.number_input("Amount", 0.0, value=current["amount"], key=f"amt{expense_id}")
    category = right.selectbox(
        "Category", categories, categories.index(current["category"]), key=f"cat{expense_id}"
    )
    description = right.text_input("Description", current["description"], key=f"desc{expense_id}")

    update_col, delete_col, _ = st.columns([1, 1, 4])
    if update_col.button("Update", type="primary"):
        db.update_expense(expense_id, day, amount, category, description.strip())
        st.rerun()
    if delete_col.button("Delete"):
        db.delete_expense(expense_id)
        st.rerun()


def filter_page():
    st.subheader("Filter expenses")
    c1, c2, c3 = st.columns(3)
    start = c1.date_input("From", date.today() - timedelta(days=30))
    end = c2.date_input("To", date.today())
    categories = c3.multiselect("Categories", db.CATEGORIES, default=db.CATEGORIES)

    result = db.get_expenses(start, end, categories)
    st.caption(f"{len(result)} expenses · total ₹{result['amount'].sum():,.0f}")
    show_table(result)


def insights_page():
    st.subheader("Insights")
    by_category = db.category_totals()
    if by_category.empty:
        st.info("Add some expenses to see insights.")
        return

    def last_days(n):
        return db.total_between(date.today() - timedelta(days=n), date.today())

    top = by_category.iloc[0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Top category", top["category"], f"₹{top['total']:,.0f}", delta_color="off")
    m2.metric("Avg per active day", f"₹{db.daily_average():,.0f}")
    m3.metric("Last 7 days", f"₹{last_days(7):,.0f}")
    m4.metric("Last 30 days", f"₹{last_days(30):,.0f}")

    share = top["total"] / by_category["total"].sum()
    if share > 0.4:
        st.warning(f"{top['category']} makes up {share:.0%} of all spending.")

    left, right = st.columns(2)
    left.markdown("#### By category")
    left.bar_chart(by_category.set_index("category"))
    right.markdown("#### By month")
    right.line_chart(db.monthly_totals().set_index("month"))


def budget_page():
    st.subheader("Monthly budget")
    budget = st.number_input("Budget (₹)", min_value=0.0, value=db.get_budget(), step=500.0)
    if st.button("Save budget"):
        db.set_budget(budget)
        st.success("Budget saved.")

    today = date.today()
    spent = db.total_between(today.replace(day=1), today)  # from the 1st of this month
    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", f"₹{budget:,.0f}")
    c2.metric("Spent this month", f"₹{spent:,.0f}")
    c3.metric("Remaining", f"₹{budget - spent:,.0f}")

    if budget > 0:
        st.progress(min(spent / budget, 1.0))
    if spent > budget > 0:
        st.error("You're over budget this month.")


def import_export_page():
    st.subheader("Import / Export")

    st.markdown("#### Import CSV")
    st.caption("Required columns: Date, Amount, Category, Description")
    upload = st.file_uploader("CSV file", type="csv")
    if upload and st.button("Import"):
        try:
            data = pd.read_csv(upload)
            data.columns = data.columns.str.strip().str.title()
            data["Date"] = pd.to_datetime(data["Date"]).dt.strftime("%Y-%m-%d")
            data["Amount"] = data["Amount"].astype(float)
            data["Description"] = data["Description"].fillna("")
            db.add_many(data[["Date", "Amount", "Category", "Description"]].values.tolist())
            st.success(f"Imported {len(data)} rows.")
        except Exception as error:
            st.error(f"Could not import file: {error}")

    st.markdown("#### Export")
    st.download_button("Download CSV", db.get_expenses().to_csv(index=False), "expenses.csv", "text/csv")


# ---- App shell ---------------------------------------------------------------

PAGES = {
    "Add": add_page,
    "Edit / Delete": edit_page,
    "Filter": filter_page,
    "Insights": insights_page,
    "Budget": budget_page,
    "Import / Export": import_export_page,
}

st.set_page_config(page_title="Smart Expenses", page_icon="💸", layout="wide")
db.init_db()

st.sidebar.title("Smart Expenses")
choice = st.sidebar.radio("Go to", list(PAGES))
st.title("Expense Tracker")
PAGES[choice]()
