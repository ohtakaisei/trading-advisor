const dirLabels = {
  bullish: "上昇狙い",
  bearish: "下落狙い",
  neutral: "方向未定",
};

const dirColor = {
  bullish: "text-accent-green",
  bearish: "text-accent-red",
  neutral: "text-gray-400",
};

export default function WatchlistSection({ items }) {
  if (!items?.length) return null;

  return (
    <section>
      <h2 className="text-lg font-semibold text-white mb-1">
        注目銘柄（{items.length}件）
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        まだ売買条件は揃っていませんが、条件を満たせばエントリー候補になる銘柄です。
        「トリガー条件」に書かれた状況になったら再チェックしてください。
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {items.map((item, i) => (
          <div
            key={item?.ticker || i}
            className="bg-card rounded-lg p-4 border border-gray-800"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-white">{item.ticker}</span>
              <span className={`text-xs ${dirColor[item.direction] || "text-gray-400"}`}>
                {dirLabels[item.direction] || item.direction}
              </span>
            </div>
            {item.trigger_condition && (
              <div className="mb-1">
                <span className="text-[10px] text-gray-500 block">トリガー条件：</span>
                <p className="text-xs text-accent-blue">{item.trigger_condition}</p>
              </div>
            )}
            {item.notes && (
              <p className="text-xs text-gray-500 mt-1">{item.notes}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
