import { useState, useEffect } from "react";
import ScanButton from "./components/ScanButton";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [report, setReport] = useState(null);
  const [reports, setReports] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  async function fetchReports() {
    try {
      const res = await fetch("/api/reports");
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch {
      // silently ignore on initial load
    }
  }

  async function runScan() {
    setScanning(true);
    setError(null);
    try {
      const res = await fetch("/api/scan", { method: "POST" });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `スキャンに失敗しました (${res.status})`);
      }
      const data = await res.json();
      setReport(data);
      fetchReports();
    } catch (e) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  }

  async function loadReport(dateStr) {
    try {
      const res = await fetch(`/api/reports/${dateStr}`);
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar reports={reports} onSelect={loadReport} activeDate={report?.date} />

      <main className="flex-1 overflow-y-auto p-6">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">週間トレードアドバイザー</h1>
            <p className="text-sm text-gray-500">米国株スイングトレード スキャナー</p>
          </div>
          <ScanButton onClick={runScan} scanning={scanning} />
        </header>

        {error && (
          <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-4 mb-6">
            <p className="text-accent-red text-sm">{error}</p>
          </div>
        )}

        {report ? (
          <Dashboard report={report} />
        ) : (
          <div className="flex items-center justify-center h-96">
            <div className="text-center max-w-md">
              <p className="text-gray-400 text-lg mb-3">レポートがありません</p>
              <p className="text-gray-500 text-sm leading-relaxed">
                右上の「週間スキャン実行」ボタンを押すと、全銘柄のテクニカル分析を行い、
                売買候補を提案します。過去のレポートは左のサイドバーから選択できます。
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
