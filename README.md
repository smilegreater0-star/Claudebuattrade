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
> **18 Coin Aktif | Data Bybit Perpetual USDT | M5 + H1 | Jan–Des 2025**

### Per Coin

| Coin | Trade | W | L | WR% | PnL ($) | ROI% | MaxDD% | PF | ATR P25 |
|------|------:|--:|--:|----:|--------:|-----:|-------:|---:|--------:|
| FARTCOINUSDT | 50 | 34 | 16 | 68% | +$11.96 | +119.6% | 4.5% | 5.19 | 0.0056 |
| PENGUUSDT | 40 | 31 | 9 | 78% | +$11.46 | +114.6% | 4.6% | 7.19 | 0.0040 |
| EIGENUSDT | 38 | 25 | 13 | 66% | +$7.24 | +72.4% | 4.6% | 4.96 | 0.0037 |
| VIRTUALUSDT | 25 | 19 | 6 | 76% | +$5.99 | +59.9% | 2.3% | 7.45 | 0.0040 |
| BERAUSDT | 31 | 21 | 10 | 68% | +$5.92 | +59.2% | 3.5% | 5.10 | 0.0032 |
| ONDOUSDT | 22 | 17 | 5 | 77% | +$5.10 | +51.0% | 3.4% | 7.63 | 0.0027 |
| BELUSDT | 21 | 16 | 5 | 76% | +$4.67 | +46.7% | 2.4% | 7.18 | 0.0024 |
| 1000BONKUSDT | 28 | 18 | 10 | 64% | +$4.78 | +47.8% | 3.3% | 4.37 | 0.0035 |
| SUIUSDT | 22 | 16 | 6 | 73% | +$4.55 | +45.5% | 2.4% | 5.69 | 0.0029 |
| PNUTUSDT | 31 | 18 | 13 | 58% | +$4.21 | +42.1% | 3.4% | 3.29 | 0.0036 |
| USUALUSDT | 33 | 18 | 15 | 55% | +$3.87 | +38.7% | 6.7% | 2.84 | 0.0034 |
| TAOUSDT | 23 | 15 | 8 | 65% | +$3.81 | +38.1% | 4.5% | 4.73 | 0.0032 |
| 1000PEPEUSDT | 21 | 14 | 7 | 67% | +$3.61 | +36.1% | 2.3% | 4.75 | 0.0031 |
| WIFUSDT | 28 | 16 | 12 | 57% | +$3.60 | +36.0% | 4.6% | 3.16 | 0.0038 |
| LINKUSDT | 25 | 15 | 10 | 60% | +$3.47 | +34.7% | 4.7% | 3.62 | 0.0025 |
| ORCAUSDT | 21 | 13 | 8 | 62% | +$3.10 | +31.0% | 2.2% | 3.81 | 0.0024 |
| AVAXUSDT | 18 | 12 | 6 | 67% | +$3.01 | +30.1% | 2.3% | 4.80 | 0.0025 |
| XVGUSDT | 24 | 13 | 11 | 54% | +$2.62 | +26.2% | 4.7% | 2.81 | 0.0030 |
| **TOTAL** | **501** | **331** | **170** | **66%** | **+$92.97** | **+930%** | — | **5.84** | — |

**$10.00 → $102.97 dalam setahun (+930% ROI)**

> _PnL per coin = compound masing-masing dari $10 awal. Di akun live (1 pot bersama),  
> efek compound cross-coin membuat pertumbuhan jauh lebih tinggi seiring balance tumbuh._

### Statistik Gabungan

| Metrik | Nilai |
|--------|------:|
| Modal Awal | $10.00 |
| Final Balance | **$102.97** |
| Total Trade | 501 |
| Win Rate | **66.1%** |
| Total PnL | **+$92.97** |
| ROI Setahun | **+930%** |
| Profit Factor | **5.84** |
| Max Drawdown (per coin) | maks 6.7% |

### Per Kuartal (Compound 1 Pot Bersama)

| Kuartal | Trade | WR% | PnL ($) | Bal Awal | Bal Akhir |
|---------|------:|----:|--------:|:--------:|:---------:|
| Q1 | 163 | 65% | +$119.41 | $10.00 | $129.41 |
| Q2 | 156 | 69% | +$1,815.33 | $129.41 | $1,944.74 |
| Q3 | 108 | 57% | +$5,711.02 | $1,944.74 | $7,655.76 |
| Q4 | 132 | 63% | +$46,744.70 | $7,655.76 | $54,400.46 |

> Balance per kuartal = semua trade diurutkan waktu, risk 1% dari balance berjalan.  
> Ini cara kerja bot live yang sesungguhnya — tiap trade, risk ikut balance Bybit saat itu.

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
| 1000BONKUSDT | 0.35% |
| USUALUSDT | 0.34% |
| BERAUSDT / TAOUSDT | 0.32% |
| 1000PEPEUSDT | 0.31% |
| XVGUSDT | 0.30% |
| SUIUSDT | 0.29% |
| ONDOUSDT | 0.27% |
| LINKUSDT / AVAXUSDT | 0.25% |
| BELUSDT / ORCAUSDT | 0.24% |

---

## ⚙️ Daftar Coin (18 coin aktif)

```python
SYMBOLS = [
    'XVGUSDT', 'BELUSDT', 'TAOUSDT', '1000BONKUSDT', 'BERAUSDT',
    'USUALUSDT',
    'FARTCOINUSDT', '1000PEPEUSDT',
    'WIFUSDT', 'PENGUUSDT', 'PNUTUSDT',
    'SUIUSDT', 'AVAXUSDT', 'ONDOUSDT', 'EIGENUSDT',
    'LINKUSDT',
    'VIRTUALUSDT', 'ORCAUSDT',
]
```

### Coin yang Tidak Dimasukkan

| Coin | Alasan |
|------|--------|
| JUPUSDT | WR 48.4%, PF 2.16, MaxDD 7.9% — compound negatif |
| WLDUSDT | WR 48.1%, PF 2.34, MaxDD 7.7% — compound negatif |
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
