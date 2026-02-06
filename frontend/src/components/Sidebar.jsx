const trendLabel = {
  bullish: "上昇",
  bearish: "下落",
  neutral: "横ばい",
  unknown: "不明",
};

const trendColor = {
  bullish: "text-accent-green",
  bearish: "text-accent-red",
  neutral: "text-gray-400",
  unknown: "text-gray-500",
};

export default function Sidebar({ reports, onSelect, activeDate }) {
  return (
    <aside className="w-64 bg-card border-r border-gray-800 overflow-y-auto flex-shrink-0">
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          過去のレポート
        </h2>
        <p className="text-xs text-gray-600 mt-1">クリックで過去の分析結果を表示</p>
      </div>

      {reports.length === 0 ? (
        <p className="text-gray-600 text-xs p-4">レポートはまだありません</p>
      ) : (
        <ul>
          {reports.map((r) => (
            <li key={r.date}>
              <button
                onClick={() => onSelect(r.date)}
                className={`w-full text-left px-4 py-3 border-b border-gray-800/50 transition-colors hover:bg-card-hover ${
                  activeDate === r.date ? "bg-card-hover border-l-2 border-l-accent-blue" : ""
                }`}
              >
                <div className="text-sm font-medium text-white">{r.date}</div>
                <div className="flex items-center gap-2 mt-1 text-xs">
                  <span className="text-gray-400">
                    候補 {r.candidates}件
                  </span>
                  <span className={trendColor[r.trend] || "text-gray-500"}>
                    {trendLabel[r.trend] || r.trend}
                  </span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
