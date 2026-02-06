const trendLabels = {
  bullish: "上昇トレンド",
  bearish: "下落トレンド",
  neutral: "横ばい",
};

const trendBadge = {
  bullish: "bg-accent-green/15 text-accent-green border-accent-green/30",
  bearish: "bg-accent-red/15 text-accent-red border-accent-red/30",
  neutral: "bg-gray-500/15 text-gray-400 border-gray-500/30",
};

const sectorNames = {
  XLK: "テクノロジー",
  XLF: "金融",
  XLV: "ヘルスケア",
  XLE: "エネルギー",
  XLI: "資本財",
  XLY: "一般消費財",
  XLP: "生活必需品",
  XLU: "公益事業",
  XLB: "素材",
  XLRE: "不動産",
  XLC: "通信",
};

export default function MarketOverview({ data }) {
  if (!data) return null;

  const vixColor = (vix) => {
    if (vix == null) return "text-gray-400";
    if (vix < 15) return "text-accent-green";
    if (vix < 20) return "text-accent-yellow";
    if (vix < 30) return "text-orange-400";
    return "text-accent-red";
  };

  const vixLabel = (vix) => {
    if (vix == null) return "—";
    if (vix < 15) return "安定（リスクオン）";
    if (vix < 20) return "やや警戒";
    if (vix < 30) return "警戒（慎重に）";
    return "高警戒（様子見推奨）";
  };

  const sectors = data.sectors || [];

  return (
    <div className="bg-card rounded-lg p-5">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold text-white">相場概況</h2>
        <span
          className={`text-xs px-3 py-1 rounded-full border ${
            trendBadge[data.trend] || trendBadge.neutral
          }`}
        >
          {trendLabels[data.trend] || "不明"}
        </span>
      </div>
      <p className="text-xs text-gray-600 mb-4">市場全体の方向感・VIX・金利をまとめて表示</p>

      {/* 主要指標 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <MetricBox
          label="S&P 500（5日間）"
          sublabel="市場全体の方向感"
          value={data.spy_change_5d != null ? `${data.spy_change_5d > 0 ? "+" : ""}${data.spy_change_5d.toFixed(2)}%` : "—"}
          color={data.spy_change_5d > 0 ? "text-accent-green" : data.spy_change_5d < 0 ? "text-accent-red" : "text-gray-400"}
        />
        <MetricBox
          label="VIX（恐怖指数）"
          sublabel={vixLabel(data.vix)}
          value={data.vix != null ? data.vix.toFixed(1) : "—"}
          color={vixColor(data.vix)}
        />
        <MetricBox
          label="米10年国債利回り"
          sublabel="金利環境の参考値"
          value={data.treasury_10y != null ? `${data.treasury_10y.toFixed(2)}%` : "—"}
          color="text-gray-300"
        />
        <MetricBox
          label="市場の温度感"
          sublabel="VIXに基づく判定"
          value={data.vix != null ? (data.vix < 15 ? "安定" : data.vix < 20 ? "やや警戒" : data.vix < 30 ? "警戒" : "高警戒") : "—"}
          color={vixColor(data.vix)}
        />
      </div>

      {/* サマリー */}
      {data.summary && (
        <p className="text-sm text-gray-400 mb-4">{data.summary}</p>
      )}

      {/* セクター別パフォーマンス */}
      {Array.isArray(sectors) && sectors.length > 0 && typeof sectors[0] === "object" && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 mb-2">
            セクター別パフォーマンス（5日間）
          </h3>
          <p className="text-xs text-gray-600 mb-2">緑＝上昇セクター、赤＝下落セクター。資金の流れを把握できます。</p>
          <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {sectors.map((s) => {
              const chg = s.change_5d ?? s.change_1d;
              const color = chg > 0 ? "bg-accent-green/10 text-accent-green" : chg < 0 ? "bg-accent-red/10 text-accent-red" : "bg-gray-700/30 text-gray-400";
              return (
                <div key={s.ticker} className={`rounded px-2 py-1.5 text-center ${color}`}>
                  <div className="text-xs font-medium">{sectorNames[s.ticker] || s.ticker}</div>
                  <div className="text-[10px] text-gray-500">{s.ticker}</div>
                  <div className="text-xs font-semibold mt-0.5">{chg != null ? `${chg > 0 ? "+" : ""}${chg.toFixed(1)}%` : "—"}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* セクターリーダー/ラガード（文字列配列フォールバック） */}
      {Array.isArray(data.sector_leaders) && data.sector_leaders.length > 0 && typeof data.sector_leaders[0] === "string" && (
        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <h3 className="text-xs font-semibold text-gray-500 mb-1">好調セクター</h3>
            <div className="flex flex-wrap gap-1">
              {data.sector_leaders.map((t) => (
                <span key={t} className="text-xs bg-accent-green/10 text-accent-green px-2 py-0.5 rounded">
                  {sectorNames[t] || t}
                </span>
              ))}
            </div>
          </div>
          {Array.isArray(data.sector_laggards) && data.sector_laggards.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-500 mb-1">不調セクター</h3>
              <div className="flex flex-wrap gap-1">
                {data.sector_laggards.map((t) => (
                  <span key={t} className="text-xs bg-accent-red/10 text-accent-red px-2 py-0.5 rounded">
                    {sectorNames[t] || t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricBox({ label, value, color, sublabel }) {
  return (
    <div className="bg-surface rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-semibold ${color || "text-white"}`}>{value}</div>
      {sublabel && <div className="text-[10px] text-gray-600 mt-0.5">{sublabel}</div>}
    </div>
  );
}
