from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


MONTHS = ["July", "August", "September", "October", "November", "December"]
MONTH_DAY_COUNTS = {
    "July": 31,
    "August": 31,
    "September": 30,
    "October": 31,
    "November": 30,
    "December": 31,
}
WEEK_BUCKETS = [
    ("Week 1", 1, 7),
    ("Week 2", 8, 14),
    ("Week 3", 15, 21),
    ("Week 4", 22, 28),
    ("Week 5", 29, 31),
]
NUMERIC_INPUTS = [
    "Qty Avail",
    "Total GRNs",
    "Opening Balance",
    "Remaining Available Stock",
    "Demand",
    "Demand Check",
]
GROUP_NUMERIC_COLS = [
    "Qty Avail",
    "Total GRNs",
    "Opening Balance",
    "Remaining Available Stock",
    "Demand",
    "Demand Check",
    "rack_present",
    "box_present",
    "order_flag",
    "okay_flag",
]
ID_COLS = ["Product Size", "Weight Kgs", "Thick MM", "Gauges", "Category"]


@dataclass
class TreeNode:
    prediction: float
    feature_index: Optional[int] = None
    threshold: Optional[float] = None
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None

    @property
    def is_leaf(self) -> bool:
        return self.feature_index is None


class DecisionTreeRegressorScratch:
    def __init__(
        self,
        max_depth: int = 8,
        min_samples_split: int = 6,
        min_samples_leaf: int = 3,
        max_features: Optional[int] = None,
        max_thresholds: int = 12,
        random_state: int = 42,
    ) -> None:
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.max_thresholds = max_thresholds
        self.random_state = random_state
        self._rng = random.Random(random_state)
        self.root: Optional[TreeNode] = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.root = self._build_tree(x, y, depth=0)

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.root is None:
            raise RuntimeError("Tree has not been fitted.")
        return np.array([self._predict_row(row, self.root) for row in x], dtype=float)

    def _predict_row(self, row: np.ndarray, node: TreeNode) -> float:
        while not node.is_leaf:
            if row[node.feature_index] <= node.threshold:
                node = node.left  # type: ignore[assignment]
            else:
                node = node.right  # type: ignore[assignment]
        return node.prediction

    def _build_tree(self, x: np.ndarray, y: np.ndarray, depth: int) -> TreeNode:
        prediction = float(np.mean(y)) if len(y) else 0.0
        node = TreeNode(prediction=prediction)
        if (
            depth >= self.max_depth
            or len(y) < self.min_samples_split
            or np.allclose(y, y[0])
        ):
            return node

        split = self._best_split(x, y)
        if split is None:
            return node

        feature_index, threshold, left_mask = split
        right_mask = ~left_mask
        node.feature_index = feature_index
        node.threshold = threshold
        node.left = self._build_tree(x[left_mask], y[left_mask], depth + 1)
        node.right = self._build_tree(x[right_mask], y[right_mask], depth + 1)
        return node

    def _best_split(
        self, x: np.ndarray, y: np.ndarray
    ) -> Optional[Tuple[int, float, np.ndarray]]:
        n_samples, n_features = x.shape
        feature_count = self.max_features or max(1, int(math.sqrt(n_features)))
        candidate_features = self._rng.sample(range(n_features), k=min(feature_count, n_features))
        parent_sse = self._sse(y)
        best_gain = 0.0
        best_split: Optional[Tuple[int, float, np.ndarray]] = None

        for feature_index in candidate_features:
            feature_values = x[:, feature_index]
            unique_values = np.unique(feature_values)
            if len(unique_values) <= 1:
                continue
            thresholds = self._candidate_thresholds(unique_values)
            for threshold in thresholds:
                left_mask = feature_values <= threshold
                left_count = int(left_mask.sum())
                right_count = n_samples - left_count
                if left_count < self.min_samples_leaf or right_count < self.min_samples_leaf:
                    continue
                left_y = y[left_mask]
                right_y = y[~left_mask]
                child_sse = self._sse(left_y) + self._sse(right_y)
                gain = parent_sse - child_sse
                if gain > best_gain:
                    best_gain = gain
                    best_split = (feature_index, float(threshold), left_mask)
        return best_split

    def _candidate_thresholds(self, unique_values: np.ndarray) -> np.ndarray:
        if len(unique_values) <= self.max_thresholds:
            return (unique_values[:-1] + unique_values[1:]) / 2.0
        quantiles = np.linspace(0.1, 0.9, num=self.max_thresholds)
        sampled = np.unique(np.quantile(unique_values, quantiles))
        if len(sampled) <= 1:
            return sampled
        return sampled

    @staticmethod
    def _sse(values: np.ndarray) -> float:
        if len(values) == 0:
            return 0.0
        mean = float(np.mean(values))
        return float(np.sum((values - mean) ** 2))


class RandomForestRegressorScratch:
    def __init__(
        self,
        n_estimators: int = 80,
        max_depth: int = 8,
        min_samples_split: int = 6,
        min_samples_leaf: int = 3,
        max_features: Optional[int] = None,
        max_thresholds: int = 12,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.max_thresholds = max_thresholds
        self.random_state = random_state
        self.trees: List[DecisionTreeRegressorScratch] = []

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.trees = []
        rng = np.random.default_rng(self.random_state)
        sample_count = len(x)
        for tree_index in range(self.n_estimators):
            bootstrap_idx = rng.choice(sample_count, size=sample_count, replace=True)
            tree = DecisionTreeRegressorScratch(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features=self.max_features,
                max_thresholds=self.max_thresholds,
                random_state=self.random_state + tree_index,
            )
            tree.fit(x[bootstrap_idx], y[bootstrap_idx])
            self.trees.append(tree)

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not self.trees:
            raise RuntimeError("Forest has not been fitted.")
        predictions = np.vstack([tree.predict(x) for tree in self.trees])
        return predictions.mean(axis=0)


def load_monthly_workbook(excel_path: Path) -> pd.DataFrame:
    monthly_frames: List[pd.DataFrame] = []
    for month_index, month_name in enumerate(MONTHS, start=1):
        sheet_df = pd.read_excel(excel_path, sheet_name=month_name, header=2)
        sheet_df.columns = [
            "Product Size",
            "Weight Kgs",
            "Thick MM",
            "Gauges",
            "Category",
            "Rack No.",
            "Box No.",
            "Qty Avail",
            "Order/Okay",
            "Total GRNs",
            "Opening Balance",
            "Remaining Available Stock",
            "Demand",
            "Demand Check",
            "Source Row",
        ]

        sheet_df = sheet_df.dropna(how="all").copy()
        invalid_rows = (
            sheet_df.iloc[:, 0].astype(str).str.strip().isin({"Product Size", "Total"})
        )
        sheet_df = sheet_df.loc[~invalid_rows].copy()
        for col in ID_COLS:
            sheet_df[col] = sheet_df[col].fillna("Unknown").astype(str).str.strip()
        sheet_df["Rack No."] = sheet_df["Rack No."].astype(str).replace("nan", "")
        sheet_df["Box No."] = sheet_df["Box No."].astype(str).replace("nan", "")
        order_okay = sheet_df["Order/Okay"].fillna("").astype(str).str.strip().str.lower()
        sheet_df["order_flag"] = (order_okay == "order").astype(int)
        sheet_df["okay_flag"] = (order_okay == "okay").astype(int)
        sheet_df["rack_present"] = (sheet_df["Rack No."] != "").astype(int)
        sheet_df["box_present"] = (sheet_df["Box No."] != "").astype(int)
        for col in NUMERIC_INPUTS:
            sheet_df[col] = pd.to_numeric(sheet_df[col], errors="coerce").fillna(0.0)

        sheet_df["month_name"] = month_name
        sheet_df["month_index"] = month_index
        monthly_frames.append(sheet_df)

    full_df = pd.concat(monthly_frames, ignore_index=True)
    aggregated = (
        full_df.groupby(ID_COLS + ["month_name", "month_index"], as_index=False)[GROUP_NUMERIC_COLS]
        .sum()
        .sort_values(["Product Size", "Weight Kgs", "Thick MM", "Gauges", "Category", "month_index"])
        .reset_index(drop=True)
    )

    variant_catalog = aggregated[ID_COLS].drop_duplicates().reset_index(drop=True)
    month_frame = pd.DataFrame(
        {"month_name": MONTHS, "month_index": list(range(1, len(MONTHS) + 1))}
    )
    full_grid = variant_catalog.merge(month_frame, how="cross")
    modeled = full_grid.merge(
        aggregated,
        how="left",
        on=ID_COLS + ["month_name", "month_index"],
    )
    fill_cols = GROUP_NUMERIC_COLS
    modeled[fill_cols] = modeled[fill_cols].fillna(0.0)
    modeled["variant_id"] = modeled[ID_COLS].agg("|".join, axis=1)
    modeled = modeled.sort_values(["variant_id", "month_index"]).reset_index(drop=True)
    return modeled


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    grouped = result.groupby("variant_id", group_keys=False)
    result["lag_1_demand"] = grouped["Demand"].shift(1).fillna(0.0)
    result["lag_2_demand"] = grouped["Demand"].shift(2).fillna(0.0)
    result["lag_3_demand"] = grouped["Demand"].shift(3).fillna(0.0)
    result["rolling_mean_2"] = (
        grouped["Demand"].shift(1).rolling(window=2, min_periods=1).mean().reset_index(level=0, drop=True)
    ).fillna(0.0)
    result["rolling_mean_3"] = (
        grouped["Demand"].shift(1).rolling(window=3, min_periods=1).mean().reset_index(level=0, drop=True)
    ).fillna(0.0)
    result["rolling_std_3"] = (
        grouped["Demand"].shift(1).rolling(window=3, min_periods=2).std().reset_index(level=0, drop=True)
    ).fillna(0.0)
    result["demand_change_1"] = result["lag_1_demand"] - result["lag_2_demand"]
    result["grn_to_stock_ratio"] = np.where(
        result["Remaining Available Stock"] > 0,
        result["Total GRNs"] / result["Remaining Available Stock"],
        0.0,
    )
    result["opening_to_qty_ratio"] = np.where(
        result["Qty Avail"] > 0,
        result["Opening Balance"] / result["Qty Avail"],
        0.0,
    )
    result["month_sin"] = np.sin(2.0 * np.pi * result["month_index"] / 12.0)
    result["month_cos"] = np.cos(2.0 * np.pi * result["month_index"] / 12.0)
    return result


def encode_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    encoded = df.copy()
    encoders: Dict[str, Dict[str, int]] = {}
    for col in ID_COLS:
        values = sorted(encoded[col].fillna("Unknown").astype(str).unique())
        mapping = {value: idx for idx, value in enumerate(values)}
        encoded[f"{col}_code"] = encoded[col].map(mapping).astype(int)
        encoders[col] = mapping
    return encoded, encoders


def prepare_model_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    modeled = add_time_features(df)
    modeled, _ = encode_features(modeled)
    feature_cols = [
        "month_index",
        "month_sin",
        "month_cos",
        "Qty Avail",
        "Total GRNs",
        "Opening Balance",
        "Remaining Available Stock",
        "Demand Check",
        "rack_present",
        "box_present",
        "order_flag",
        "okay_flag",
        "lag_1_demand",
        "lag_2_demand",
        "lag_3_demand",
        "rolling_mean_2",
        "rolling_mean_3",
        "rolling_std_3",
        "demand_change_1",
        "grn_to_stock_ratio",
        "opening_to_qty_ratio",
        "Product Size_code",
        "Weight Kgs_code",
        "Thick MM_code",
        "Gauges_code",
        "Category_code",
    ]
    return modeled, feature_cols


def score_predictions(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(actual - predicted)))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    total_variance = float(np.sum((actual - np.mean(actual)) ** 2))
    residual_variance = float(np.sum((actual - predicted) ** 2))
    r2 = 1.0 - residual_variance / total_variance if total_variance else 0.0
    return {"mae": mae, "rmse": rmse, "r2": r2}


def train_forest(train_df: pd.DataFrame, feature_cols: List[str]) -> RandomForestRegressorScratch:
    x_train = train_df[feature_cols].to_numpy(dtype=float)
    y_train = train_df["Demand"].to_numpy(dtype=float)
    forest = RandomForestRegressorScratch(
        n_estimators=90,
        max_depth=9,
        min_samples_split=8,
        min_samples_leaf=3,
        max_features=max(2, int(math.sqrt(len(feature_cols)))),
        max_thresholds=10,
        random_state=42,
    )
    forest.fit(x_train, y_train)
    return forest


def predict_all_months(modeled_df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, float]]:
    prediction_parts: List[pd.DataFrame] = []
    for month_name in MONTHS:
        train_df = modeled_df.loc[modeled_df["month_name"] != month_name].copy()
        test_df = modeled_df.loc[modeled_df["month_name"] == month_name].copy()
        forest = train_forest(train_df, feature_cols)
        predicted = forest.predict(test_df[feature_cols].to_numpy(dtype=float))
        test_df["predicted_monthly_demand"] = np.maximum(predicted, 0.0)
        prediction_parts.append(test_df)

    predictions_df = pd.concat(prediction_parts, ignore_index=True)
    metrics = score_predictions(
        predictions_df["Demand"].to_numpy(dtype=float),
        predictions_df["predicted_monthly_demand"].to_numpy(dtype=float),
    )
    return predictions_df, metrics


def expand_to_weekly(predictions_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for _, row in predictions_df.iterrows():
        monthly_prediction = float(max(row["predicted_monthly_demand"], 0.0))
        month_name = str(row["month_name"])
        total_days = MONTH_DAY_COUNTS[month_name]
        for week_label, start_day, end_day in WEEK_BUCKETS:
            if start_day > total_days:
                continue
            effective_end_day = min(end_day, total_days)
            day_count = effective_end_day - start_day + 1
            weekly_prediction = monthly_prediction * day_count / total_days
            output_row: Dict[str, object] = {col: row[col] for col in ID_COLS}
            output_row.update(
                {
                    "forecast_month": month_name,
                    "week_label": week_label,
                    "week_start_day": start_day,
                    "week_end_day": effective_end_day,
                    "weekly_share": round(day_count / total_days, 6),
                    "predicted_weekly_demand": round(weekly_prediction, 3),
                    "predicted_monthly_demand": round(monthly_prediction, 3),
                    "allocation_basis": "calendar_day_share",
                }
            )
            rows.append(output_row)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Forecast next-month demand from monthly Excel demand data and export weekly predictions."
    )
    parser.add_argument(
        "--input",
        default=r"D:\predicting_demand\monthly_demand_report.xlsx",
        help="Path to the monthly demand Excel workbook.",
    )
    parser.add_argument(
        "--output",
        default="final.csv",
        help="Path for the exported weekly prediction CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent
    excel_path = Path(args.input)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    monthly_df = load_monthly_workbook(excel_path)
    modeled_df, feature_cols = prepare_model_data(monthly_df)

    monthly_predictions, metrics = predict_all_months(modeled_df, feature_cols)
    final_df = expand_to_weekly(monthly_predictions[ID_COLS + ["month_name", "predicted_monthly_demand"]])
    final_df.to_csv(output_path, index=False)

    total_monthly_forecast = float(monthly_predictions["predicted_monthly_demand"].sum())
    print(f"Saved weekly demand forecast to: {output_path}")
    print(
        "Validation metrics across July-December out-of-fold predictions -> "
        f"MAE: {metrics['mae']:.3f}, RMSE: {metrics['rmse']:.3f}, R2: {metrics['r2']:.3f}"
    )
    print(f"Predicted total demand across {MONTHS[0]}-{MONTHS[-1]}: {total_monthly_forecast:.3f}")
    print(
        "Weekly output assumption: each predicted monthly demand value is split into week-of-month buckets "
        "based on the number of calendar days in each bucket."
    )


if __name__ == "__main__":
    main()
