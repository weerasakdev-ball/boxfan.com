"""
BOXFAN — generate_profiles.py v3
สร้าง static HTML โปรไฟล์ self-contained (CSS ในตัว ไม่พึ่งไฟล์นอก)
ดีไซน์เหมือน profile.html ต้นฉบับ 100%
วางใน data/ รันด้วย: python data/generate_profiles.py
"""
import sqlite3, json, os, re, html as H

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
DB   = os.path.join(BASE, 'fighters.db')
OUT  = os.path.join(ROOT, 'fighters')
SITE = 'https://www.boxingfandom.com'
CLOUD = 'dpvyl7nan'

FLAGS = {
    'ไทย':'🇹🇭','ญี่ปุ่น':'🇯🇵','เกาหลีใต้':'🇰🇷','จีน':'🇨🇳',
    'บราซิล':'🇧🇷','ฟิลิปปินส์':'🇵🇭','รัสเซีย':'🇷🇺','อิตาลี':'🇮🇹',
    'ฝรั่งเศส':'🇫🇷','อังกฤษ':'🇬🇧','สหรัฐ':'🇺🇸','แคนาดา':'🇨🇦',
    'ออสเตรเลีย':'🇦🇺','เนเธอร์แลนด์':'🇳🇱','สเปน':'🇪🇸',
    'เมียนมาร์':'🇲🇲','กัมพูชา':'🇰🇭','มาเลเซีย':'🇲🇾',
    'อินโดนีเซีย':'🇮🇩','อินเดีย':'🇮🇳','มองโกเลีย':'🇲🇳',
    'คาซัคสถาน':'🇰🇿','จอร์เจีย':'🇬🇪','อุซเบกิสถาน':'🇺🇿',
    'ตุรกี':'🇹🇷','โมร็อกโก':'🇲🇦','แอลจีเรีย':'🇩🇿',
    'อาร์เจนตินา':'🇦🇷','เม็กซิโก':'🇲🇽','โคลอมเบีย':'🇨🇴',
    'เยอรมนี':'🇩🇪','โปแลนด์':'🇵🇱','ยูเครน':'🇺🇦',
    'เบลารุส':'🇧🇾','โรมาเนีย':'🇷🇴','เช็ก':'🇨🇿',
    'สวีเดน':'🇸🇪','นอร์เวย์':'🇳🇴','เดนมาร์ก':'🇩🇰',
    'ไอร์แลนด์':'🇮🇪','นิวซีแลนด์':'🇳🇿','แอฟริกาใต้':'🇿🇦',
    'ซาอุดีอาระเบีย':'🇸🇦','อิหร่าน':'🇮🇷','ปากีสถาน':'🇵🇰',
    'เวียดนาม':'🇻🇳','ลาว':'🇱🇦','สิงคโปร์':'🇸🇬',
    'เบลเยียม':'🇧🇪','ออสเตรีย':'🇦🇹','สวิตเซอร์แลนด์':'🇨🇭',
    'โปรตุเกส':'🇵🇹','กรีซ':'🇬🇷','ทาจิกิสถาน':'🇹🇯',
    'คีร์กีซสถาน':'🇰🇬','ฮ่องกง':'🇭🇰','ไต้หวัน':'🇹🇼',
}

def slug(f):
    """สร้าง slug จากชื่ออังกฤษ หรือชื่อไทยถ้าไม่มีอังกฤษ"""
    name = f.get('name_en') or f.get('name_th') or str(f['id'])
    s = name.strip()
    # English: lowercase
    if all(ord(c) < 128 or c in ' -' for c in s):
        s = s.lower()
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'[/\\:*?"<>|]', '', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

def fl(c): return FLAGS.get(c, '🏳️')
def esc(s): return H.escape(str(s)) if s else ''

def cimg(fn, size='lg'):
    if not fn: return ''
    clean = re.sub(r'\.(jpg|jpeg|png|webp)$', '', fn, flags=re.IGNORECASE)
    d = {'sm':'w_80,h_80,g_face','md':'w_160,h_160,g_face','lg':'w_300,h_375,g_north'}
    return f'https://res.cloudinary.com/{CLOUD}/image/upload/c_fill,{d.get(size,d["lg"])},f_auto,q_auto/{clean}'

# ═══ ดึง CSS จาก profile.html ต้นฉบับ ═══
# อ่านจากไฟล์จริงเพื่อให้ตรง 100%
def load_profile_css():
    """อ่าน CSS ทั้งหมดจาก profile.html ต้นฉบับ"""
    profile_path = os.path.join(ROOT, 'profile.html')
    if not os.path.exists(profile_path):
        print(f'⚠️  ไม่พบ {profile_path} — ใช้ CSS fallback')
        return None
    with open(profile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # ดึง <style>...</style> ทั้งหมด
    blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    return '\n'.join(blocks)

# ═══ ดึง CSS จาก style.css + boxfan-tokens.css ═══
def load_external_css():
    """อ่าน CSS จากไฟล์ภายนอกที่ profile.html อ้างถึง"""
    css = ''
    for fn in ['style.css', 'boxfan-tokens.css']:
        path = os.path.join(ROOT, fn)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                css += f'\n/* ── {fn} ── */\n' + f.read()
    return css


def generate(f, history, full_css, fighters_map):
    name_th = esc(f.get('name_th',''))
    name_en = esc(f.get('name_en',''))
    country = esc(f.get('country',''))
    division = esc(f.get('division',''))
    team = esc(f.get('team',''))
    wins = f.get('total_wins',0)
    losses = f.get('total_losses',0)
    nc = f.get('total_nc',0) or 0
    total = f.get('total_fights',0)
    wr = f.get('win_rate',0) or 0
    bio = esc(f.get('biography',''))
    age = f.get('age','')
    img = cimg(f.get('image_filename'),'lg')
    fid = f['id']
    s = slug(f)

    title = f'{name_th} ({name_en}) สถิตินักมวย | Boxfan' if name_en else f'{name_th} สถิตินักมวย | Boxfan'
    desc = f'{name_th} นักมวย ONE Championship {division} สถิติ {wins}W {losses}L อัตราชนะ {wr}% | Boxfan'
    canonical = f'{SITE}/fighters/{s}.html'

    past = [h for h in history if h.get('result_type') != 'upcoming']
    past.sort(key=lambda x: x.get('date',''), reverse=True)
    up = [h for h in history if h.get('result_type') == 'upcoming']
    sc = round(wins * 3 - losses * 1, 1)

    # Days since last fight
    days_rest = ''
    if past:
        from datetime import datetime, date
        try:
            last_date = datetime.strptime(past[0].get('date',''), '%Y-%m-%d').date()
            delta = (date.today() - last_date).days
            days_rest = f'<span class="htag">พัก {delta} วัน</span>'
        except: pass

    # Form bar
    form = ''
    for h in reversed(past[:10]):
        r = h.get('result_type','')
        if r == 'win': form += '<div class="fseg win">W</div>'
        elif r == 'loss': form += '<div class="fseg loss">L</div>'
        else: form += '<div class="fseg nc">NC</div>'

    # Tags
    tags = ''
    if country: tags += f'<span class="htag">{fl(f.get("country",""))} {country}</span>'
    if team: tags += f'<span class="htag">{team}</span>'
    if age: tags += f'<span class="htag">อายุ {age} ปี</span>'
    tags += f'<span class="htag htag-pts">{sc} pts</span>'
    if days_rest: tags += f' {days_rest}'

    # Physical grid
    pg = ''
    if f.get('height_ft_in'): pg += f'<div class="pitem"><div class="pval">{f["height_ft_in"]}</div><div class="plbl">ส่วนสูง</div></div>'
    if f.get('height_cm'): pg += f'<div class="pitem"><div class="pval">{f["height_cm"]}</div><div class="plbl">ซม.</div></div>'
    if f.get('weight_lbs'): pg += f'<div class="pitem"><div class="pval">{f["weight_lbs"]}</div><div class="plbl">ปอนด์</div></div>'
    if f.get('weight_kg'): pg += f'<div class="pitem"><div class="pval">{f["weight_kg"]}</div><div class="plbl">กก.</div></div>'
    pg += f'<div class="pitem accent"><div class="pval">{sc}</div><div class="plbl">คะแนน</div></div>'
    pg += f'<div class="pitem"><div class="pval">{total}</div><div class="plbl">แมตช์รวม</div></div>'

    # NC record
    nc_html = ''
    if nc > 0:
        nc_html = f'<div class="rsep">–</div><div><div class="rn n">{nc}</div><div class="rl">NC</div></div>'

    # Fight table rows
    PH_IMG = 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2250%22 height=%2250%22><rect fill=%22%23232d3b%22 width=%2250%22 height=%2250%22 rx=%228%22/></svg>'
    rows = ''
    for h in (up + past[:10]):
        r = h.get('result_type','')
        if r == 'win': badge = '<span class="bw">ชนะ</span>'
        elif r == 'loss': badge = '<span class="bl">แพ้</span>'
        elif r == 'upcoming': badge = '<span class="bu">รอผล</span>'
        else: badge = '<span class="bn">NC</span>'
        opp_name = h.get('opponent','—')
        opp = esc(opp_name)
        date = esc(h.get('date','—'))
        event = esc(h.get('event','—'))
        decision = esc(h.get('decision',''))
        rules = esc(h.get('rules',''))
        rnd = h.get('round','')
        time = h.get('time','')
        opp_country = h.get('opponent_country','')
        method = f'<span class="deco-pill">{decision}</span>' if decision else '<span class="dash">—</span>'
        if rnd: method += f'<div style="font-size:11px;color:var(--tx-3);margin-top:3px">ยก {rnd}{" · "+time if time else ""}</div>'

        # Opponent image + link lookup
        opp_f = fighters_map.get(opp_name)
        if opp_f:
            opp_img = cimg(opp_f.get('image_filename'), 'sm') or PH_IMG
            opp_slug = slug(opp_f)
            opp_link = f'../fighters/{opp_slug}.html'
            opp_td = f'''<td><div class="opp-row"><a href="{opp_link}"><img class="opp-av" src="{opp_img}" loading="lazy" alt="{opp}"></a><div><a href="{opp_link}" class="opp-name-link">{opp}</a>'''
        else:
            opp_td = f'''<td><div class="opp-row"><img class="opp-av no-link" src="{PH_IMG}" alt=""><div><span class="opp-name-nolink">{opp}</span>'''

        if opp_country and opp_country != '-':
            opp_td += f'<div style="font-size:11px;color:var(--tx-3)">{fl(opp_country)} {esc(opp_country)}</div>'
        opp_td += '</div></div></td>'

        rows += f'''<tr>
<td>{badge}</td>
{opp_td}
<td class="col-hide-sm">{method}</td>
<td class="col-hide-sm" style="color:var(--tx-3);font-size:12px">{rules or "—"}</td>
<td class="col-hide-sm" style="font-size:12px">{event}</td>
<td style="color:var(--tx-3);font-size:12px;white-space:nowrap">{date}</td>
</tr>'''

    jsonld = json.dumps({"@context":"https://schema.org","@type":"Person","name":f.get('name_th',''),"alternateName":f.get('name_en') or None,"description":f'{name_th} นักมวย ONE Championship {division}',"image":img,"url":canonical,"nationality":f.get('country') or None,"sport":"Muay Thai / Kickboxing / MMA","memberOf":{"@type":"SportsOrganization","name":"ONE Championship"}}, ensure_ascii=False)

    return f'''<!DOCTYPE html>
<html lang="th" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{name_th},{name_en},ONE Championship,{division},มวยไทย,Boxfan">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="Boxfan">
<meta property="og:locale" content="th_TH">
<meta name="twitter:card" content="summary_large_image">
<script defer src="https://cloud.umami.is/script.js" data-website-id="40ec0b51-4f08-45be-801d-9cf01fc79260"></script>
<script type="application/ld+json">{jsonld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{full_css}
</style>
</head>
<body>

<!-- UTIL BAR -->
<div class="util-bar">
  <a href="../about.html">เกี่ยวกับเรา</a>
  <a href="../contact.html">ติดต่อเรา</a>
  <a href="../blog/">บทความ</a>
  <a href="../disclaimer.html">ข้อจำกัดความรับผิด</a>
  <span class="util-bar-right">ข้อมูลโดยแฟนกีฬา · ไม่ใช่เว็บทางการ ONE Championship</span>
</div>

<!-- NAV -->
<nav class="nav">
  <a class="nav-logo" href="../index.html">
    <img src="https://res.cloudinary.com/dia2yts2f/image/upload/v1779892068/ChatGPT_Image_22_%E0%B8%A1.%E0%B8%84._2569_19_38_45.png" alt="Boxfan" onerror="this.style.display='none'">
    <div class="nav-logo-text">
      <span class="logo-main"><span>BOX</span>FAN</span>
      <span class="logo-sub">ผลมวยทุกสังเวียน</span>
    </div>
  </a>
  <div class="nav-tabs">
    <a class="nav-tab" href="../index.html">อันดับ</a>
    <a class="nav-tab" href="../rankings.html">ตารางคะแนน</a>
    <a class="nav-tab" href="../weight-classes.html">แยกตามรุ่น</a>
    <a class="nav-tab" href="../Fighters.html">นักมวยทั้งหมด</a>
    <a class="nav-tab" href="../schedule.html">โปรแกรมชก</a>
    <a class="nav-tab" href="../results.html">ผลการแข่งขัน</a>
    <a class="nav-tab" href="../compare.html">เปรียบเทียบ</a>
    <a class="nav-tab" href="../blog/">บทความ</a>
    <a class="nav-tab" href="../tierlist.html">Tier List</a>
  </div>
</nav>

<div class="page">
  <a class="back" href="../Fighters.html">← นักมวยทั้งหมด</a>

  <!-- HERO -->
  <div class="hero">
    <div class="hav-wrap">
      <img class="hav" src="{img}" alt="{name_th}" loading="eager">
      {'<div class="hflag">' + fl(f.get("country","")) + '</div>' if country else ''}
    </div>
    <div class="hinfo">
      {'<div class="hdiv">' + division + '</div>' if division else ''}
      <h1 class="hname">{name_th}</h1>
      {'<div class="hname-en">' + name_en + '</div>' if name_en else ''}
      <div class="htags">{tags}</div>
      <div class="hrec">
        <div><div class="rn w">{wins}</div><div class="rl">ชนะ</div></div>
        <div class="rsep">–</div>
        <div><div class="rn l">{losses}</div><div class="rl">แพ้</div></div>
        {nc_html}
        <div class="wr-box">
          <div class="wr-bar" style="width:96px"><div class="wr-fill" style="width:{wr}%"></div></div>
          <div style="font-size:11px;color:var(--tx-3);margin-top:5px;font-weight:600">WR {wr:.1f}%</div>
        </div>
      </div>
    </div>
  </div>

  <!-- PHYSICAL -->
  <div class="pgrid">{pg}</div>

  <!-- FORM BAR -->
  {('<div class="form-label">ฟอร์มล่าสุด ' + str(min(len(past),10)) + ' แมตช์</div><div class="fbar">' + form + '</div>') if form else ''}

  <!-- FIGHT HISTORY -->
  <div class="card" style="overflow:hidden">
    <table class="tbl"><thead><tr>
      <th>ผล</th><th>คู่ต่อสู้</th><th class="col-hide-sm">วิธี/ยก</th><th class="col-hide-sm">กติกา</th><th class="col-hide-sm">อีเวนต์</th><th>วันที่</th>
    </tr></thead><tbody>
    {rows if rows else '<tr><td colspan="6" style="padding:32px;text-align:center;color:var(--tx-3)">ยังไม่มีประวัติการชก</td></tr>'}
    </tbody></table>
  </div>

  {('<div style="margin-top:8px;font-size:12px;color:var(--tx-4);text-align:center">แสดง ' + str(min(len(past),10)+len(up)) + ' จาก ' + str(len(past)+len(up)) + ' แมตช์</div>') if len(past) > 10 else ''}

  <a class="back" href="../profile.html?id={fid}" style="margin-top:18px;background:var(--red);color:#fff;border-color:var(--red)">ดูข้อมูลเต็ม + เปรียบเทียบสถิติ →</a>

  {('<div style="margin-top:18px;padding:24px;background:var(--surf);border:1px solid var(--line-2);border-radius:11px;box-shadow:var(--sh-2)"><div style="font-family:var(--sans);font-size:15px;font-weight:800;color:var(--tx);margin-bottom:12px;display:flex;align-items:center;gap:8px;text-transform:uppercase"><span style="color:var(--gold)">★</span> ประวัตินักมวย</div><p style="line-height:1.9;color:var(--tx-2);font-size:14px;margin:0">' + bio + '</p></div>') if bio else ''}
</div>

<!-- FOOTER -->
<footer style="border-top:1px solid var(--line);background:var(--footer-bg);margin-top:30px">
  <div style="max-width:1100px;margin:0 auto;padding:30px 26px;text-align:center">
    <div style="font-family:var(--sans);font-weight:800;font-size:24px;color:var(--tx);text-transform:uppercase">BOX<span style="color:var(--red)">FAN</span></div>
    <div style="font-size:10px;color:var(--tx-4);font-weight:700;letter-spacing:.26em;text-transform:uppercase;margin-top:2px">ผลมวยทุกสังเวียน</div>
    <div style="margin:16px 0 10px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px 18px">
      <a href="../about.html" style="font-size:13px;color:var(--tx-2);font-weight:500">เกี่ยวกับเรา</a>
      <a href="../contact.html" style="font-size:13px;color:var(--tx-2);font-weight:500">ติดต่อเรา</a>
      <a href="../privacy.html" style="font-size:13px;color:var(--tx-2);font-weight:500">นโยบายความเป็นส่วนตัว</a>
      <a href="../disclaimer.html" style="font-size:13px;color:var(--tx-2);font-weight:500">ข้อจำกัดความรับผิด</a>
    </div>
    <div style="font-size:11.5px;color:var(--tx-4)">© 2025 Boxfan · รวมผลมวยจากทุกรายการ บันทึกโดยแฟนมวย</div>
  </div>
</footer>

<script>
(function(){{try{{var s=localStorage.getItem('boxfan-theme');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}}catch(e){{}}}})();
</script>
</body>
</html>'''


def main():
    if not os.path.exists(DB):
        print(f'❌  ไม่พบ {DB}'); return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM fighters ORDER BY name_th')
    fighters = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM fight_history ORDER BY fighter_id, date DESC')
    all_history = [dict(r) for r in cur.fetchall()]
    conn.close()

    hmap = {}
    for h in all_history:
        fid = h.get('fighter_id')
        if fid not in hmap: hmap[fid] = []
        hmap[fid].append(h)

    # โหลด CSS จาก profile.html + style.css + boxfan-tokens.css
    profile_css = load_profile_css() or ''
    external_css = load_external_css()
    full_css = external_css + '\n' + profile_css

    # สร้าง map ชื่อ → fighter object สำหรับหารูปคู่ต่อสู้
    fighters_map = {}
    for ff in fighters:
        if ff.get('name_th'): fighters_map[ff['name_th']] = ff
        if ff.get('name_en'): fighters_map[ff['name_en']] = ff

    os.makedirs(OUT, exist_ok=True)
    old = [x for x in os.listdir(OUT) if x.endswith('.html')]
    for x in old: os.remove(os.path.join(OUT, x))
    if old: print(f'🧹  ลบไฟล์เก่า {len(old)} ไฟล์')

    count = 0
    for f in fighters:
        s = slug(f)
        path = os.path.join(OUT, f'{s}.html')
        content = generate(f, hmap.get(f['id'], []), full_css, fighters_map)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
        count += 1

    print(f'✅  สร้าง {count} หน้านักมวย → fighters/')

if __name__ == '__main__':
    main()