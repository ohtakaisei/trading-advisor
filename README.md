# Weekly Trading Advisor

S&P 500銘柄を対象に、テクニカル分析とLLMエージェントを組み合わせた週次トレード推奨システム。

## アーキテクチャ概要

```
[React Frontend] <--API--> [FastAPI Backend]
                                  |
                     Phase A: ルールベーススクリーニング
                     (yfinance + pandas-ta)
                                  |
                     Phase B: LLMエージェント分析
                     (LangGraph ReAct Agent + GPT-4o)
                                  |
                           JSON レポート出力
```

## LangChain / LangGraph の利用方法

このシステムでは、**LangGraph**（LangChainエコシステムの一部）を使って、LLMが自律的にツールを呼び出しながら株式分析を行う**ReActエージェント**を構築しています。

### 使用しているライブラリ

| パッケージ | 用途 |
|---|---|
| `langgraph` | ReActエージェントの構築 (`create_react_agent`) |
| `langchain-openai` | OpenAI GPT-4oとの接続 (`ChatOpenAI`) |
| `langchain-core` | カスタムツールの定義 (`@tool` デコレータ) |

### 2フェーズ分析パイプライン

#### Phase A: ルールベーススクリーニング (`screener.py`)

LLMは使用しません。S&P 500全銘柄（約500銘柄）の1年分のデータを`yfinance`でバッチダウンロードし、`pandas-ta`で以下のテクニカルシグナルを計算します:

- RSI（買われすぎ/売られすぎ）
- MACDヒストグラム（モメンタム変化）
- ボリンジャーバンド（スクイーズ/バンドタッチ）
- SMA近接（20/50/200日移動平均線）
- 出来高急増

**2つ以上のシグナルが検出された銘柄**だけがPhase Bに進みます。

#### Phase B: LangGraph ReActエージェント (`agent.py`)

Phase Aを通過した銘柄に対して、LLMエージェントが深掘り分析を行います。

```python
# agent.py - エージェントの作成
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

graph = create_react_agent(
    llm,
    tools=ALL_TOOLS,       # 4つのカスタムツール
    prompt=SYSTEM_PROMPT,  # トレーディングアドバイザーとしての役割定義
)

# エージェントの実行
result = graph.invoke(
    {"messages": [{"role": "user", "content": analysis_prompt}]},
    config={"recursion_limit": 30},
)
```

**ReActパターン**とは、LLMが以下のループを自律的に繰り返す手法です:

1. **Reasoning（推論）**: 現在の情報を元に次のアクションを考える
2. **Acting（行動）**: ツールを呼び出してデータを取得する
3. **Observation（観察）**: ツールの結果を確認する
4. 十分な情報が揃うまで 1-3 を繰り返し、最終的にJSON形式のレポートを出力する

### カスタムツール（`@tool`デコレータ）

LangChainの`@tool`デコレータで定義された4つのツールを、LLMが**自分の判断で**呼び出します:

```
tools/
├── technicals.py  - get_stock_technicals(ticker)
├── earnings.py    - get_earnings_calendar(ticker)
├── market.py      - get_market_overview()
└── volume.py      - scan_unusual_volume()
```

| ツール | 説明 | LLMの使い方 |
|---|---|---|
| `get_stock_technicals` | 個別銘柄のRSI, MACD, BB, SMA等を取得 | Phase A通過銘柄を1つずつ詳細分析 |
| `get_earnings_calendar` | 次の決算発表日を取得 | 有望な銘柄の決算リスクを確認 |
| `get_market_overview` | SPY, VIX, 金利, セクターETF等の全体像 | 分析の最初にマーケット環境を把握 |
| `scan_unusual_volume` | 出来高異常銘柄のスキャン | 必要に応じて出来高パターンを確認 |

各ツールは内部で`yfinance`を使ってリアルタイムの市場データを取得し、JSON文字列で結果を返します。

### エージェントの実行フロー（具体例）

```
User Prompt: "Phase Aで5銘柄が通過しました: AAPL, NVDA, MSFT, TSLA, AMZN"
  │
  ├─ LLM: "まずマーケット全体を確認しよう"
  │   └─ Tool Call: get_market_overview()
  │       └─ Result: {spy: +1.2%, vix: 15.3, trend: "bullish", ...}
  │
  ├─ LLM: "各銘柄のテクニカルを詳しく見よう"
  │   ├─ Tool Call: get_stock_technicals("AAPL")
  │   ├─ Tool Call: get_stock_technicals("NVDA")
  │   ├─ Tool Call: get_stock_technicals("MSFT")
  │   ├─ Tool Call: get_stock_technicals("TSLA")
  │   └─ Tool Call: get_stock_technicals("AMZN")
  │
  ├─ LLM: "AAPLとNVDAが有望。決算リスクを確認"
  │   ├─ Tool Call: get_earnings_calendar("AAPL")
  │   └─ Tool Call: get_earnings_calendar("NVDA")
  │
  └─ LLM: 最終JSON出力
      {
        "market_overview": {...},
        "candidates": [AAPL, NVDA],      // 推奨銘柄
        "watchlist": [MSFT, AMZN],        // 監視リスト
        "risk_warnings": [...]            // リスク警告
      }
```

### プロンプト設計 (`prompts.py`)

エージェントには2つのプロンプトが与えられます:

- **システムプロンプト**: トレーディングアドバイザーとしての役割、リスク管理ルール（ポジションサイズ上限5%、リスクリワード比2:1以上等）、出力フォーマットを定義
- **分析プロンプト**: Phase Aのスクリーニング結果を含む具体的な分析指示。ツールの呼び出し順序もガイドする

## ローカル開発

```bash
# Backend
source venv/bin/activate && cd backend && uvicorn main:app --reload --port 8000

# Frontend（別ターミナル）
cd frontend && npm run dev
```

## 技術スタック

- **Backend**: FastAPI, LangGraph, LangChain, OpenAI GPT-4o, yfinance, pandas-ta
- **Frontend**: React (Vite), Tailwind CSS
- **Deployment**: Render
