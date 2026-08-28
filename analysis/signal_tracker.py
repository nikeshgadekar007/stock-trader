"""
Signal Outcome Tracker - Logs every signal and tracks forward returns.

Storage: SQLite database (signal_outcomes.db)
- Auto-created on first use
- Lazy-update: outcomes filled in when Performance page is viewed
"""
import sqlite3
import json
import os
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
from typing import Dict, List
import yfinance as yf


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'signal_outcomes.db')


def init_db():
    """Create signal_outcomes table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS signal_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL NOT NULL,
            grade TEXT NOT NULL,
            signal TEXT NOT NULL,
            entry_price REAL,
            entry_date TEXT,
            return_5d REAL,
            return_10d REAL,
            win_5d INTEGER,
            win_10d INTEGER,
            regime TEXT,
            sector TEXT,
            layers_json TEXT,
            updated_at TEXT
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON signal_outcomes(symbol)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_grade ON signal_outcomes(grade)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON signal_outcomes(timestamp)')
    conn.commit()
    conn.close()


def log_signal(symbol, direction, score, max_score, grade, signal,
                entry_price=None, regime=None, sector=None, layers=None):
    """Log a new signal. Returns the row id. No-op if duplicate today."""
    init_db()
    timestamp = datetime.now().isoformat()
    entry_date = datetime.now().strftime('%Y-%m-%d')
    layers_json = json.dumps(layers) if layers else None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''SELECT id FROM signal_outcomes
                  WHERE symbol=? AND entry_date=? AND direction=?''',
              (symbol, today, direction))
    existing = c.fetchone()
    if existing:
        conn.close()
        return existing[0]

    c.execute('''INSERT INTO signal_outcomes
        (timestamp, symbol, direction, score, max_score, grade, signal,
         entry_price, entry_date, regime, sector, layers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (timestamp, symbol, direction, score, max_score, grade, signal,
         entry_price, entry_date, regime, sector, layers_json))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def update_outcomes(symbol=None, batch_size=50):
    """
    Lazy-update: fetch current prices for unresolved signals and compute returns.
    Returns number of signals updated.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if symbol:
        c.execute('''SELECT id, symbol, entry_date, entry_price, direction
                      FROM signal_outcomes
                      WHERE symbol=? AND (return_5d IS NULL OR return_10d IS NULL)''',
                  (symbol,))
    else:
        c.execute('''SELECT id, symbol, entry_date, entry_price, direction
                      FROM signal_outcomes
                      WHERE return_5d IS NULL OR return_10d IS NULL
                      LIMIT ?''', (batch_size,))

    rows = c.fetchall()
    updated_count = 0

    for row in rows:
        row_id, sym, entry_date_str, entry_price, direction = row
        if not entry_price:
            try:
                t = yf.Ticker(sym)
                df = t.history(period='15d', auto_adjust=True)
                if not df.empty:
                    entry_price = float(df['Close'].iloc[0])
                    c.execute('UPDATE signal_outcomes SET entry_price=? WHERE id=?',
                              (entry_price, row_id))
            except Exception:
                pass

        if not entry_price:
            continue

        try:
            t = yf.Ticker(sym)
            df = t.history(start=entry_date_str, period='20d', auto_adjust=True)
            if df.empty or len(df) < 2:
                continue

            closes = df['Close'].tolist()

            ret_5d = None
            win_5d = None
            if len(closes) > 5:
                ret_5d = (closes[5] - entry_price) / entry_price * 100
                if direction == 'short':
                    ret_5d = -ret_5d
                win_5d = 1 if ret_5d > 0 else 0

            ret_10d = None
            win_10d = None
            if len(closes) > 10:
                ret_10d = (closes[10] - entry_price) / entry_price * 100
                if direction == 'short':
                    ret_10d = -ret_10d
                win_10d = 1 if ret_10d > 0 else 0

            c.execute('''UPDATE signal_outcomes
                          SET return_5d=?, win_5d=?, return_10d=?, win_10d=?,
                              entry_price=?, updated_at=?
                          WHERE id=?''',
                      (ret_5d, win_5d, ret_10d, win_10d, entry_price,
                       datetime.now().isoformat(), row_id))
            updated_count += 1
        except Exception:
            continue

    conn.commit()
    conn.close()
    return updated_count


def get_performance_stats(days=90):
    """Get win rate statistics by grade, sector, regime."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    c.execute('''SELECT COUNT(*),
                        SUM(CASE WHEN win_5d=1 THEN 1 ELSE 0 END) as wins_5d,
                        AVG(return_5d) as avg_ret_5d,
                        SUM(CASE WHEN win_10d=1 THEN 1 ELSE 0 END) as wins_10d,
                        AVG(return_10d) as avg_ret_10d
                 FROM signal_outcomes
                 WHERE entry_date >= ? AND win_5d IS NOT NULL''', (cutoff,))
    overall = c.fetchone()
    total, wins_5d, avg_ret_5d, wins_10d, avg_ret_10d = overall

    c.execute('''SELECT grade, COUNT(*),
                        SUM(CASE WHEN win_5d=1 THEN 1 ELSE 0 END) as wins,
                        AVG(return_5d) as avg_ret
                 FROM signal_outcomes
                 WHERE entry_date >= ? AND win_5d IS NOT NULL
                 GROUP BY grade''', (cutoff,))
    by_grade = {}
    for row in c.fetchall():
        grade, n, wins, avg_ret = row
        wr = wins / n * 100 if n > 0 else 0
        by_grade[grade] = {'trades': n, 'wins': wins, 'win_rate': round(wr, 1),
                            'avg_return_pct': round(avg_ret or 0, 2)}

    c.execute('''SELECT sector, COUNT(*),
                        SUM(CASE WHEN win_5d=1 THEN 1 ELSE 0 END) as wins,
                        AVG(return_5d) as avg_ret
                 FROM signal_outcomes
                 WHERE entry_date >= ? AND win_5d IS NOT NULL AND sector IS NOT NULL
                 GROUP BY sector''', (cutoff,))
    by_sector = {}
    for row in c.fetchall():
        sector, n, wins, avg_ret = row
        wr = wins / n * 100 if n > 0 else 0
        by_sector[sector] = {'trades': n, 'wins': wins, 'win_rate': round(wr, 1),
                              'avg_return_pct': round(avg_ret or 0, 2)}

    c.execute('''SELECT regime, COUNT(*),
                        SUM(CASE WHEN win_5d=1 THEN 1 ELSE 0 END) as wins,
                        AVG(return_5d) as avg_ret
                 FROM signal_outcomes
                 WHERE entry_date >= ? AND win_5d IS NOT NULL AND regime IS NOT NULL
                 GROUP BY regime''', (cutoff,))
    by_regime = {}
    for row in c.fetchall():
        regime, n, wins, avg_ret = row
        wr = wins / n * 100 if n > 0 else 0
        by_regime[regime] = {'trades': n, 'wins': wins, 'win_rate': round(wr, 1),
                              'avg_return_pct': round(avg_ret or 0, 2)}

    c.execute('''SELECT timestamp, symbol, direction, score, max_score, grade,
                        entry_price, return_5d, return_10d, win_5d, win_10d, regime, sector
                 FROM signal_outcomes
                 WHERE win_5d IS NOT NULL
                 ORDER BY timestamp DESC LIMIT 20''')
    recent = []
    for row in c.fetchall():
        recent.append({
            'timestamp': row[0], 'symbol': row[1], 'direction': row[2],
            'score': row[3], 'max_score': row[4], 'grade': row[5],
            'entry_price': row[6], 'return_5d': row[7], 'return_10d': row[8],
            'win_5d': bool(row[9]), 'win_10d': bool(row[10]),
            'regime': row[11], 'sector': row[12]
        })

    conn.close()

    return {
        'total_tracked': total or 0,
        'wins_5d': wins_5d or 0,
        'wins_10d': wins_10d or 0,
        'win_rate_5d': round((wins_5d or 0) / (total or 1) * 100, 1),
        'avg_return_5d_pct': round(avg_ret_5d or 0, 2),
        'avg_return_10d_pct': round(avg_ret_10d or 0, 2),
        'by_grade': by_grade,
        'by_sector': by_sector,
        'by_regime': by_regime,
        'recent_signals': recent,
    }


def get_layer_performance(days=90):
    """
    For each layer, compute win rate when that layer scored high vs low.
    Identifies which layers are most predictive of winning trades.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute('''SELECT layers_json, win_5d FROM signal_outcomes
                 WHERE entry_date >= ? AND win_5d IS NOT NULL AND layers_json IS NOT NULL''',
              (cutoff,))

    rows = c.fetchall()
    layer_wins_high = {}
    layer_total_high = {}
    layer_wins_low = {}
    layer_total_low = {}

    for layers_json, win_5d in rows:
        try:
            layers = json.loads(layers_json)
        except Exception:
            continue
        for layer, score in layers.items():
            if score is None or not isinstance(score, (int, float)):
                continue
            threshold = 7
            if score >= threshold:
                layer_wins_high[layer] = layer_wins_high.get(layer, 0) + (1 if win_5d else 0)
                layer_total_high[layer] = layer_total_high.get(layer, 0) + 1
            else:
                layer_wins_low[layer] = layer_wins_low.get(layer, 0) + (1 if win_5d else 0)
                layer_total_low[layer] = layer_total_low.get(layer, 0) + 1

    layer_stats = {}
    all_layers = set(layer_total_high.keys()) | set(layer_total_low.keys())
    for layer in all_layers:
        h_total = layer_total_high.get(layer, 0)
        h_wins = layer_wins_high.get(layer, 0)
        l_total = layer_total_low.get(layer, 0)
        l_wins = layer_wins_low.get(layer, 0)

        h_wr = h_wins / h_total * 100 if h_total >= 5 else None
        l_wr = l_wins / l_total * 100 if l_total >= 5 else None

        if h_wr is not None and l_wr is not None:
            predictive_power = h_wr - l_wr
        else:
            predictive_power = None

        layer_stats[layer] = {
            'high_score_trades': h_total,
            'high_win_rate': round(h_wr, 1) if h_wr is not None else None,
            'low_score_trades': l_total,
            'low_win_rate': round(l_wr, 1) if l_wr is not None else None,
            'predictive_power': round(predictive_power, 1) if predictive_power is not None else None,
        }

    conn.close()
    return layer_stats


if __name__ == '__main__':
    init_db()
    print('Signal tracker DB initialized at:', DB_PATH)
    print('Stats:', get_performance_stats())