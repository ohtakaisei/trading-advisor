export default function RiskWarnings({ warnings }) {
  if (!warnings?.length) return null;

  return (
    <div className="bg-accent-red/5 border border-accent-red/20 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-accent-red mb-1">リスク警告</h3>
      <p className="text-[10px] text-accent-red/50 mb-2">現在の相場状況で注意すべきポイントです。トレード前に必ず確認してください。</p>
      <ul className="space-y-1">
        {warnings.map((w, i) => (
          <li key={i} className="text-sm text-accent-red/80 flex items-start gap-2">
            <span className="mt-0.5 shrink-0">&#x26A0;</span>
            <span>{w}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
