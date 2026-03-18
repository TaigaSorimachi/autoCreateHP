"""
アポ太郎 — 自動パイプライン
検索 → HP生成 → 一覧更新 を完全自動で実行

使い方:
  # ワンショット実行
  python pipeline.py

  # スケジューラー（毎日指定時刻に自動実行）
  python pipeline.py --schedule 09:00

  # エリア・業種指定
  python pipeline.py --area "渋谷" --type restaurant --radius 1500

  # 複数エリア一括
  python pipeline.py --areas "中洲,天神,博多駅前"
"""

import argparse
import json
import os
import time
import threading
from datetime import datetime
from config import GENERATED_SITES_DIR, DEFAULT_AREA, DEFAULT_BUSINESS_TYPE, DEFAULT_RADIUS
from discovery import search_businesses, save_businesses, load_businesses
from generator import generate_all_hps, list_generated_sites


class Pipeline:
    """検索→生成→レポートの全自動パイプライン"""

    def __init__(self):
        self.log_entries: list[dict] = []
        os.makedirs(GENERATED_SITES_DIR, exist_ok=True)

    def log(self, msg: str, level: str = "info"):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": msg,
        }
        self.log_entries.append(entry)
        icon = {"info": "ℹ️", "success": "✅", "error": "❌", "start": "🚀"}
        print(f'  {icon.get(level, "•")} [{entry["time"]}] {msg}')

    def run(
        self,
        areas: list[str] | None = None,
        business_type: str = DEFAULT_BUSINESS_TYPE,
        radius: int = DEFAULT_RADIUS,
    ) -> dict:
        """
        パイプライン全体を実行
        Returns: 実行結果サマリー
        """
        if areas is None:
            areas = [DEFAULT_AREA]

        start_time = time.time()
        self.log_entries = []

        print()
        print("╔══════════════════════════════════════════════╗")
        print("║   🤖 アポ太郎 — 自動パイプライン実行開始       ║")
        print("╚══════════════════════════════════════════════╝")
        print()

        # ──────────────────────────────
        # STEP 1: ビジネス発見
        # ──────────────────────────────
        self.log(f"STEP 1/3: ビジネス発見 ({len(areas)}エリア)", "start")
        all_businesses = []

        for area in areas:
            self.log(f'  検索中: {area} / {business_type} / 半径{radius}m')
            businesses = search_businesses(area, business_type, radius)
            self.log(f'  → {len(businesses)}件発見', "success")
            all_businesses.extend(businesses)

        # 重複排除（place_id ベース）
        seen = set()
        unique = []
        for biz in all_businesses:
            pid = biz.get("place_id", biz["name"])
            if pid not in seen:
                seen.add(pid)
                unique.append(biz)
        all_businesses = unique

        self.log(f"発見合計: {len(all_businesses)}件（重複排除済み）", "success")

        # ──────────────────────────────
        # STEP 2: データ保存
        # ──────────────────────────────
        self.log("STEP 2/3: データ保存", "start")
        saved = save_businesses(all_businesses)
        self.log(f"保存完了: 累計{len(saved)}件", "success")

        # ──────────────────────────────
        # STEP 3: HP一括生成
        # ──────────────────────────────
        self.log("STEP 3/3: HP一括生成", "start")
        generated = generate_all_hps(all_businesses)
        self.log(f"HP生成完了: {len(generated)}件", "success")

        # ──────────────────────────────
        # レポート出力
        # ──────────────────────────────
        elapsed = round(time.time() - start_time, 1)
        sites = list_generated_sites()

        report = {
            "executed_at": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "areas_searched": areas,
            "business_type": business_type,
            "radius": radius,
            "businesses_discovered": len(all_businesses),
            "hps_generated": len(generated),
            "total_sites": len(sites),
            "generated_sites": [
                {
                    "name": s["business_name"],
                    "folder": s["folder"],
                    "url": f'/sites/{s["folder"]}/index.html',
                }
                for s in sites
            ],
        }

        # レポートをJSONで保存
        report_path = os.path.join(GENERATED_SITES_DIR, "pipeline_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print()
        print("┌──────────────────────────────────────────────┐")
        print("│           📊 パイプライン実行完了              │")
        print("├──────────────────────────────────────────────┤")
        print(f"│  検索エリア:     {', '.join(areas):<28}│")
        print(f"│  業種:           {business_type:<28}│")
        print(f"│  発見ビジネス:   {len(all_businesses):<28}│")
        print(f"│  生成HP数:       {len(generated):<28}│")
        print(f"│  実行時間:       {elapsed}秒{' ' * (25 - len(str(elapsed)))}│")
        print("├──────────────────────────────────────────────┤")
        print("│  生成済みHP一覧:                              │")
        for s in sites:
            name = s["business_name"][:25]
            print(f"│    🏪 {name:<38}│")
        print("├──────────────────────────────────────────────┤")
        print("│  ダッシュボード: http://127.0.0.1:5000        │")
        print("└──────────────────────────────────────────────┘")
        print()

        return report


class Scheduler:
    """定期自動実行スケジューラー"""

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self._running = False

    def start(
        self,
        schedule_time: str,
        areas: list[str],
        business_type: str,
        radius: int,
        run_on_start: bool = True,
    ):
        """
        毎日指定時刻にパイプラインを実行
        schedule_time: "HH:MM" 形式
        """
        self._running = True
        hour, minute = map(int, schedule_time.split(":"))

        print(f"🕐 スケジューラー起動: 毎日 {schedule_time} に自動実行")
        print(f"   エリア: {', '.join(areas)}")
        print(f"   業種: {business_type}")
        print(f"   Ctrl+C で停止\n")

        if run_on_start:
            print("── 初回実行（即時） ──")
            self.pipeline.run(areas, business_type, radius)

        while self._running:
            now = datetime.now()
            if now.hour == hour and now.minute == minute:
                print(f"\n── スケジュール実行 ({now.strftime('%Y-%m-%d %H:%M')}) ──")
                self.pipeline.run(areas, business_type, radius)
                # 同じ分に再実行しないよう待機
                time.sleep(61)
            else:
                time.sleep(30)

    def stop(self):
        self._running = False


def run_pipeline_async(
    areas: list[str] | None = None,
    business_type: str = DEFAULT_BUSINESS_TYPE,
    radius: int = DEFAULT_RADIUS,
    callback=None,
) -> threading.Thread:
    """
    バックグラウンドでパイプラインを実行（Flask API から呼ぶ用）
    """
    pipeline = Pipeline()

    def _run():
        report = pipeline.run(areas, business_type, radius)
        if callback:
            callback(report)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


# ──────────────────────────────
#  CLI エントリーポイント
# ──────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="アポ太郎 自動パイプライン")
    parser.add_argument("--area", default=DEFAULT_AREA, help="検索エリア（単一）")
    parser.add_argument("--areas", default=None, help="検索エリア（カンマ区切り複数）")
    parser.add_argument("--type", default=DEFAULT_BUSINESS_TYPE, dest="business_type", help="業種")
    parser.add_argument("--radius", type=int, default=DEFAULT_RADIUS, help="検索半径（メートル）")
    parser.add_argument("--schedule", default=None, help="定期実行（HH:MM形式）例: --schedule 09:00")
    args = parser.parse_args()

    # エリア解析
    if args.areas:
        areas = [a.strip() for a in args.areas.split(",")]
    else:
        areas = [args.area]

    pipeline = Pipeline()

    if args.schedule:
        scheduler = Scheduler(pipeline)
        try:
            scheduler.start(args.schedule, areas, args.business_type, args.radius)
        except KeyboardInterrupt:
            scheduler.stop()
            print("\n🛑 スケジューラー停止")
    else:
        pipeline.run(areas, args.business_type, args.radius)
