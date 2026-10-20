"""Generator data sintetis patch satelit 16x16 piksel dengan 6 kanal.

Kanal (urutan tetap):
    0 red         reflektansi optik (Sentinel-2 B4)
    1 nir         reflektansi optik (Sentinel-2 B8)
    2 swir        reflektansi optik (Sentinel-2 B11)
    3 ndvi_change selisih NDVI sesudah - sebelum kejadian
    4 vv          backscatter SAR VV dalam dB (Sentinel-1)
    5 vh          backscatter SAR VH dalam dB (Sentinel-1)

Kanal 0-3 = optik (rentan awan), kanal 4-5 = SAR (tembus awan).

Kelas pemicu deforestasi:
    0 pertanian | 1 jalan | 2 pertambangan | 3 kebakaran
"""
import numpy as np
from scipy.ndimage import gaussian_filter

CLASSES = ["pertanian", "jalan", "pertambangan", "kebakaran"]
CHANNELS = ["red", "nir", "swir", "ndvi_change", "vv", "vh"]
OPTICAL_IDX = [0, 1, 2, 3]
SAR_IDX = [4, 5]
SIZE = 16

# Nilai hutan sehat (latar belakang)
FOREST = dict(red=0.04, nir=0.45, swir=0.15, ndvi_change=0.0, vv=-7.0, vh=-13.0)

# Nilai rata-rata area terdampak per kelas (dibuat sengaja tumpang-tindih sebagian)
SIGNATURE = {
    0: dict(red=0.18, nir=0.30, swir=0.28, ndvi_change=-0.35, vv=-10.5, vh=-17.0),
    1: dict(red=0.24, nir=0.26, swir=0.34, ndvi_change=-0.55, vv=-13.5, vh=-20.0),
    2: dict(red=0.28, nir=0.29, swir=0.40, ndvi_change=-0.60, vv=-5.5, vh=-12.0),
    3: dict(red=0.09, nir=0.13, swir=0.27, ndvi_change=-0.50, vv=-9.0, vh=-15.5),
}


def _blob(rng, smooth, thresh_q):
    """Bentuk tidak beraturan: noise yang dihaluskan lalu di-threshold."""
    z = gaussian_filter(rng.normal(size=(SIZE, SIZE)), smooth)
    return z > np.quantile(z, 1 - thresh_q)


def _mask(rng, cls):
    m = np.zeros((SIZE, SIZE), bool)
    if cls == 0:  # pertanian: persegi panjang sejajar sumbu (petak ladang)
        for _ in range(rng.integers(1, 3)):
            h, w = rng.integers(5, 11, size=2)
            y, x = rng.integers(0, SIZE - h), rng.integers(0, SIZE - w)
            m[y:y + h, x:x + w] = True
    elif cls == 1:  # jalan: garis tipis dengan sudut acak
        ang = rng.uniform(0, np.pi)
        cy, cx = rng.uniform(5, 11, size=2)
        yy, xx = np.mgrid[0:SIZE, 0:SIZE]
        dist = np.abs((xx - cx) * np.sin(ang) - (yy - cy) * np.cos(ang))
        m = dist < rng.uniform(0.8, 1.6)
    elif cls == 2:  # tambang: area besar tidak beraturan dengan tepi tegas
        m = _blob(rng, smooth=2.5, thresh_q=rng.uniform(0.30, 0.50))
    else:  # kebakaran: area tidak beraturan dengan tepi berbulu
        m = _blob(rng, smooth=1.6, thresh_q=rng.uniform(0.25, 0.55))
    return m


def make_patch(rng, cls, cloudy=False):
    m = _mask(rng, cls)
    soft = gaussian_filter(m.astype(float), 0.6)  # piksel campuran di tepi
    gain = rng.normal(1.0, 0.25)                  # variasi kecerahan antar-scene
    x = np.zeros((6, SIZE, SIZE), np.float32)
    for i, name in enumerate(CHANNELS):
        bg, fg = FOREST[name], SIGNATURE[cls][name]
        if name in ("red", "nir", "swir"):
            fg = bg + (fg - bg) * gain
        base = bg + (fg - bg) * soft
        if name in ("vv", "vh"):  # speckle SAR: derau multiplikatif -> aditif di dB
            noise = rng.normal(0, 3.4, (SIZE, SIZE))
        elif name == "ndvi_change":
            noise = rng.normal(0, 0.22, (SIZE, SIZE))
        else:
            noise = rng.normal(0, 0.06, (SIZE, SIZE))
        x[i] = base + noise
    if cloudy:  # awan menutup seluruh patch optik; SAR tetap bersih
        cloud = gaussian_filter(rng.normal(size=(SIZE, SIZE)), 3) * 0.6
        x[0] = 0.45 + cloud + rng.normal(0, 0.03, (SIZE, SIZE))
        x[1] = 0.48 + cloud + rng.normal(0, 0.03, (SIZE, SIZE))
        x[2] = 0.38 + cloud + rng.normal(0, 0.03, (SIZE, SIZE))
        x[3] = rng.normal(0, 0.15, (SIZE, SIZE))
    return x


def make_dataset(n, seed, cloud_frac=0.0, class_probs=None):
    rng = np.random.default_rng(seed)
    p = np.full(4, 0.25) if class_probs is None else np.asarray(class_probs)
    y = rng.choice(4, size=n, p=p / p.sum())
    cloudy = rng.random(n) < cloud_frac
    X = np.stack([make_patch(rng, c, cl) for c, cl in zip(y, cloudy)])
    return X, y.astype(np.int64), cloudy


def monthly_class_probs(month):
    """Prior musiman (Indonesia): kebakaran puncak di musim kemarau Agu-Okt."""
    fire = {8: 0.40, 9: 0.55, 10: 0.45, 7: 0.25, 11: 0.15}.get(month, 0.05)
    rest = (1 - fire) / 3
    return np.array([rest * 1.2, rest * 0.8, rest, fire])
