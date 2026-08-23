with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    text = f.read()
old = "                tdf = pd.DataFrame(tdata)\n                st.dataframe(tdf, use_container_width=True, hide_index=True)"
new_sort = '''                tdf = pd.DataFrame(tdata)
                # Apply 5-level sort: score > conf > ML match > ML conf > WR
                tdf['_score'] = tdf['Score'].astype(int)
                tdf['_conf'] = tdf['Confidence'].str.rstrip('%').astype(float)
                tdf['_ml_match'] = (
                    ((tdf['Signal'] == 'BUY') & (tdf['ML Signal'] == 'BUY')) |
                    ((tdf['Signal'] == 'SELL') & (tdf['ML Signal'] == 'SELL')) |
                    ((tdf['Signal'] == 'HOLD') & (tdf['ML Signal'] == 'HOLD'))
                ).astype(int)
                tdf['_ml_conf'] = tdf['ML Conf'].str.rstrip('%').astype(float)
                tdf['_wr'] = tdf['Win Rate'].str.rstrip('%').astype(float)
                tdf = tdf.sort_values(
                    ['_score', '_conf', '_ml_match', '_ml_conf', '_wr'],
                    ascending=[False]*5
                ).drop(columns=['_score','_conf','_ml_match','_ml_conf','_wr']).reset_index(drop=True)
                st.dataframe(tdf, use_container_width=True, hide_index=True)'''
if old in text:
    text = text.replace(old, new_sort)
    open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py','w').write(text)
    print('Sort applied to per-tab tables')
else:
    print('Not found')
import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')