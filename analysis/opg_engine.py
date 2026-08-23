"""Opening Price Gap (OPG) Detection with Historical Database"""
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from typing import Dict, List
import os
import warnings
warnings.filterwarnings('ignore')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'opg_history.db')


class OPGDatabase:
    """SQLite store for OPG history"""
    def __init__(self):
        self.db_path = DB_PATH
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.db_path); c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL, date TEXT NOT NULL,
            prev_close REAL, open_price REAL, gap_pct REAL,
            gap_type TEXT, vol_ratio REAL, signal TEXT,
            score INTEGER, outcome_1d REAL, outcome_3d REAL,
            filled INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date))''')
        conn.commit(); conn.close()

    def save(self, data: Dict):
        try:
            conn = sqlite3.connect(self.db_path); c = conn.cursor()
            c.execute('''INSERT OR IGNORE INTO gaps (symbol,date,prev_close,open_price,gap_pct,gap_type,vol_ratio,signal,score)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (data['symbol'],data['date'],data.get('prev_close',0),data.get('open_price',0),
                 data.get('gap_pct',0),data.get('gap_type',''),data.get('vol_ratio',1),
                 data.get('signal',''),data.get('score',0)))
            conn.commit(); conn.close()
        except Exception: pass

    def get_today(self) -> List[Dict]:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row; c = conn.cursor()
            c.execute('SELECT * FROM gaps WHERE date=? ORDER BY abs(gap_pct) DESC', (today,))
            rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
        except: return []

    def get_stats(self) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path); c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM gaps'); total = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM gaps WHERE gap_type="GAP_UP"'); ups = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM gaps WHERE gap_type="GAP_DOWN"'); downs = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM gaps WHERE filled=1'); filled = c.fetchone()[0]
            conn.close()
            return {'total':total, 'gap_ups':ups, 'gap_downs':downs,
                    'filled':filled, 'fill_rate':round((filled/max(1,total))*100,1)}
        except: return {}
class OPGDetector:
    """Detect and score opening price gaps"""
    def __init__(self):
        self.db = OPGDatabase()

    def detect_today(self, symbol) -> Dict:
        try:
            t = yf.Ticker(symbol)
            intra = t.history(period='5d', interval='5m', prepost=True, auto_adjust=True)
            daily = t.history(period='1mo', prepost=False, auto_adjust=True)
            if intra.empty or len(intra) < 6 or daily.empty or len(daily) < 2:
                return {'symbol': symbol, 'gap': False, 'signal': 'NO_DATA'}
            today = intra.index[-1].date()
            bars = intra[intra.index.date == today]
            if bars.empty or len(bars) < 3:
                return {'symbol': symbol, 'gap': False, 'signal': 'PRE_MARKET'}
            prev = daily[daily.index.date < today]
            if prev.empty:
                return {'symbol': symbol, 'gap': False, 'signal': 'NO_PREV'}
            pc = prev['Close'].iloc[-1]; op = bars['Open'].iloc[0]
            hi = bars['High'].max(); lo = bars['Low'].min(); cl = bars['Close'].iloc[-1]
            gp = ((op - pc) / pc) * 100
            f30 = bars[(bars.index.time <= pd.Timestamp('10:00').time())]
            v30 = f30['Volume'].sum() if len(f30) >= 2 else bars['Volume'].sum()
            avg = bars['Volume'].mean() * 6; vr = v30 / max(avg, 1)
            if abs(gp) < 0.5: gt, sig = 'NO_GAP', 'NO_SIGNAL'
            elif gp >= 1.0:
                if hi >= op * 1.005 and cl > pc: gt, sig = 'GAP_UP', 'GAP_AND_GO'
                elif cl < op * 0.997: gt, sig = 'GAP_UP', 'GAP_FILL'
                else: gt, sig = 'GAP_UP', 'GAP_HOLD'
            else:
                if lo <= op * 0.995 and cl < pc: gt, sig = 'GAP_DOWN', 'GAP_DOWN_AND_GO'
                elif cl > op * 1.003: gt, sig = 'GAP_DOWN', 'GAP_DOWN_FILL'
                else: gt, sig = 'GAP_DOWN', 'GAP_DOWN_HOLD'
            sc = 5; ag = abs(gp)
            if 1.0 <= ag <= 3.0: sc += 3
            elif 0.5 <= ag < 1.0: sc += 2
            elif ag > 3.0: sc += 1
            if vr > 2.0: sc += 2
            elif vr > 1.5: sc += 1
            if sig in ('GAP_AND_GO','GAP_DOWN_AND_GO'): sc += 1
            sc = min(sc, 10)
            r = {'symbol':symbol,'date':str(today),'prev_close':round(pc,2),'open_price':round(op,2),
                 'gap_pct':round(gp,2),'gap_type':gt,'vol_ratio':round(vr,2),'signal':sig,
                 'score':sc,'gap':abs(gp)>=0.5}
            self.db.save(r)
            return r
        except Exception as e:
            return {'symbol': symbol, 'gap': False, 'signal': f'ERR:{str(e)[:40]}'}

    def scan(self, symbols) -> List[Dict]:
        results = []
        for s in symbols:
            r = self.detect_today(s)
            if r.get('gap'): results.append(r)
        return sorted(results, key=lambda x: abs(x.get('gap_pct', 0)), reverse=True)

    def backtest(self, symbol, period='1y') -> Dict:
        try:
            t = yf.Ticker(symbol); df = t.history(period=period, auto_adjust=True)
            if df.empty or len(df) < 60: return {'error':'Insufficient data'}
            df['pc'] = df['Close'].shift(1)
            df['gp'] = ((df['Open'] - df['pc']) / df['pc']) * 100
            df['vm'] = df['Volume'].rolling(20).mean()
            df['vr'] = (df['Volume'] / df['vm']).fillna(1)
            trades = []
            for i, r in df.iterrows():
                if abs(r['gp']) < 1.0 or r['vr'] < 1.5: continue
                e = r['Open']; pnl = ((df['Close'].iloc[min(i+3,len(df)-1)]-e)/e)*100
                trades.append({'date':str(i.date()),'signal':'GAP_UP' if r['gp']>0 else 'GAP_DOWN',
                               'gap_pct':round(r['gp'],2),'pnl':round(pnl,2)})
            if not trades: return {'trades':0,'win_rate':0}
            wins = [t for t in trades if t['pnl']>0]; losses = [t for t in trades if t['pnl']<=0]
            wr = len(wins)/len(trades)*100
            return {'symbol':symbol,'total_trades':len(trades),'wins':len(wins),'losses':len(losses),
                    'win_rate':round(wr,1),'avg_win':round(np.mean([t['pnl'] for t in wins]) if wins else 0,2),
                    'avg_loss':round(np.mean([abs(t['pnl']) for t in losses]) if losses else 0,2),
                    'trades':trades[-20:]}
        except Exception as e: return {'error': str(e)}


    def get_history(self, symbol=None, limit=50) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row; c = conn.cursor()
            if symbol: c.execute('SELECT * FROM gaps WHERE symbol=? ORDER BY date DESC LIMIT ?', (symbol, limit))
            else: c.execute('SELECT * FROM gaps ORDER BY date DESC LIMIT ?', (limit,))
            rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
        except: return []