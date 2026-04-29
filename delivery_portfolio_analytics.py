import pandas as pd
from pathlib import Path

DATA_FILE = "synthetic_delivery_portfolio_data.csv"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["reporting_month"] = pd.to_datetime(df["reporting_month"], errors="coerce")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    required_fields = [
        "client_name", "project_name", "workstream", "delivery_item_id",
        "item_type", "status", "severity", "sla_target_hours", "actual_resolution_hours"
    ]

    clean = df.dropna(subset=required_fields).copy()
    clean = clean[clean["sla_target_hours"] > 0]
    clean = clean[clean["actual_resolution_hours"] >= 0]

    return clean


def add_delivery_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["sla_breach_flag"] = (
        df["actual_resolution_hours"] > df["sla_target_hours"]
    ).astype(int)

    df["open_backlog_flag"] = df["status"].isin(["Open", "In Progress", "Blocked"]).astype(int)

    df["high_severity_flag"] = df["severity"].isin(["Critical", "High"]).astype(int)

    df["risk_score"] = (
        df["sla_breach_flag"] * 30
        + df["open_backlog_flag"] * 25
        + df["high_severity_flag"] * 25
        + (df["blocked_flag"] * 20)
    )

    return df


def create_portfolio_health_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["client_name", "project_name", "workstream"], as_index=False)
        .agg(
            total_items=("delivery_item_id", "nunique"),
            open_backlog=("open_backlog_flag", "sum"),
            sla_breaches=("sla_breach_flag", "sum"),
            high_severity_items=("high_severity_flag", "sum"),
            avg_resolution_hours=("actual_resolution_hours", "mean"),
            avg_risk_score=("risk_score", "mean"),
            avg_sprint_throughput=("sprint_throughput", "mean")
        )
    )

    summary["sla_breach_rate"] = (
        summary["sla_breaches"] / summary["total_items"]
    ).round(3)

    summary["avg_resolution_hours"] = summary["avg_resolution_hours"].round(1)
    summary["avg_risk_score"] = summary["avg_risk_score"].round(1)
    summary["avg_sprint_throughput"] = summary["avg_sprint_throughput"].round(1)

    summary["health_status"] = summary["avg_risk_score"].apply(
        lambda x: "High Risk" if x >= 55 else ("Watchlist" if x >= 30 else "Healthy")
    )

    return summary.sort_values(by=["avg_risk_score", "sla_breach_rate"], ascending=[False, False])


def create_sla_breach_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["client_name", "item_type", "root_cause"], as_index=False)
        .agg(
            total_items=("delivery_item_id", "nunique"),
            sla_breaches=("sla_breach_flag", "sum"),
            avg_resolution_hours=("actual_resolution_hours", "mean")
        )
    )

    summary["sla_breach_rate"] = (
        summary["sla_breaches"] / summary["total_items"]
    ).round(3)

    summary["avg_resolution_hours"] = summary["avg_resolution_hours"].round(1)

    return summary.sort_values(by=["sla_breach_rate", "sla_breaches"], ascending=[False, False])


def create_at_risk_items(df: pd.DataFrame) -> pd.DataFrame:
    at_risk = df[df["risk_score"] >= 55].copy()

    columns = [
        "delivery_item_id", "client_name", "project_name", "workstream",
        "item_type", "status", "severity", "root_cause",
        "sla_target_hours", "actual_resolution_hours", "risk_score",
        "recommended_action"
    ]

    return at_risk[columns].sort_values(
        by=["risk_score", "actual_resolution_hours"],
        ascending=[False, False]
    )


def main():
    df = load_data(DATA_FILE)
    df = clean_data(df)
    df = add_delivery_metrics(df)

    portfolio_summary = create_portfolio_health_summary(df)
    sla_summary = create_sla_breach_summary(df)
    at_risk_items = create_at_risk_items(df)

    df.to_csv(OUTPUT_DIR / "clean_delivery_portfolio_data.csv", index=False)
    portfolio_summary.to_csv(OUTPUT_DIR / "portfolio_health_summary.csv", index=False)
    sla_summary.to_csv(OUTPUT_DIR / "sla_breach_summary.csv", index=False)
    at_risk_items.to_csv(OUTPUT_DIR / "at_risk_delivery_items.csv", index=False)

    print("Delivery portfolio analytics pipeline completed successfully.")
    print(f"Delivery items analyzed: {len(df)}")
    print(f"At-risk items identified: {len(at_risk_items)}")


if __name__ == "__main__":
    main()
