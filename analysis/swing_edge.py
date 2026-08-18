"""
Swing Edge Engine -- 5 Institutional-Grade Strategies
Options Wall, VIX Term Structure, Cross-Asset, SMI, Liquidity Sweep
"""
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


class SwingEdgeEngine:
    @staticmethod
    def options_wall(sym, cp):
        try:
            t = yf.Ticker(sym)
            exp = t.options[0] if t.options else None
            if not exp:
                return {'call_wall': None, 'put_wall': None, 'signal': 'NO_DATA', 'score': 5}
            chain = t.option_chain(exp)
            c = chain.calls
            p = chain.puts
            if c.empty or p.empty:
                return {'call_wall': None, 'put_wall': None, 'signal': 'NO_DATA', 'score': 5}
            cw = float(c.strike.iloc[c.openInterest.argmax()])
            pw = float(p.strike.iloc[p.openInterest.argmax()])
            r = {'call_wall': cw, 'put_wall': pw, 'expiry': exp}
            if cp > cw:
                r['signal'] = 'BREAKOUT'
                r['score'] = 10
            elif cp > pw + (cw - pw) * 0.5:
                r['signal'] = 'NEAR_CALL'
                r['score'] = 7
            elif cp > pw * 1.02:
                r['signal'] = 'MID_CHANNEL'
                r['score'] = 5
            elif cp > pw:
                r['signal'] = 'NEAR_PUT'
                r['score'] = 8
            else:
                r['signal'] = 'BREAKDOWN'
                r['score'] = 3
            return r
        except:
            return {'call_wall': None, 'put_wall': None, 'signal': 'UNAVAILABLE', 'score': 5}

    @staticmethod
    def vix_term():
        try:
            vx = yf.Ticker('^VIX').history(period='10d', auto_adjust=True)
            v3 = yf.Ticker('^VIX3M').history(period='10d', auto_adjust=True)
            if vx.empty or v3.empty:
                return {'signal': 'NEUTRAL', 'score': 5}
            s = vx.Close.iloc[-1]
            f = v3.Close.iloc[-1]
            sl = f - s
            if sl > 2:
                sig = 'CONTANGO'
                sc = 10
            elif sl > 0:
                sig = 'WEAK_CONTANGO'
                sc = 8
            elif sl > -2:
                sig = 'NEUTRAL'
                sc = 5
            elif sl > -5:
                sig = 'WEAK_BACKWARDATION'
                sc = 3
            else:
                sig = 'BACKWARDATION'
                sc = 1
            return {'spot': round(s, 1), 'fwd': round(f, 1), 'slope': round(sl, 1), 'signal': sig, 'score': sc}
        except:
            return {'signal': 'NEUTRAL', 'score': 5}

    @staticmethod
    def xasset():
        try:
            d = {'SPY': 1, 'TLT': -1, 'GLD': -1, 'UUP': -1}
            sigs = {}
            for k, v in d.items():
                df = yf.Ticker(k).history(period='3mo', auto_adjust=True)
                if df.empty or len(df) < 50:
                    sigs[k] = 0
                    continue
                a = df.Close.iloc[-1] > df.Close.rolling(20).mean().iloc[-1]
                sigs[k] = 1 if (a and v == 1) or (not a and v == -1) else -1
            al = sum(1 for x in sigs.values() if x == 1)
            return {'aligned': al, 'score': min(al * 2 + 2, 10)}
        except:
            return {'aligned': 0, 'score': 5}

    @staticmethod
    def smi(sym):
        try:
            df = yf.Ticker(sym).history(period='6mo', auto_adjust=True)
            if df.empty or len(df) < 60:
                return {'signal': 'NO_DATA', 'score': 5}
            df = df.copy()
            df['r'] = df.Close.pct_change()
            df['v'] = df.Volume.rolling(20).mean()
            df['u'] = (df.r > 0) & (df.Volume > df.v * 0.8)
            df['d'] = (df.r < 0) & (df.Volume > df.v * 0.8)
            rc = df.tail(20)
            u = rc.u.sum()
            d = rc.d.sum()
            t = u + d
            if t == 0:
                return {'signal': 'NEUTRAL', 'score': 5}
            rt = u / t * 100
            if rt > 65:
                sig = 'STRONG_ACCUMULATION'
                sc = 10
            elif rt > 55:
                sig = 'ACCUMULATION'
                sc = 8
            elif rt < 35:
                sig = 'STRONG_DISTRIBUTION'
                sc = 2
            elif rt < 45:
                sig = 'DISTRIBUTION'
                sc = 4
            else:
                sig = 'NEUTRAL'
                sc = 5
            return {'buy': int(u), 'sell': int(d), 'ratio': round(rt, 1), 'signal': sig, 'score': sc}
        except:
            return {"signal": "ERROR", "score": 5}
    @staticmethod
    def sweep(df, cp):
        try:
            if len(df) < 20:
                return {'sweep': False, 'score': 5}
            r10 = df.tail(10)
            p20 = df.iloc[-20:-10]
            lo = r10.Low.min()
            rl = p20.Low.min()
            rh = p20.High.max()
            vr = r10.Volume.mean() / max(p20.Volume.mean(), 1)
            if cp <= rl * 0.995 and cp > lo and vr > 1.3:
                return {'sweep': True, 'type': 'BULLISH_REVERSAL', 'score': 10, 'vol_ratio': round(vr, 2)}
            if cp >= rh * 1.005 and cp < r10.High.max() and vr > 1.3:
                return {'sweep': True, 'type': 'BEARISH_REVERSAL', 'score': 10, 'vol_ratio': round(vr, 2)}
            return {'sweep': False, 'score': 5}
        except:
            return {'sweep': False, 'score': 5}

