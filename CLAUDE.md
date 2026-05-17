# SMC Trading Bot — Claude Code Instructions

Ini adalah project bot trading otomatis berbasis **Smart Money Concepts (SMC)** untuk Bybit Futures.  
Kamu adalah asisten yang membantu mengembangkan, debugging, dan backtest bot ini.

---

## File Utama

| File | Keterangan |
|------|-----------|
| `bott_v4.py` | Bot trading live — deploy di Railway |
| `backtest.py` | Engine backtest — simulasi dengan data historis M5 |
| `backtest_web.py` | Backtest via Bybit API langsung, hasil tampil di browser |
| `CLAUDE.md` | File ini — instruksi untuk Claude Code |

---

## Struktur Bot (`bott_v4.py`)

### Alur strategi SMC (Recursive IDM):
```
BOS H1 → EMA50 Filter → FVG Touch → IDM#1 M5 → BOS M5 (wajib)
  → IDM#2 dalam BOS → WAIT_MSS → MSS=Entry | BOS lagi=IDM#3 → ...
```

### Fungsi-fungsi kunci:
- `find_last_swing_bos(df)` — deteksi swing high/low dan BOS
- `get_internal_gaps(df, stype, bos_idx)` — cari FVG di dalam range BOS
- `replay_m5(df, stype)` — state machine IDM M5 (SINGLE_MOVE → KONSOLIDASI → TUNGGU_SENTUH)
- `check_bos_or_sweep(df, fh, fl, ts, stype)` — deteksi BOS/Sweep M5 setelah IDM
- `find_breaker_block(df, ts, stype)` — cari Breaker Block untuk entry
- `place_limit_order(symbol, side, entry, sl, tp)` — eksekusi order ke Bybit
- `run_bot()` — main loop, jalan setiap M5 close (5 menit)

### State machine pending setup:
```
WAIT_FVG_TOUCH → WAIT_IDM_TOUCH → WAIT_BOS_BREAK → WAIT_IDM_TOUCH → WAIT_MSS → ENTRY
                                                         ↑___________↓ (loop jika BOS lagi)
```

### Flag `inner_idm`:
- `inner_idm = False/absent` → IDM#1 → transisi ke **WAIT_BOS_BREAK** (wajib BOS dulu)
- `inner_idm = True` → IDM#2+ → transisi ke **WAIT_MSS** (bisa MSS atau BOS lagi)

### Pembatalan setup (CHOCH):
- BOS Long → swing low ditembus → setup batal
- BOS Short → swing high ditembus → setup batal

### Risk Management:
- Risk per trade: 1% dari balance (compound)
- TP: 3R (3× jarak SL)
- Leverage: otomatis sesuai limit coin, maks 10×
- Fee: 0.055% per sisi (Bybit taker)

### SYMBOLS — 22 coin aktif:
```python
SYMBOLS = [
    # Core
    'XVGUSDT', 'BELUSDT', '1000BONKUSDT', 'BERAUSDT', 'USUALUSDT',
    '1000PEPEUSDT', 'WIFUSDT', 'PENGUUSDT', 'PNUTUSDT',
    'AVAXUSDT', 'ONDOUSDT', 'EIGENUSDT', 'LINKUSDT', 'VIRTUALUSDT', 'ORCAUSDT',
    # Rehabilitasi (dibuang di strategi lama, layak di recursive IDM)
    'DOGEUSDT', 'ARBUSDT', 'NEARUSDT', 'STORJUSDT', 'ENAUSDT', 'ADAUSDT',
    # Baru
    'SHIB1000USDT',
]
```

### ATR Filter Adaptif (threshold per coin):
```python
ATR_THRESHOLD = {
    'XVGUSDT'       : 0.0030,   # P25=0.303%
    '1000PEPEUSDT'  : 0.0031,   # P25=0.306%
    '1000BONKUSDT'  : 0.0035,   # P25=0.348%
    'BELUSDT'       : 0.0024,   # P25=0.238%
    'USUALUSDT'     : 0.0034,   # P25=0.340%
    'BERAUSDT'      : 0.0032,   # P25=0.322%
    'WIFUSDT'       : 0.0038,   # P25=0.378%
    'PENGUUSDT'     : 0.0040,   # P25=0.397%
    'PNUTUSDT'      : 0.0036,   # P25=0.357%
    'AVAXUSDT'      : 0.0025,   # P25=0.251%
    'ONDOUSDT'      : 0.0027,   # P25=0.270%
    'EIGENUSDT'     : 0.0037,   # P25=0.369%
    'LINKUSDT'      : 0.0025,   # P25=0.253%
    'VIRTUALUSDT'   : 0.0040,   # P25=0.402%
    'ORCAUSDT'      : 0.0024,   # P25=0.237%
    'DOGEUSDT'      : 0.0024,   # P25=0.242%
    'ARBUSDT'       : 0.0028,   # P25=0.279%
    'NEARUSDT'      : 0.0029,   # P25=0.287%
    'STORJUSDT'     : 0.0017,   # P25=0.172%
    'ENAUSDT'       : 0.0039,   # P25=0.388%
    'ADAUSDT'       : 0.0025,   # P25=0.247%
    'SHIB1000USDT'  : 0.0020,   # P25=0.197%
}
```
> Threshold = P25 ATR historis → 75% waktu lolos filter, 25% waktu skip (sideways)
> Window: 20 candle M5 terbaru (termasuk candle MSS), ref_price = close MSS

### Environment Variables (Railway):
```
API_KEY      = Bybit API Key
API_SECRET   = Bybit API Secret
TESTNET      = false  (true untuk testnet)
PORT         = 8080   (otomatis dari Railway)
```

---

## Struktur Backtest

### `backtest.py` — engine (identik dengan logika bott_v4.py):
```python
from backtest import load_m5, backtest_coin, FILES, INITIAL_BALANCE

df = load_m5('XVGUSDT', FILES['XVGUSDT'])
trades, final_balance = backtest_coin('XVGUSDT', df, initial_balance=10.0)
```

### `backtest_web.py` — fetch data live dari Bybit API + tampil di browser:
```bash
python backtest_web.py   # buka Railway domain untuk lihat progress
# /readme  → export hasil ke markdown
# /logs    → raw log
```

### Sinkronisasi backtest ↔ live bot:
| Komponen | backtest.py | bott_v4.py |
|----------|------------|-----------|
| Strategy | Recursive IDM (for loop max 8 depth) | State machine WAIT_IDM→WAIT_BOS→WAIT_IDM→WAIT_MSS |
| ATR window | 20 candle include MSS | get_data(limit=20) |
| Volume window | 20 candle include MSS | tail(20) |
| MSS strength | body/range ≥ 30% | body/range ≥ 30% |
| Fee | 0.055% × 2 (modeled) | tidak dimodel (real Bybit yang potong) |

---

## Workflow Umum

### 1. Tambah coin baru ke bot
```python
# Di bott_v4.py — tambah ke SYMBOLS
SYMBOLS = [..., 'NEWCOINUSDT']

# Di ATR_THRESHOLD (bott_v4.py DAN backtest.py)
ATR_THRESHOLD = {
    ...
    'NEWCOINUSDT': 0.00XX,  # hasil P25 ATR dari backtest_web.py log
}
```

### 2. Cek ATR P25 coin baru
```python
import numpy as np, pandas as pd
from backtest import load_m5, FILES

df = load_m5('NEWCOIN', FILES['NEWCOIN'])
c = df['close'].to_numpy(float)
h = df['high'].to_numpy(float)
l = df['low'].to_numpy(float)
pc = np.roll(c,1); pc[0]=c[0]
tr = np.maximum.reduce([h-l, np.abs(h-pc), np.abs(l-pc)])
atr14 = pd.Series(tr).rolling(14).mean().to_numpy()
atr_pct = np.where(c>0, atr14/c*100, 0)[14:]

p25 = np.percentile(atr_pct[atr_pct>0], 25)
print(f'P25={p25:.3f}%')
# Gunakan P25 sebagai ATR_THRESHOLD untuk coin ini
```

### 3. Backtest coin baru via backtest_web.py
```python
# Edit COINS di backtest_web.py, deploy Railway
# ATR P25 dihitung otomatis dari data live Bybit
```

---

## Hasil Backtest Terkini

**Full Year 2025 | Modal $10 | Risk 1% compound | TP 3R | 22 Coin | Recursive IDM**

| Coin | Trade | WR% | PnL Compound | ROI% | MaxDD% | PF |
|------|------:|----:|-------------:|-----:|-------:|---:|
| PENGUUSDT | 64 | 50.0% | +$3,491 | +34915% | 7.6% | 2.44 |
| USUALUSDT | 53 | 43.4% | +$2,889 | +28899% | 7.2% | 1.92 |
| DOGEUSDT | 34 | 55.9% | +$2,402 | +24024% | 5.7% | 3.17 |
| VIRTUALUSDT | 58 | 48.3% | +$2,197 | +21972% | 5.5% | 2.27 |
| 1000BONKUSDT | 57 | 57.9% | +$2,100 | +21007% | 3.6% | 3.02 |
| SHIB1000USDT | 35 | 42.9% | +$1,944 | +19445% | 8.9% | 1.81 |
| EIGENUSDT | 55 | 41.8% | +$1,513 | +15134% | 12.1% | 1.82 |
| XVGUSDT | 46 | 43.5% | +$1,459 | +14597% | 5.7% | 1.90 |
| ARBUSDT | 43 | 44.2% | +$1,303 | +13036% | 6.6% | 1.89 |
| 1000PEPEUSDT | 60 | 41.7% | +$1,228 | +12286% | 6.0% | 1.74 |
| BERAUSDT | 51 | 45.1% | +$1,203 | +12040% | 3.5% | 1.96 |
| NEARUSDT | 42 | 42.9% | +$1,191 | +11914% | 5.1% | 1.83 |
| STORJUSDT | 29 | 41.4% | +$1,181 | +11819% | 3.9% | 1.70 |
| BELUSDT | 38 | 36.8% | +$1,004 | +10045% | 5.1% | 1.44 |
| ADAUSDT | 30 | 40.0% | +$729 | +7299% | 5.3% | 1.58 |
| LINKUSDT | 32 | 40.6% | +$289 | +2898% | 4.6% | 1.63 |
| ONDOUSDT | 41 | 36.6% | +$242 | +2429% | 5.7% | 1.39 |
| WIFUSDT | 74 | 43.2% | +$237 | +2374% | 7.5% | 1.78 |
| ENAUSDT | 68 | 38.2% | +$23 | +233% | 5.7% | 1.50 |
| PNUTUSDT | 61 | 52.5% | +$35 | +356% | 7.8% | 2.54 |
| ORCAUSDT | 36 | 36.1% | +$97 | +978% | 10.9% | 1.39 |
| AVAXUSDT | 34 | 47.1% | -$89 | -893% | 6.3% | 2.05 |
| **TOTAL** | **1041** | **44.5%** | **+$26,680** | **+266,809%** | — | — |

**$10 → $26,690 dalam setahun**

### Per Kuartal:
| Kuartal | Trade | WR% | PnL | Bal Awal → Akhir |
|---------|------:|----:|----:|:----------------:|
| Q1 | 271 | 40% | +$39 | $10 → $49 |
| Q2 | 280 | 54% | +$1,119 | $49 → $1,168 |
| Q3 | 245 | 42% | +$4,491 | $1,168 → $5,659 |
| Q4 | 245 | 41% | +$21,031 | $5,659 → $26,690 |

---

## Coin yang Dikeluarkan

| Coin | Alasan |
|------|--------|
| TAOUSDT | Compound -$347 meski PF 1.76 — timing buruk (loss saat balance besar) |
| FARTCOINUSDT | Compound -$71, MaxDD 13.1%, WR 36.9% — tidak cocok dengan strategi |
| SUIUSDT | WR 28.3%, PF 0.94 — satu-satunya coin net losing |
| 1000FLOKIUSDT | WR 26.9%, PF 0.88 — net losing, MaxDD 14% |
| TONUSDT | WR 30.4%, hanya 23 trade, compound negatif |
| INJUSDT | WR 30.5%, PF 1.04 — di level noise |
| ICPUSDT | WR 29.7%, PF 1.02 — di level noise |

---

## Kapasitas Bot

- Sleep per coin: 3 detik → maks ~36 coin (worst case)
- Bybit API limit: 600 req/5 menit → aman
- Railway free tier: cukup (512MB RAM, 1 vCPU)
- **Sekarang: 22 coin** — masih dalam batas nyaman

---

## Catatan Penting

1. **Selalu backtest dulu** sebelum tambah coin ke bot live
2. **ATR P25** tersedia di log backtest_web.py — langsung pakai nilai itu
3. **Recursive IDM**: IDM#1 wajib BOS dulu, IDM#2+ langsung bisa MSS atau BOS lagi
4. **inner_idm flag**: membedakan IDM#1 (→WAIT_BOS_BREAK) dari IDM#2+ (→WAIT_MSS)
5. **CHOCH**: cek dilakukan SEBELUM print apapun agar tidak ada log spurious
6. **AVAXUSDT**: PF 2.05 tapi compound negatif karena timing — **jangan dibuang**, strategy-nya profitable
7. **Compound Q4 dominan**: bukan karena WR lebih tinggi, tapi balance sudah besar → tiap 1% = lebih banyak dollar
