import MarketOverview from "./MarketOverview";
import CandidateCard from "./CandidateCard";
import WatchlistSection from "./WatchlistSection";
import RiskWarnings from "./RiskWarnings";
import ScreeningFunnel from "./ScreeningFunnel";

export default function Dashboard({ report }) {
  const market = report?.market_overview;
  const candidates = report?.candidates || [];
  const watchlist = report?.watchlist || [];
  const warnings = report?.risk_warnings || [];
  const stats = report?.screening_stats;

  return (
    <div className="space-y-6">
      {/* 使い方ガイド */}
      <div className="bg-accent-blue/5 border border-accent-blue/20 rounded-lg px-4 py-3">
        <p className="text-xs text-accent-blue/80 leading-relaxed">
          <span className="font-semibold">見方：</span>
          「相場概況」で市場全体のトレンドを確認 → 「スクリーニング結果」で絞り込み状況を把握 →
          「売買候補」でエントリー・損切り・利確の具体的な価格を確認 → 「注目銘柄」で次の候補をチェック
        </p>
      </div>

      {/* 上段: 相場概況 + スクリーニングファネル */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MarketOverview data={market} />
        </div>
        <div>
          <ScreeningFunnel stats={stats} />
        </div>
      </div>

      {/* リスク警告 */}
      {warnings.length > 0 && <RiskWarnings warnings={warnings} />}

      {/* 売買候補 */}
      {candidates.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-1">
            売買候補（{candidates.length}件）
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            AIが選んだ今週の注目トレード。エントリー価格・損切り・利確目標が設定済みです。
          </p>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {candidates.map((c, i) => (
              <CandidateCard key={c?.ticker || i} candidate={c} />
            ))}
          </div>
        </section>
      )}

      {/* 候補なしメッセージ */}
      {candidates.length === 0 && (
        <div className="bg-card rounded-lg p-8 text-center">
          <p className="text-gray-400">今回のスキャンでは売買候補が見つかりませんでした。</p>
          <p className="text-gray-600 text-sm mt-1">
            下の「注目銘柄」に、条件が揃えばエントリー可能な銘柄があります。
          </p>
        </div>
      )}

      {/* 注目銘柄（ウォッチリスト） */}
      {watchlist.length > 0 && <WatchlistSection items={watchlist} />}
    </div>
  );
}
