const actionLabels = {
  BUY: "買い",
  SELL: "売り",
  HOLD: "様子見",
};

const actionColor = {
  BUY: "bg-accent-green/15 text-accent-green border-accent-green/30",
  SELL: "bg-accent-red/15 text-accent-red border-accent-red/30",
  HOLD: "bg-accent-yellow/15 text-accent-yellow border-accent-yellow/30",
};

const confidenceLabels = {
  high: "自信度：高",
  medium: "自信度：中",
  low: "自信度：低",
};

const confidenceColor = {
  high: "text-accent-green",
  medium: "text-accent-yellow",
  low: "text-gray-400",
};

export default function CandidateCard({ candidate: c }) {
  if (!c) return null;

  return (
    <div className="bg-card rounded-lg p-5 border border-gray-800 hover:border-gray-700 transition-colors">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-bold text-white">{c.ticker}</h3>
          <span className={`text-xs px-2.5 py-0.5 rounded-full border ${actionColor[c.action] || actionColor.HOLD}`}>
            {actionLabels[c.action] || c.action}
          </span>
        </div>
        <span className={`text-xs font-medium ${confidenceColor[c.confidence] || "text-gray-400"}`}>
          {confidenceLabels[c.confidence] || c.confidence}
        </span>
      </div>

      {/* 価格レベル */}
      <div className="grid grid-cols-3 gap-3 mb-2">
        <PriceBox label="エントリー" sublabel="この価格で購入" value={c.entry_price} color="text-white" />
        <PriceBox label="損切りライン" sublabel="ここで撤退" value={c.stop_loss} color="text-accent-red" />
        <PriceBox label="利確目標" sublabel="ここで利益確定" value={c.target_price} color="text-accent-green" />
      </div>
      <p className="text-[10px] text-gray-600 mb-4">
        ※ 損切り＝損失を限定するための撤退価格、利確＝利益を確定するための目標価格
      </p>

      {/* 指標 */}
      <div className="flex flex-wrap gap-3 mb-4 text-xs">
        {c.risk_reward_ratio != null && (
          <span className="bg-surface px-2 py-1 rounded text-gray-300" title="リスクリワード比（1以上が望ましい）">
            損益比 {c.risk_reward_ratio.toFixed(1)}:1
          </span>
        )}
        {c.position_size_pct != null && (
          <span className="bg-surface px-2 py-1 rounded text-gray-300" title="ポートフォリオ全体に対する推奨比率">
            推奨比率 {c.position_size_pct}%
          </span>
        )}
        {c.timeframe && (
          <span className="bg-surface px-2 py-1 rounded text-gray-300">
            保有期間 {c.timeframe}
          </span>
        )}
      </div>

      {/* テクニカルシグナル */}
      {c.technical_signals?.length > 0 && (
        <div className="mb-3">
          <span className="text-[10px] text-gray-500 block mb-1">検出されたシグナル：</span>
          <div className="flex flex-wrap gap-1.5">
            {c.technical_signals.map((sig, i) => (
              <span key={i} className="text-xs bg-accent-blue/10 text-accent-blue px-2 py-0.5 rounded">
                {sig}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 分析理由 */}
      {c.reasoning && (
        <div className="mb-3">
          <span className="text-[10px] text-gray-500 block mb-1">AIの判断理由：</span>
          <p className="text-sm text-gray-400">{c.reasoning}</p>
        </div>
      )}

      {/* リスク要因 */}
      {c.risk_factors?.length > 0 && (
        <div className="mb-2">
          <span className="text-[10px] text-gray-500 block mb-1">注意すべきリスク：</span>
          <span className="text-xs text-accent-red/70">{c.risk_factors.join(" ／ ")}</span>
        </div>
      )}

      {/* 決算警告 */}
      {c.earnings_warning && (
        <div className="bg-accent-yellow/10 border border-accent-yellow/20 rounded px-3 py-2 mt-2">
          <span className="text-xs text-accent-yellow">決算注意: {c.earnings_warning}</span>
        </div>
      )}
    </div>
  );
}

function PriceBox({ label, sublabel, value, color }) {
  return (
    <div className="bg-surface rounded p-2.5 text-center">
      <div className="text-xs text-gray-500 mb-0.5">{label}</div>
      <div className={`text-sm font-semibold ${color}`}>
        {value != null ? `$${Number(value).toFixed(2)}` : "—"}
      </div>
      {sublabel && <div className="text-[10px] text-gray-600 mt-0.5">{sublabel}</div>}
    </div>
  );
}
