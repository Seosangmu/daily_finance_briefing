from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd
from jinja2 import Template


@dataclass(frozen=True)
class MarketItem:
    category: str
    label: str
    symbol: str


ITEMS = [
    MarketItem("국내", "코스피", "KS11"),
    MarketItem("국내", "코스닥", "KQ11"),
    MarketItem("해외", "다우 산업", "DJI"),
    MarketItem("해외", "나스닥 종합", "IXIC"),
    MarketItem("해외", "상해 종합", "SSEC"),
    MarketItem("해외", "니케이225", "N225"),
    MarketItem("환율", "원달러", "USD/KRW"),
    MarketItem("환율", "중국 위안달러", "USD/CNY"),
    MarketItem("상품", "금", "GC=F"),
    MarketItem("상품", "은", "SI=F"),
    MarketItem("상품", "WTI", "CL=F"),
]

TEMPLATE = Template(
    """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>{{ title }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 760px; margin: 20px auto; color:#222; }
    h1 { font-size: 28px; margin-bottom: 8px; }
    .meta { color:#666; margin-bottom: 16px; }
    h2 { border-bottom:1px solid #ddd; padding-bottom:6px; margin-top: 18px; }
    table { width:100%; border-collapse: collapse; margin-top:8px; }
    th, td { border:1px solid #eee; padding:10px; text-align:center; }
    th { background: #f7f7f7; }
    .up { color:#d9534f; font-weight: 600; }
    .down { color:#337ab7; font-weight: 600; }
    .flat { color:#888; font-weight: 600; }
    .warn { color:#999; font-style: italic; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="meta">기준일: {{ base_date }}</div>
  {% for category, rows in grouped.items() %}
    <h2>{{ category }}</h2>
    <table>
      <thead><tr><th>항목</th><th>종가</th><th>전일 대비</th></tr></thead>
      <tbody>
      {% for row in rows %}
        <tr>
          <td>{{ row['label'] }}</td>
          {% if row['value'] is not none %}
            <td>{{ "{:,.2f}".format(row['value']) }}</td>
            <td class="{{ row['direction'] }}">
              {{ "▲" if row['change_pct'] > 0 else "▼" if row['change_pct'] < 0 else "-" }} {{ "{:.2f}".format(row['change_pct']|abs) }}%
            </td>
          {% else %}
            <td colspan="2" class="warn">데이터 없음</td>
          {% endif %}
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% endfor %}
</body>
</html>
"""
)


def latest_business_day(today: datetime) -> datetime:
    day = today - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def fetch_item(item: MarketItem, base_day: datetime) -> dict:
    start = (base_day - timedelta(days=7)).strftime("%Y-%m-%d")
    end = (base_day + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        df = fdr.DataReader(item.symbol, start, end)
    except Exception:
        return {"category": item.category, "label": item.label, "value": None, "change_pct": None, "direction": "flat"}

    if df.empty or "Close" not in df.columns:
        return {"category": item.category, "label": item.label, "value": None, "change_pct": None, "direction": "flat"}

    closes = df["Close"].dropna().tail(2)
    if len(closes) < 2:
        return {"category": item.category, "label": item.label, "value": None, "change_pct": None, "direction": "flat"}

    prev_close, close = closes.iloc[0], closes.iloc[1]
    change_pct = ((close / prev_close) - 1) * 100
    direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
    return {
        "category": item.category,
        "label": item.label,
        "value": float(close),
        "change_pct": float(change_pct),
        "direction": direction,
    }


def generate() -> Path:
    today = datetime.now(UTC) + timedelta(hours=9)  # KST
    base_day = latest_business_day(today)
    rows = [fetch_item(item, base_day) for item in ITEMS]

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)

    output_dir = Path("reports/daily")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"market_summary_{base_day:%Y-%m-%d}.html"
    output_path.write_text(
        TEMPLATE.render(title="전일 시장 요약", base_date=base_day.strftime("%Y-%m-%d"), grouped=grouped),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    out = generate()
    print(f"generated: {out}")
