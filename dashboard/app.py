"""
Streamlit Web Application: Dynamic Pricing & Promotion Simulation Dashboard.
Provides:
- Executive KPIs and pricing metrics
- Interactive price decision explorer & real-time simulation sandbox
- Historical pricing & competitor benchmark visualizer
- Promotions & stacking rule governance
- Edge-case anomaly & exception inspection
- System validation audit report
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(
    page_title="Dynamic Pricing & Promotion Simulator",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pricing_simulation.db")
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "..", "ground_truth", "ground_truth_anomalies.csv")


@st.cache_resource
def get_connection():
    if not os.path.exists(DB_PATH):
        st.error(f"Database file not found at {DB_PATH}. Please run `python main.py --mode starter` first.")
        st.stop()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def load_table(table_name: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


# Custom CSS Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .badge-approved {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-flagged {
        background-color: #fff3e0;
        color: #ef6c00;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-rejected {
        background-color: #ffebee;
        color: #c62828;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🏷️ Pricing Simulator")
st.sidebar.caption("YottaFlex AI Project | Seed: 20261022")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive KPIs & Summary",
        "💡 Price Recommendations & History",
        "🧪 Interactive Pricing Sandbox",
        "🎟️ Promotions & Stacking Rules",
        "⚠️ Exceptions & Edge-Case Audit",
        "✅ Validation & Benchmark Report"
    ]
)

# -------------------------------------------------------------
# 1. EXECUTIVE KPIS & SUMMARY
# -------------------------------------------------------------
if nav_choice == "📊 Executive KPIs & Summary":
    st.title("📊 Executive Pricing & Margins Dashboard")
    st.markdown("High-level performance indicators, margin health, and pricing decision distributions.")

    df_decisions = load_table("price_decisions")
    df_products = load_table("products")

    total_skus = len(df_products)
    total_decisions = len(df_decisions)
    normal_decisions = df_decisions[df_decisions["is_anomaly"] == 0]
    avg_margin = normal_decisions["expected_margin_rate"].mean() * 100
    approved_cnt = len(df_decisions[df_decisions["decision_status"] == "APPROVED"])
    flagged_cnt = len(df_decisions[df_decisions["decision_status"] == "FLAGGED"])
    anomaly_cnt = len(df_decisions[df_decisions["is_anomaly"] == 1])

    # Top KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Active Catalog SKUs", f"{total_skus:,}")
    col2.metric("Total Decisions Evaluated", f"{total_decisions:,}")
    col3.metric("Average Gross Margin", f"{avg_margin:.2f}%")
    col4.metric("Approved Decisions", f"{approved_cnt:,}")
    col5.metric("Flagged / Anomalies", f"{flagged_cnt + anomaly_cnt:,}")

    st.markdown("---")

    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("Price Decision Status Distribution")
        fig_status = px.pie(
            df_decisions,
            names="decision_status",
            title="Decisions by Status",
            color="decision_status",
            color_discrete_map={"APPROVED": "#2e7d32", "FLAGGED": "#ef6c00", "REJECTED": "#c62828"},
            hole=0.45
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with c_right:
        st.subheader("Pricing Rules Applied")
        rule_counts = df_decisions["pricing_rule_applied"].value_counts().reset_index()
        rule_counts.columns = ["Pricing Rule", "Count"]
        fig_rules = px.bar(
            rule_counts,
            x="Count",
            y="Pricing Rule",
            orientation="h",
            color="Count",
            color_continuous_scale="Blues",
            title="Frequency of Applied Pricing Rules"
        )
        st.plotly_chart(fig_rules, use_container_width=True)

    st.subheader("Gross Margin Distribution Across Catalog")
    fig_hist = px.histogram(
        normal_decisions,
        x="expected_margin_rate",
        nbins=25,
        title="Distribution of Expected Gross Margin Rate (Normal Decisions)",
        labels={"expected_margin_rate": "Gross Margin Rate"},
        color_discrete_sequence=["#1E88E5"]
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# -------------------------------------------------------------
# 2. PRICE RECOMMENDATIONS & HISTORY
# -------------------------------------------------------------
elif nav_choice == "💡 Price Recommendations & History":
    st.title("💡 Price Recommendations & Historical Trends")

    df_decisions = load_table("price_decisions")
    df_products = load_table("products")
    df_merged = df_decisions.merge(df_products[["sku", "name", "category", "brand", "min_margin_rate", "price_floor", "price_ceiling"]], on="sku")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    categories = ["ALL"] + sorted(df_merged["category"].unique().tolist())
    selected_cat = col_f1.selectbox("Filter Category", categories)

    statuses = ["ALL"] + sorted(df_merged["decision_status"].unique().tolist())
    selected_status = col_f2.selectbox("Filter Status", statuses)

    search_query = col_f3.text_input("Search SKU or Name", "")

    filtered_df = df_merged.copy()
    if selected_cat != "ALL":
        filtered_df = filtered_df[filtered_df["category"] == selected_cat]
    if selected_status != "ALL":
        filtered_df = filtered_df[filtered_df["decision_status"] == selected_status]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["sku"].str.contains(search_query, case=False) |
            filtered_df["name"].str.contains(search_query, case=False)
        ]

    st.dataframe(
        filtered_df[[
            "decision_id", "sku", "name", "category", "input_cost", "current_price",
            "final_price", "expected_margin_rate", "pricing_rule_applied", "decision_status"
        ]],
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("SKU Deep Dive & Traceability")

    sku_list = filtered_df["sku"].unique().tolist()
    if sku_list:
        selected_sku = st.selectbox("Select SKU for Detailed Audit Log", sku_list)
        sku_decision = df_merged[df_merged["sku"] == selected_sku].iloc[0]

        d_col1, d_col2 = st.columns([1, 2])
        with d_col1:
            st.markdown(f"### `{sku_decision['sku']}`")
            st.markdown(f"**Title:** {sku_decision['name']}")
            st.markdown(f"**Category:** {sku_decision['category']} | **Brand:** {sku_decision['brand']}")
            st.markdown(f"**Unit Cost:** ₹{sku_decision['input_cost']:,.2f}")
            st.markdown(f"**Current Price:** ₹{sku_decision['current_price']:,.2f}")
            st.markdown(f"**Recommended Final Price:** ₹{sku_decision['final_price']:,.2f}")
            st.markdown(f"**Expected Margin:** {sku_decision['expected_margin_rate']*100:.2f}% (Min: {sku_decision['min_margin_rate']*100:.1f}%)")
            st.markdown(f"**Decision Status:** `{sku_decision['decision_status']}`")

        with d_col2:
            st.markdown("### Decision Explainability Trail")
            st.info(sku_decision["decision_reason"])

            # Historical Chart
            conn = get_connection()
            df_price_hist = pd.read_sql_query(
                "SELECT effective_start_date, base_price FROM price_history WHERE sku = ? ORDER BY effective_start_date;",
                conn, params=(selected_sku,)
            )
            df_comp_hist = pd.read_sql_query(
                "SELECT observation_time, observed_price, competitor_name FROM competitor_observations WHERE sku = ? ORDER BY observation_time;",
                conn, params=(selected_sku,)
            )

            fig_sku = go.Figure()
            if not df_price_hist.empty:
                fig_sku.add_trace(go.Scatter(
                    x=df_price_hist["effective_start_date"],
                    y=df_price_hist["base_price"],
                    mode="lines+markers",
                    name="Our Base Price",
                    line=dict(color="#1E88E5", width=3)
                ))
            if not df_comp_hist.empty:
                fig_sku.add_trace(go.Scatter(
                    x=df_comp_hist["observation_time"].str[:10],
                    y=df_comp_hist["observed_price"],
                    mode="markers",
                    name="Competitor Price",
                    marker=dict(color="#E53935", size=8, symbol="diamond")
                ))

            fig_sku.update_layout(
                title=f"Price History & Competitor Intelligence ({selected_sku})",
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                height=350
            )
            st.plotly_chart(fig_sku, use_container_width=True)

# -------------------------------------------------------------
# 3. INTERACTIVE PRICING SANDBOX
# -------------------------------------------------------------
elif nav_choice == "🧪 Interactive Pricing Sandbox":
    st.title("🧪 Interactive Dynamic Pricing Sandbox")
    st.markdown("Test the pricing engine with custom inputs in real time to observe automated rule selection and margin guardrail enforcement.")

    from src.pricing_engine import PricingEngine, ProductProfile, CompetitorData, StockData, DemandData, PromotionCandidate

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Product & Financial Inputs")
        sim_cost = st.number_input("Unit Cost (₹)", min_value=10.0, max_value=200000.0, value=1000.0, step=50.0)
        sim_margin = st.slider("Minimum Required Margin (%)", min_value=5.0, max_value=50.0, value=20.0, step=1.0) / 100.0
        sim_current_price = st.number_input("Current Selling Price (₹)", min_value=10.0, max_value=300000.0, value=1400.0, step=50.0)
        sim_floor = st.number_input("Product Floor Guardrail (₹)", min_value=10.0, max_value=200000.0, value=1100.0, step=50.0)
        sim_ceiling = st.number_input("Product Ceiling Guardrail (₹)", min_value=sim_floor, max_value=500000.0, value=2500.0, step=50.0)

    with c2:
        st.subheader("Market & Operational Signals")
        sim_comp_price = st.number_input("Competitor Scraped Price (₹)", min_value=0.0, max_value=300000.0, value=1300.0, step=50.0)
        sim_comp_fresh = st.selectbox("Competitor Data Freshness", ["CURRENT (2 days old)", "STALE (18 days old)", "UNAVAILABLE"])
        sim_stock = st.slider("Available Stock Units", min_value=0, max_value=300, value=45)
        sim_demand = st.select_slider("Customer Demand Signal", options=["LOW", "MEDIUM", "HIGH"], value="MEDIUM")

        apply_promo = st.checkbox("Include Active Promotion?")
        promo_cand = []
        if apply_promo:
            p_discount = st.slider("Promotion Discount Rate (%)", min_value=5, max_value=40, value=10) / 100.0
            promo_cand.append(PromotionCandidate(
                promotion_id="SANDBOX-PROMO-01",
                promo_code="SANDBOX10",
                discount_type="PERCENTAGE",
                discount_value=p_discount,
                rule_type="EXCLUSIVE",
                priority_order=1
            ))

    # Run Pricing Engine
    engine = PricingEngine(freshness_threshold_days=7)
    profile = ProductProfile(
        sku="SKU-SANDBOX", name="Sandbox Test Item", category="Electronics", brand="TestBrand",
        base_cost=sim_cost, min_margin_rate=sim_margin, price_floor=sim_floor, price_ceiling=sim_ceiling, lifecycle_status="ACTIVE"
    )

    if "CURRENT" in sim_comp_fresh:
        c_data = CompetitorData(benchmark_price=sim_comp_price, freshness_status="CURRENT", days_old=2)
    elif "STALE" in sim_comp_fresh:
        c_data = CompetitorData(benchmark_price=sim_comp_price, freshness_status="STALE", days_old=18)
    else:
        c_data = CompetitorData(benchmark_price=None, freshness_status="UNAVAILABLE", days_old=None)

    stock_data, _ = engine.evaluate_signals(sim_stock, 20, 0)
    demand_data = DemandData(recent_order_count=10 if sim_demand == "HIGH" else (1 if sim_demand == "LOW" else 5), demand_signal=sim_demand)

    decision = engine.decide_price(
        product=profile,
        current_price=sim_current_price,
        unit_cost=sim_cost,
        competitor_data=c_data,
        stock_data=stock_data,
        demand_data=demand_data,
        promotions=promo_cand,
        decision_date="2026-01-20",
        decision_id="DEC-SANDBOX-001"
    )

    st.markdown("---")
    st.subheader("💡 Pricing Engine Decision Output")

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Proposed Candidate Price", f"₹{decision.proposed_price:,.2f}")
    o2.metric("Final Recommended Price", f"₹{decision.final_price:,.2f}")
    o3.metric("Expected Gross Margin", f"{decision.expected_margin_rate*100:.2f}%")
    o4.metric("Rule Applied", decision.pricing_rule_applied)

    st.markdown("#### Audit & Explainability Explanation")
    st.success(decision.decision_reason)

# -------------------------------------------------------------
# 4. PROMOTIONS & STACKING RULES
# -------------------------------------------------------------
elif nav_choice == "🎟️ Promotions & Stacking Rules":
    st.title("🎟️ Promotions & Stacking Rules Governance")
    st.markdown("Manage marketing promotions, discount structures, eligibility mappings, and stacking/exclusivity rules.")

    df_promos = load_table("promotions")
    df_rules = load_table("promotion_rules")
    df_bridge = load_table("promotion_products")

    df_promo_full = df_promos.merge(df_rules, on="promotion_id", how="left")

    st.dataframe(
        df_promo_full[[
            "promotion_id", "promo_code", "discount_type", "discount_value",
            "start_date", "end_date", "status", "rule_type", "priority_order", "max_discount_cap"
        ]],
        use_container_width=True
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("Promotions by Rule Type")
        fig_r = px.pie(df_rules, names="rule_type", title="Stacking Rule Distribution", hole=0.4)
        st.plotly_chart(fig_r, use_container_width=True)

    with col_p2:
        st.subheader("Promotions by Status")
        fig_ps = px.bar(df_promos["status"].value_counts().reset_index(), x="status", y="count", color="status")
        st.plotly_chart(fig_ps, use_container_width=True)

# -------------------------------------------------------------
# 5. EXCEPTIONS & EDGE-CASE AUDIT
# -------------------------------------------------------------
elif nav_choice == "⚠️ Exceptions & Edge-Case Audit":
    st.title("⚠️ Exceptions & Edge-Case Audit Center")
    st.markdown("Audit trail of labelled edge cases and system exceptions, independently benchmarked against isolated ground truth.")

    if os.path.exists(GROUND_TRUTH_PATH):
        df_gt = pd.read_csv(GROUND_TRUTH_PATH)
        df_decisions = load_table("price_decisions")
        df_anomalies = df_decisions[df_decisions["is_anomaly"] == 1].merge(df_gt, on="decision_id")

        st.subheader("Injected & Audited Edge Cases")
        st.dataframe(
            df_anomalies[[
                "decision_id", "sku_x", "issue_type", "expected_label",
                "final_price", "expected_margin_rate", "decision_reason", "injected_details"
            ]],
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Edge Case Deep Dive")

        for _, row in df_anomalies.iterrows():
            with st.expander(f"📌 {row['decision_id']} — {row['issue_type']} ({row['expected_label']})"):
                st.markdown(f"**SKU:** `{row['sku_x']}`")
                st.markdown(f"**Issue Description:** {row['injected_details']}")
                st.markdown(f"**Decision Status:** `{row['decision_status']}`")
                st.markdown(f"**Recorded Final Price:** ₹{row['final_price']:,.2f} | **Expected Margin:** {row['expected_margin_rate']*100:.2f}%")
                st.markdown(f"**Decision Reason:** {row['decision_reason']}")
    else:
        st.warning("Ground truth file not found. Run `python main.py` to generate edge cases.")

# -------------------------------------------------------------
# 6. VALIDATION & BENCHMARK REPORT
# -------------------------------------------------------------
elif nav_choice == "✅ Validation & Benchmark Report":
    st.title("✅ System Validation & Benchmark Report")

    report_path = os.path.join(os.path.dirname(__file__), "..", "validation_report.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
        st.markdown(report_text)
    else:
        st.warning("Validation report not found. Please run `python main.py` first.")
