export default function ScanButton({ onClick, scanning }) {
  return (
    <button
      onClick={onClick}
      disabled={scanning}
      className={`
        px-6 py-2.5 rounded-lg font-medium text-sm transition-all duration-200
        ${
          scanning
            ? "bg-accent-blue/20 text-accent-blue cursor-not-allowed"
            : "bg-accent-blue hover:bg-accent-blue/80 text-white cursor-pointer"
        }
      `}
    >
      {scanning ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12" cy="12" r="10"
              stroke="currentColor" strokeWidth="4" fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          分析中...（数分かかります）
        </span>
      ) : (
        "週間スキャン実行"
      )}
    </button>
  );
}
