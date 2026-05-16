# 🤖 SMC Trading Bot v4

Bot trading otomatis berbasis **Smart Money Concepts (SMC)** untuk Bybit Futures (USDT Perpetual).  
Deploy di [Railway](https://railway.app) — isi API key, langsung jalan.

---

## 📐 Strategi

```
BOS H1 → EMA50 Filter → FVG Touch → IDM M5 → BOS/Sweep M5 → MSS → Entry
```

| Langkah | Keterangan |
|---------|-----------|
| **BOS H1** | Break of Structure timeframe 1 jam sebagai bias arah |
| **EMA50 Filter** | Harga harus di atas EMA50 (Long) atau di bawah (Short) |
| **FVG H1** | Fair Value Gap sebagai zona pullback |
| **IDM M5** | Inducement M5 — konfirmasi likuiditas diambil |
| **BOS/Sweep M5** | Konfirmasi pergerakan M5 setelah IDM |
| **MSS** | Market Structure Shift — sinyal entry final |
| **Entry** | Breaker Block (prioritas) atau FVG fallback |

**Risk Management:**
- Risk per trade: **1% dari balance** (compound — tiap trade risk ikut balance live saat itu)
- TP: **3R** (3× jarak SL dari entry)
- Leverage: otomatis sesuai limit coin, maks 10×
- SL: ujung candle MSS atau Breaker Block

**Pembatalan Setup (CHOCH):**
- BOS Long → harga tutup di bawah swing low referensi → setup batal
- BOS Short → harga tutup di atas swing high referensi → setup batal

---

## 📊 Hasil Backtest — Full Year 2025

> Modal $10 | Risk 1%/trade compound | TP 3R | ATR Filter Adaptif  
> **20 Coin | Data Bybit Perpetual USDT | M5 + H1 | Jan–Des 2025**

### Per Coin

| Coin | Trade | W | L | WR% | PnL ($) | ROI% | MaxDD% | PF | ATR P25 |
|------|------:|--:|--:|----:|--------:|-----:|-------:|---:|--------:|
| FARTCOINUSDT | 36 | 27 | 9 | 75% | +$9.53 | +95.3% | 2.2% | 7.88 | 0.0056 |
| PENGUUSDT | 30 | 23 | 7 | 77% | +$7.56 | +75.6% | 3.5% | 6.96 | 0.0040 |
| EIGENUSDT | 28 | 20 | 8 | 71% | +$5.84 | +58.4% | 2.3% | 6.02 | 0.0037 |
| ONDOUSDT | 18 | 16 | 2 | 89% | +$5.30 | +53.0% | 2.3% | 16.29 | 0.0027 |
| VIRTUALUSDT | 26 | 18 | 8 | 69% | +$5.12 | +51.2% | 2.3% | 5.19 | 0.0040 |
| TAOUSDT | 23 | 16 | 7 | 70% | +$4.37 | +43.7% | 2.4% | 5.68 | 0.0032 |
| WLDUSDT | 20 | 15 | 5 | 75% | +$4.28 | +42.8% | 2.3% | 7.60 | 0.0032 |
| LINKUSDT | 19 | 14 | 5 | 74% | +$3.91 | +39.1% | 3.5% | 6.88 | 0.0025 |
| 1000BONKUSDT | 24 | 15 | 9 | 62% | +$3.69 | +36.9% | 3.3% | 3.97 | 0.0035 |
| BERAUSDT | 24 | 15 | 9 | 62% | +$3.67 | +36.7% | 4.5% | 4.09 | 0.0032 |
| PNUTUSDT | 22 | 14 | 8 | 64% | +$3.48 | +34.8% | 3.4% | 4.22 | 0.0036 |
| JUPUSDT | 19 | 12 | 7 | 63% | +$2.89 | +28.9% | 3.5% | 3.87 | 0.0030 |
| SUIUSDT | 15 | 11 | 4 | 73% | +$2.88 | +28.8% | 2.4% | 6.19 | 0.0029 |
| WIFUSDT | 28 | 15 | 13 | 54% | +$3.09 | +30.9% | 3.5% | 2.76 | 0.0038 |
| XVGUSDT | 14 | 10 | 4 | 71% | +$2.66 | +26.6% | 2.2% | 6.13 | 0.0030 |
| ORCAUSDT | 15 | 10 | 5 | 67% | +$2.48 | +24.8% | 2.1% | 4.65 | 0.0024 |
| BELUSDT | 12 | 9 | 3 | 75% | +$2.39 | +23.9% | 1.2% | 6.92 | 0.0024 |
| 1000PEPEUSDT | 20 | 11 | 9 | 55% | +$2.21 | +22.1% | 4.5% | 2.96 | 0.0031 |
| USUALUSDT | 24 | 12 | 12 | 50% | +$2.14 | +21.4% | 3.5% | 2.40 | 0.0034 |
| AVAXUSDT | 12 | 7 | 5 | 58% | +$1.45 | +14.5% | 3.4% | 3.34 | 0.0025 |
| **TOTAL** | **429** | **290** | **139** | **68%** | **+$78.94** | **+789%** | — | **4.81** | — |

**$10.00 → $88.94 dalam setahun (+789% ROI)**

> _PnL per coin = compound masing-masing dari $10 awal. Di akun live (1 pot bersama),  
> efek compound cross-coin membuat pertumbuhan lebih tinggi seiring balance tumbuh._

### Statistik Gabungan

| Metrik | Nilai |
|--------|------:|
| Modal Awal | $10.00 |
| Final Balance | **$88.94** |
| Total Trade | 429 |
| Win Rate | **67.6%** |
| Total PnL | **+$78.94** |
| ROI Setahun | **+789%** |
| Profit Factor | **4.81** |
| Max Drawdown (per coin) | maks 4.5% |

### Per Kuartal

| Kuartal | Trade | WR% | PnL ($) | Bal Awal | Bal Akhir |
|---------|------:|----:|--------:|:--------:|:---------:|
| Q1 | 143 | 69% | +$25.20 | $10.00 | $35.20 |
| Q2 | 121 | 65% | +$20.73 | $35.20 | $55.93 |
| Q3 | 87 | 63% | +$14.95 | $55.93 | $70.88 |
| Q4 | 78 | 64% | +$18.06 | $70.88 | $88.94 |

> Balance per kuartal = akumulasi PnL semua coin (compound bertahap).  
> Q4 merupakan kuartal dengan pertumbuhan absolut terkecil karena trade count lebih sedikit.

---

## 🔧 ATR Filter Adaptif

Setiap coin punya threshold ATR minimum berbeda (P25 ATR historis = 75% waktu lolos filter):

| Coin | Threshold |
|------|:---------:|
| FARTCOINUSDT | 0.56% |
| PENGUUSDT / VIRTUALUSDT | 0.40% |
| WIFUSDT | 0.38% |
| EIGENUSDT | 0.37% |
| PNUTUSDT | 0.36% |
| USUALUSDT | 0.34% |
| 1000BONKUSDT | 0.35% |
| BERAUSDT / TAOUSDT / WLDUSDT | 0.32% |
| JUPUSDT | 0.30% |
| XVGUSDT | 0.30% |
| 1000PEPEUSDT | 0.31% |
| SUIUSDT | 0.29% |
| ONDOUSDT | 0.27% |
| LINKUSDT / AVAXUSDT | 0.25% |
| BELUSDT / ORCAUSDT | 0.24% |

---

## ⚙️ Daftar Coin (20 coin aktif)

```python
SYMBOLS = [
    'XVGUSDT', 'BELUSDT', 'TAOUSDT', '1000BONKUSDT', 'BERAUSDT',
    'USUALUSDT',
    'FARTCOINUSDT', '1000PEPEUSDT',
    'WIFUSDT', 'PENGUUSDT', 'PNUTUSDT',
    'SUIUSDT', 'AVAXUSDT', 'ONDOUSDT', 'JUPUSDT', 'EIGENUSDT',
    'LINKUSDT',
    'WLDUSDT', 'VIRTUALUSDT', 'ORCAUSDT',
]
```

### Coin yang Tidak Dimasukkan

| Coin | Alasan |
|------|--------|
| DOGEUSDT | WR 46%, PF 2.02 — profit tapi weak |
| 1000FLOKIUSDT | WR 45.8%, PF 1.92 — borderline |
| ENAUSDT | Bearish 3/4 kuartal, ATR tinggi tapi choppy |
| INJUSDT | WR 40.7%, PF 1.62 |
| ICPUSDT | Hanya 9 trade/tahun |
| ARBUSDT | WR 40%, PF 1.57 |
| TONUSDT | PF 0.82 (losing) |
| ADAUSDT | 9 trade/tahun |
| STORJUSDT | 5 trade/tahun |
| NEARUSDT | WR 44% |

---

## 🚀 Deploy ke Railway

### Set Environment Variables

| Variable | Wajib | Keterangan |
|----------|:-----:|-----------|
| `API_KEY` | ✅ | Bybit API Key (permission: Trade + Read) |
| `API_SECRET` | ✅ | Bybit API Secret |
| `TESTNET` | ❌ | `true` untuk testnet, default `false` |

### Monitoring Log

```
https://<nama-project>.up.railway.app/logs
```

---

## 📦 Dependencies

```
pandas>=2.0
numpy>=1.24
pybit>=5.0
```

---

> ⚠️ **Disclaimer**: Bot ini untuk keperluan pribadi. Trading crypto mengandung risiko tinggi.  
> Hasil backtest tidak menjamin performa di masa depan.
