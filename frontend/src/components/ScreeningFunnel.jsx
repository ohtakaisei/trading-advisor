const stageInfo = {
  universe: "監視対象の全銘柄数",
  phaseA: "テクニカル条件を2つ以上満たした銘柄",
  candidates: "AIが売買推奨と判断した銘柄",
  watchlist: "条件待ちで監視を続ける銘柄",
};

export default function ScreeningFunnel({ stats }) {
  if (!stats) return null;

  const stages = [
    { label: "全銘柄", value: stats.total_universe, color: "bg-gray-500", info: stageInfo.universe },
    { label: "Phase A通過", value: stats.phase_a_passed, color: "bg-accent-blue", info: stageInfo.phaseA },
    { label: "売買候補", value: stats.phase_b_candidates, color: "bg-accent-green", info: stageInfo.candidates },
    { label: "注目銘柄", value: stats.watchlist_count, color: "bg-accent-yellow", info: stageInfo.watchlist },
  ];

  const maxVal = Math.max(...stages.map((s) => s.value || 0), 1);

  return (
    <div className="bg-card rounded-lg p-5 h-full">
      <h2 className="text-lg font-semibold text-white mb-1">スクリーニング結果</h2>
      <p className="text-xs text-gray-600 mb-4">全銘柄 → ルール選別 → AI分析の絞り込みフロー</p>
      <div className="space-y-3">
        {stages.map((stage) => {
          const pct = ((stage.value || 0) / maxVal) * 100;
          return (
            <div key={stage.label}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-gray-400">{stage.label}</span>
                <span className="text-white font-medium">{stage.value ?? 0}件</span>
              </div>
              <div className="h-3 bg-surface rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${stage.color} transition-all duration-500`}
                  style={{ width: `${Math.max(pct, 2)}%` }}
                />
              </div>
              <p className="text-[10px] text-gray-600 mt-0.5">{stage.info}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
