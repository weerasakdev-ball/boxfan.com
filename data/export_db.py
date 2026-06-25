import sqlite3, json, os
BASE = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(os.path.join(BASE,'fighters.db'))
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT * FROM fighters ORDER BY name_th')
fighters = [dict(r) for r in cur.fetchall()]
cur.execute('SELECT * FROM fight_history ORDER BY fighter_id, date DESC')
history = [dict(r) for r in cur.fetchall()]
conn.close()
out = ('const FIGHTERS = '+json.dumps(fighters,ensure_ascii=False)+';\n'
       'const HISTORY  = '+json.dumps(history, ensure_ascii=False)+';\n')
open(os.path.join(BASE,'fighters_data.js'),'w',encoding='utf-8').write(out)
print(f'✅  {len(fighters)} นักมวย | {len(history)} แมตช์ → fighters_data.js')