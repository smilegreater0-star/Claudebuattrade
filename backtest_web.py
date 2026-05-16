"""
backtest_web.py — Backtest coin baru via Bybit API (tanpa file lokal)
Coins : TONUSDT, ADAUSDT, STORJUSDT, LINKUSDT, NEARUSDT
Period: Full Year 2025 (1 Jan – 31 Des)

Deploy ke Railway:
  Start command → python backtest_web.py
  Buka domain Railway → lihat progress & hasil di browser
"""

import os, threading, time
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

import numpy as np
import pandas as pd

import backtest as bt   # engine backtest dari backtest.py

# ── Config ──────────────────────────────────────────────────────────────
PORT   = int(os.environ.get('PORT', 8080))
COINS  = ['TONUSDT', 'ADAUSDT', 'STORJUSDT', 'LINKUSDT', 'NEARUSDT']

# 2025-01-01 00:00:00 UTC → 2025-12-31 23:59:59 UTC (dalam ms)
_START_MS = 1735689600000
_END_MS   = 1767225599999

# ── Global state ─────────────────────────────────────────────────────────
_lock    = threading.Lock()
_log     = []
_phase   = 'running'   # 'running' | 'done' | 'error'
_results = []


def _ts():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime('%H:%M:%S')


def _log_msg(msg: str):
    line = f"[{_ts()}] {msg}"
    print(line, flush=True)
    with _lock:
        _log.append(line)


# ── Bybit M5 fetch ───────────────────────────────────────────────────────
def fetch_bybit_m5(symbol: str) -> pd.DataFrame:
    """Fetch semua M5 candle 2025 dari Bybit API (paginasi otomatis)."""
    from pybit.unified_trading import HTTP
    session = HTTP(testnet=False)

    rows    = []
    cur_end = _END_MS
    n_call  = 0

    while True:
        for attempt in range(4):
            try:
                res  = session.get_kline(
                    symbol=symbol, category='linear', interval=5,
                    limit=1000, start=_START_MS, end=cur_end,
                )
                data = res['result']['list']   # newest-first
                break
            except Exception as e:
                wait = 2 ** attempt
                _log_msg(f"   ⚠ API error (attempt {attempt+1}): {e} — retry in {wait}s")
                time.sleep(wait)
        else:
            _log_msg("   ❌ Gagal fetch setelah 4 percobaan, hentikan.")
            break

        if not data:
            break

        for kl in data:
            ts_ms_bybit = int(kl[0])
            rows.append({
                'ts'   : pd.Timestamp(ts_ms_bybit, unit='ms'),
                'open' : float(kl[1]),
                'high' : float(kl[2]),
                'low'  : float(kl[3]),
                'close': float(kl[4]),
                'vol'  : float(kl[5]),
            })

        n_call   += 1
        oldest_ts = int(data[-1][0])   # data[-1] = candle paling lama (newest-first)
        if oldest_ts <= _START_MS:
            break
        cur_end = oldest_ts - 1
        time.sleep(0.2)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset='ts').sort_values('ts').reset_index(drop=True)
    df['ts_ms'] = df['ts'].astype('datetime64[s]').astype(np.int64)

    _log_msg(f"   {len(df):,} candle dari {n_call} API call")
    return df


# ── ATR P25 ──────────────────────────────────────────────────────────────
def calc_p25_atr(df: pd.DataFrame) -> float:
    c  = df['close'].to_numpy(float)
    h  = df['high'].to_numpy(float)
    l  = df['low'].to_numpy(float)
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)])
    atr14   = pd.Series(tr).rolling(14).mean().to_numpy()
    atr_pct = np.where(c > 0, atr14 / c, 0)[14:]
    valid   = atr_pct[atr_pct > 0]
    return float(np.percentile(valid, 25)) if len(valid) else 0.0035


# ── Diagnostic scan — hitung berapa sinyal lolos tiap tahap ──────────────
def _diagnose(symbol: str, df: pd.DataFrame, atr_thresh: float):
    """
    Scan 90 hari pertama, hitung sinyal yang lolos tiap tahap filter.
    Membantu debug kenapa 0 trade.
    """
    from backtest import (build_h1, find_last_swing_bos, calc_ema,
                          get_internal_gaps, replay_m5, check_bos_or_sweep)

    WARMUP   = 2400          # sama dengan backtest_coin
    H1_WIN   = 100
    total    = len(df)
    scan_end = min(total - 1, WARMUP + 90 * 24 * 12)  # 90 hari = 25920 candle

    c_bos = c_ema = c_fvg = c_fvg_touch = c_idm = c_bos2 = c_mss = 0
    last_bos_key = None

    i = WARMUP
    while i < scan_end:
        m5_win = df.iloc[max(0, i - H1_WIN * 12): i].reset_index(drop=True)
        df_h1  = build_h1(m5_win)
        if len(df_h1) < 52:
            i += 12; continue

        sh_h1, sl_h1 = find_last_swing_bos(df_h1)
        if not sh_h1 or not sl_h1:
            i += 12; continue

        closed_h1 = df_h1.iloc[-2]
        curr_h1   = df_h1.iloc[-1]
        is_long   = closed_h1['close'] > sh_h1[-1]['val']
        is_short  = closed_h1['close'] < sl_h1[-1]['val']
        if not (is_long or is_short):
            i += 12; continue

        stype = 'Long' if is_long else 'Short'

        # Deduplikasi BOS (sama dengan backtest_coin)
        swing_val = sh_h1[-1]['val'] if is_long else sl_h1[-1]['val']
        bos_key   = (stype, round(swing_val, 8))
        if bos_key == last_bos_key:
            i += 12; continue
        last_bos_key = bos_key

        c_bos += 1

        # EMA50 filter
        ema50 = calc_ema(df_h1['close'], 50).iloc[-1]
        if stype == 'Long'  and curr_h1['close'] < ema50: i += 12; continue
        if stype == 'Short' and curr_h1['close'] > ema50: i += 12; continue
        c_ema += 1

        # FVG exists?
        bos_idx = sl_h1[-1]['idx'] if is_long else sh_h1[-1]['idx']
        gaps    = get_internal_gaps(df_h1, stype, bos_idx)
        if not gaps:
            i += 12; continue
        c_fvg += 1

        # FVG touch? (scan 96 H1 = 96*12 M5 candle ke depan)
        scan_fvg_end = min(total - 1, i + 12 * 96)
        seg_h = df.iloc[i:scan_fvg_end]['high'].to_numpy(float)
        seg_l = df.iloc[i:scan_fvg_end]['low'].to_numpy(float)
        seg_c = df.iloc[i:scan_fvg_end]['close'].to_numpy(float)
        seg_len = len(seg_h)

        found_fvg_idx = -1
        used_fvg      = None
        for fvg in gaps:
            ft, fb = float(fvg['top']), float(fvg['bottom'])
            blk = 0
            while blk < seg_len:
                be = min(blk + 12, seg_len)
                bc = seg_c[be - 1]
                if stype == 'Long'  and bc < fb: break
                if stype == 'Short' and bc > ft: break
                if stype == 'Long'  and seg_l[blk:be].min() <= ft:
                    found_fvg_idx = i + blk; used_fvg = fvg; break
                if stype == 'Short' and seg_h[blk:be].max() >= fb:
                    found_fvg_idx = i + blk; used_fvg = fvg; break
                blk += 12
            if found_fvg_idx >= 0: break

        if found_fvg_idx < 0:
            i += 12 * 24; continue
        c_fvg_touch += 1

        # IDM?
        idm_end    = min(total - 1, found_fvg_idx + 12 * 48)
        df_m5_idm  = df.iloc[found_fvg_idx:idm_end].reset_index(drop=True)
        if len(df_m5_idm) < 5:
            i += 12; continue
        m5_state = replay_m5(df_m5_idm, stype)
        if m5_state['phase'] != 'IDM_TOUCHED':
            i += 12 * 24; continue
        c_idm += 1

        fh, fl, fts = m5_state['freeze_high'], m5_state['freeze_low'], m5_state['freeze_ts']
        freeze_mask = df['ts_ms'] == fts
        if not freeze_mask.any():
            i += 12; continue
        freeze_m5_idx = df[freeze_mask].index[0]

        # BOS/Sweep setelah IDM?
        bos2_end = min(total - 1, freeze_m5_idx + 12 * 12)
        df_bos2  = df.iloc[freeze_m5_idx:bos2_end].reset_index(drop=True)
        result   = check_bos_or_sweep(df_bos2, fh, fl, fts, stype)
        if result['trigger'] is None:
            i += 12 * 12; continue
        c_bos2 += 1

        trig_mask = df['ts_ms'] == result['ts']
        if not trig_mask.any():
            i += 12; continue
        trigger_m5_idx = df[trig_mask].index[0]

        # MSS?
        mss_end    = min(total - 1, trigger_m5_idx + 12 * 24)
        df_mss     = df.iloc[trigger_m5_idx:mss_end].reset_index(drop=True)
        mss_closes = df_mss['close'].to_numpy(float)
        hits       = (np.where(mss_closes > result['nfh'])[0] if stype == 'Long'
                      else np.where(mss_closes < result['nfl'])[0])
        if len(hits) == 0:
            i += 12 * 6; continue

        mss_c  = df_mss.iloc[hits[0]]
        body   = abs(float(mss_c['close']) - float(mss_c['open']))
        rng    = abs(float(mss_c['high'])  - float(mss_c['low']))
        if rng > 0 and body / rng < 0.30:
            # MSS body filter aktif — catat sebagai filter MSS
            c_mss += 0   # body terlalu kecil
            i += 12; continue

        c_mss += 1
        i += 12

    _log_msg(
        f"  [DIAG 90d] BOS:{c_bos} → EMA:{c_ema} → FVG:{c_fvg} "
        f"→ FVG_touch:{c_fvg_touch} → IDM:{c_idm} "
        f"→ BOS2:{c_bos2} → MSS:{c_mss}"
    )
    if c_bos == 0:
        _log_msg("  [DIAG] ⚠ Tidak ada BOS signal! Cek data atau symbol.")
    elif c_ema == 0:
        _log_msg("  [DIAG] ⚠ Semua BOS terfilter EMA50 — pasar sideways atau trending berlawanan.")
    elif c_fvg == 0:
        _log_msg("  [DIAG] ⚠ Tidak ada FVG ditemukan dalam range BOS.")
    elif c_fvg_touch == 0:
        _log_msg("  [DIAG] ⚠ FVG ada tapi tidak pernah disentuh harga.")
    elif c_idm == 0:
        _log_msg("  [DIAG] ⚠ IDM tidak selesai — tidak ada reversal setelah FVG touch.")
    elif c_bos2 == 0:
        _log_msg("  [DIAG] ⚠ Tidak ada BOS/Sweep M5 setelah IDM.")
    elif c_mss == 0:
        _log_msg("  [DIAG] ⚠ MSS filter terlalu ketat (body/range < 30%) — semua MSS ditolak.")
    else:
        _log_msg(f"  [DIAG] ✓ Pipeline OK sampai MSS ({c_mss} sinyal) — backtest full mungkin butuh waktu.")


# ── Main runner (background thread) ─────────────────────────────────────
def _run():
    global _phase, _results

    _log_msg("=" * 60)
    _log_msg("BACKTEST COIN BARU | Full Year 2025 | Modal $30 | Risk 1%")
    _log_msg(f"Coins: {', '.join(COINS)}")
    _log_msg("=" * 60)

    all_trades = []
    results    = []

    for symbol in COINS:
        _log_msg(f"\n{'─'*52}")
        _log_msg(f"▶ {symbol}")
        _log_msg("  Fetching M5 data dari Bybit API...")

        df = fetch_bybit_m5(symbol)

        if df.empty or len(df) < 3000:
            _log_msg(f"  ⚠ Data terlalu sedikit ({len(df)} candle) — "
                     f"symbol mungkin salah atau listing belum ada di 2025.")
            results.append({'symbol': symbol, 'status': 'no_data'})
            with _lock:
                _results = list(results)
            continue

        date_from = df['ts'].iloc[0].strftime('%Y-%m-%d')
        date_to   = df['ts'].iloc[-1].strftime('%Y-%m-%d')
        expected  = 365 * 24 * 12  # 105120
        missing   = max(0, expected - len(df))
        _log_msg(f"  Data: {len(df):,} candle | {date_from} → {date_to} "
                 f"| Missing: {missing:,} (~{missing/expected*100:.1f}%)")

        # ATR P25
        p25_atr = calc_p25_atr(df)
        bt.ATR_THRESHOLD[symbol] = round(p25_atr, 4)
        _log_msg(f"  ATR P25: {p25_atr*100:.3f}% → threshold = {p25_atr:.4f}")

        # Diagnostic — scan 90 hari pertama stage-by-stage
        _log_msg("  Diagnostic scan 90 hari pertama...")
        try:
            _diagnose(symbol, df, p25_atr)
        except Exception as e:
            _log_msg(f"  [DIAG] Error: {e}")

        # Full backtest
        _log_msg("  Running full backtest (1 tahun)...")
        try:
            trades, final_bal = bt.backtest_coin(symbol, df, bt.INITIAL_BALANCE)
        except Exception as e:
            import traceback
            _log_msg(f"  ❌ Error: {e}")
            _log_msg(traceback.format_exc())
            results.append({'symbol': symbol, 'status': 'error', 'p25_atr': p25_atr})
            with _lock:
                _results = list(results)
            continue

        n = len(trades)
        if n == 0:
            _log_msg("  Tidak ada trade ditemukan (full year).")
            results.append({
                'symbol': symbol, 'status': 'ok', 'trades': 0,
                'win': 0, 'loss': 0, 'wr': 0.0, 'pnl': 0.0,
                'roi': 0.0, 'max_dd': 0.0, 'pf': 0.0,
                'final_bal': bt.INITIAL_BALANCE, 'longs': 0, 'shorts': 0,
                'p25_atr': p25_atr,
            })
            with _lock:
                _results = list(results)
            continue

        wins   = [t for t in trades if t['outcome'] == 'tp']
        losses = [t for t in trades if t['outcome'] == 'sl']
        pnl    = sum(t['pnl_usd'] for t in trades)
        wr     = len(wins) / n * 100
        roi    = pnl / bt.INITIAL_BALANCE * 100

        peak = bt.INITIAL_BALANCE; cur_bal = bt.INITIAL_BALANCE; max_dd = 0.0
        for t in trades:
            cur_bal += t['pnl_usd']
            if cur_bal > peak: peak = cur_bal
            dd = (peak - cur_bal) / peak * 100
            if dd > max_dd: max_dd = dd

        gw = sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0)
        gl = abs(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0))
        pf = gw / gl if gl > 0 else 99.0

        longs  = [t for t in trades if t['type'] == 'Long']
        shorts = [t for t in trades if t['type'] == 'Short']

        _log_msg(
            f"  ✅ Trade:{n} | W:{len(wins)} L:{len(losses)} | WR:{wr:.1f}% | "
            f"PnL:${pnl:.2f} | ROI:{roi:.1f}% | MaxDD:{max_dd:.1f}% | PF:{pf:.2f}"
        )

        results.append({
            'symbol'   : symbol, 'status': 'ok',
            'trades'   : n, 'win': len(wins), 'loss': len(losses),
            'wr'       : wr, 'pnl': pnl, 'roi': roi,
            'max_dd'   : max_dd, 'pf': pf, 'final_bal': final_bal,
            'longs'    : len(longs), 'shorts': len(shorts),
            'p25_atr'  : p25_atr,
        })
        all_trades.extend(trades)

        with _lock:
            _results = list(results)

    # ── Ringkasan ──────────────────────────────────────────────────────
    _log_msg(f"\n{'='*60}")
    if all_trades:
        total_pnl = sum(t['pnl_usd'] for t in all_trades)
        total_w   = sum(1 for t in all_trades if t['outcome'] == 'tp')
        wr_all    = total_w / len(all_trades) * 100
        _log_msg(f"TOTAL: {len(all_trades)} trade | WR:{wr_all:.1f}% | PnL:${total_pnl:.2f}")
    _log_msg("✅ SELESAI — Refresh halaman untuk melihat tabel lengkap.")

    with _lock:
        _phase = 'done'


# ── HTML rendering ───────────────────────────────────────────────────────
_CSS = """
<style>
*{box-sizing:border-box}
body{font-family:'Courier New',monospace;background:#0d1117;color:#c9d1d9;
     padding:24px 32px;max-width:1100px;margin:0 auto}
h1{color:#58a6ff;font-size:20px;margin:0 0 6px}
h2{color:#79c0ff;font-size:14px;margin:22px 0 8px;text-transform:uppercase;letter-spacing:.5px}
p{margin:4px 0;font-size:13px}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
th{background:#161b22;color:#58a6ff;padding:9px 14px;text-align:left;
   border-bottom:2px solid #30363d;white-space:nowrap}
td{padding:8px 14px;border-bottom:1px solid #21262d;white-space:nowrap}
tr:hover td{background:#161b22}
.g{color:#3fb950}.r{color:#f85149}.y{color:#e3b341}
.log{background:#161b22;border:1px solid #30363d;border-radius:6px;
     padding:14px 16px;max-height:600px;overflow-y:auto;
     white-space:pre-wrap;font-size:12px;line-height:1.6}
.chip{display:inline-block;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:bold}
.chip-run{background:#1c3c5e;color:#58a6ff}
.chip-done{background:#1a3d28;color:#3fb950}
.note{background:#161b22;border-left:3px solid #58a6ff;padding:10px 14px;
      border-radius:0 6px 6px 0;font-size:12px;margin:10px 0 0;line-height:1.6}
</style>
"""


def _render_html() -> bytes:
    with _lock:
        phase  = _phase
        log_cp = list(_log)
        res_cp = list(_results)

    refresh = '<meta http-equiv="refresh" content="6">' if phase == 'running' else ''
    chip    = ('<span class="chip chip-run">⏳ Running…</span>' if phase == 'running'
               else '<span class="chip chip-done">✅ Selesai</span>')

    rows_html = ''
    for r in res_cp:
        sym     = r['symbol']
        atr_str = f"{r['p25_atr']:.4f}" if 'p25_atr' in r else '—'
        if r.get('status') in ('no_data', 'error'):
            label = '⚠ no data / symbol salah' if r['status'] == 'no_data' else '❌ error'
            rows_html += (f'<tr><td><b>{sym}</b></td>'
                          f'<td class="r" colspan="8">{label}</td></tr>\n')
        elif r.get('trades', 0) == 0:
            rows_html += (f'<tr><td><b>{sym}</b></td><td class="y">0</td>'
                          + '<td class="y">—</td>' * 6
                          + f'<td class="g">{atr_str}</td></tr>\n')
        else:
            wr_c  = 'g' if r['wr']     >= 50 else 'r'
            pnl_c = 'g' if r['pnl']    >= 0  else 'r'
            dd_c  = ('r' if r['max_dd'] > 20  else ('y' if r['max_dd'] > 10 else 'g'))
            rows_html += (
                f'<tr>'
                f'<td><b>{sym}</b></td>'
                f'<td>{r["trades"]}</td>'
                f'<td class="{wr_c}">{r["wr"]:.1f}%</td>'
                f'<td class="{pnl_c}">${r["pnl"]:.2f}</td>'
                f'<td class="{pnl_c}">{r["roi"]:.1f}%</td>'
                f'<td class="{dd_c}">{r["max_dd"]:.1f}%</td>'
                f'<td>{r["pf"]:.2f}</td>'
                f'<td>${r["final_bal"]:.2f}</td>'
                f'<td class="g">{atr_str}</td>'
                f'</tr>\n'
            )

    table_html = (f'''
        <table>
          <tr>
            <th>Coin</th><th>Trade</th><th>WR%</th><th>PnL USD</th>
            <th>ROI%</th><th>MaxDD%</th><th>PF</th>
            <th>Final Bal</th><th>ATR P25 (rec.)</th>
          </tr>
          {rows_html or '<tr><td colspan="9" class="y">Menunggu hasil pertama…</td></tr>'}
        </table>
        <div class="note">
          💡 <b>ATR P25 (rec.)</b> = nilai yang perlu dimasukkan ke
          <code>ATR_THRESHOLD</code> di <code>backtest.py</code> dan
          <code>bott_v4.py</code> untuk setiap coin yang layak ditambahkan.
          <br>
          <b>DIAG</b> = cek baris <code>[DIAG 90d]</code> di log untuk tahu
          sinyal terfilter di tahap mana jika trade = 0.
          <br>Modal: $30 &nbsp;|&nbsp; Risk: 1%/trade &nbsp;|&nbsp; TP: 3R
        </div>
    ''')

    log_html = '\n'.join(log_cp[-300:])

    return f'''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Backtest Coin Baru — SMC Bot</title>
  {_CSS}
  {refresh}
</head>
<body>
  <h1>🤖 Backtest SMC Bot — Coin Baru</h1>
  <p>
    Coins: <b>TONUSDT · ADAUSDT · STORJUSDT · LINKUSDT · NEARUSDT</b> &nbsp;|&nbsp;
    Period: <b>2025-01-01 → 2025-12-31</b> &nbsp;|&nbsp;
    Status: {chip}
  </p>

  <h2>Hasil Backtest</h2>
  {table_html}

  <h2>Log Progress</h2>
  <div class="log" id="log">{log_html}</div>
  <script>
    var el = document.getElementById('log');
    if (el) el.scrollTop = el.scrollHeight;
  </script>
</body>
</html>'''.encode('utf-8')


# ── HTTP handler ─────────────────────────────────────────────────────────
class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/logs'):
            with _lock:
                body = '\n'.join(_log).encode('utf-8')
            ctype = 'text/plain; charset=utf-8'
        else:
            body  = _render_html()
            ctype = 'text/html; charset=utf-8'

        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


# ── Entry point ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=_run, daemon=True).start()
    server = HTTPServer(('0.0.0.0', PORT), _Handler)
    print(f"🌐 Server running on port {PORT}", flush=True)
    server.serve_forever()
