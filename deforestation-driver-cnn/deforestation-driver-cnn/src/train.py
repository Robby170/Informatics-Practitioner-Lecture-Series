"""Pipeline lengkap: data sintetis -> latih CNN -> ablasi sensor -> analisis musiman.

Jalankan:  python -m src.train            (penuh, ~beberapa menit di CPU)
           python -m src.train --quick    (cepat, untuk uji coba)
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .cnn_numpy import CNN
from .synth_data import (CHANNELS, CLASSES, OPTICAL_IDX, SAR_IDX,
                         make_dataset, make_patch, monthly_class_probs)

OUT = "results"
COLORS = ["#c9a227", "#6b6b6b", "#b5533c", "#e07b00"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
SCENARIOS = {"Optik saja": OPTICAL_IDX, "SAR saja": SAR_IDX, "Fusi optik+SAR": list(range(6))}


def confusion(y, p, k=4):
    cm = np.zeros((k, k), int)
    np.add.at(cm, (y, p), 1)
    return cm


def f1_macro(cm):
    prec = np.diag(cm) / np.maximum(cm.sum(0), 1)
    rec = np.diag(cm) / np.maximum(cm.sum(1), 1)
    return float(np.mean(2 * prec * rec / np.maximum(prec + rec, 1e-9)))


def standardize(Xtr, *others):
    mu = Xtr.mean((0, 2, 3), keepdims=True)
    sd = Xtr.std((0, 2, 3), keepdims=True) + 1e-6
    return [(a - mu) / sd for a in (Xtr, *others)], (mu, sd)


def plot_samples(path):
    rng = np.random.default_rng(7)
    fig, ax = plt.subplots(4, 4, figsize=(8, 8))
    shows = [("nir", 1), ("swir", 2), ("vv", 4), ("vh", 5)]
    for r, c in enumerate(range(4)):
        x = make_patch(rng, c)
        for k, (nm, ch) in enumerate(shows):
            ax[r, k].imshow(x[ch], cmap="viridis")
            ax[r, k].set_xticks([]); ax[r, k].set_yticks([])
            if r == 0: ax[r, k].set_title(nm.upper())
            if k == 0: ax[r, k].set_ylabel(CLASSES[c])
    fig.suptitle("Contoh patch sintetis per kelas (kanal terpilih)")
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_cm(cm, path, title):
    cmn = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5, 4.4))
    im = ax.imshow(cmn, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(4)); ax.set_xticklabels(CLASSES, rotation=30)
    ax.set_yticks(range(4)); ax.set_yticklabels(CLASSES)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center",
                    color="white" if cmn[i, j] > 0.5 else "black")
    ax.set_xlabel("Prediksi"); ax.set_ylabel("Sebenarnya"); ax.set_title(title)
    fig.colorbar(im, fraction=0.046); fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_ablation(res, path):
    names = list(res)
    clear = [res[n]["clear"]["acc"] for n in names]
    cloud = [res[n]["cloudy"]["acc"] for n in names]
    x = np.arange(len(names)); w = 0.36
    fig, ax = plt.subplots(figsize=(6.5, 4))
    b1 = ax.bar(x - w / 2, clear, w, label="Langit cerah", color="#2f7d4f")
    b2 = ax.bar(x + w / 2, cloud, w, label="Tertutup awan", color="#7a8fa6")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height():.2f}",
                ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(names); ax.set_ylim(0, 1.1)
    ax.set_ylabel("Akurasi uji"); ax.set_title("Ablasi sensor: peran SAR saat tutupan awan")
    ax.legend(loc="lower right"); fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_monthly(counts, path):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    bottom = np.zeros(12)
    for k in range(4):
        ax.bar(BULAN, counts[:, k], bottom=bottom, label=CLASSES[k], color=COLORS[k])
        bottom += counts[:, k]
    ax.set_ylabel("Jumlah kejadian terklasifikasi")
    ax.set_title("Pola musiman pemicu deforestasi (prediksi model, data sintetis)")
    ax.legend(ncol=2, fontsize=9); fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="mode cepat (data & epoch lebih sedikit)")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    n_train, n_test, epochs, per_month = (600, 300, 6, 20) if a.quick else (2400, 800, 14, 60)
    os.makedirs(OUT, exist_ok=True)

    # 1. Data: train berisi 30% patch berawan (agar model belajar mengandalkan SAR saat perlu)
    Xtr, ytr, _ = make_dataset(n_train, a.seed, cloud_frac=0.3)
    Xte_clear, yte_clear, _ = make_dataset(n_test, a.seed + 1, cloud_frac=0.0)
    Xte_cloud, yte_cloud, _ = make_dataset(n_test, a.seed + 2, cloud_frac=1.0)
    plot_samples(f"{OUT}/contoh_patch.png")

    # 2. Ablasi sensor
    res, models = {}, {}
    for name, ch in SCENARIOS.items():
        print(f"\n== Skenario: {name}  (kanal: {[CHANNELS[i] for i in ch]})")
        (tr, te_a, te_b), stats = standardize(Xtr[:, ch], Xte_clear[:, ch], Xte_cloud[:, ch])
        t0 = time.time()
        net = CNN(in_ch=len(ch), seed=a.seed)
        hist = net.fit(tr, ytr, epochs=epochs, seed=a.seed)
        res[name] = {"train_sec": round(time.time() - t0, 1), "loss": [round(float(h), 4) for h in hist]}
        for tag, X, y in (("clear", te_a, yte_clear), ("cloudy", te_b, yte_cloud)):
            p = net.predict(X); cm = confusion(y, p)
            res[name][tag] = {"acc": float((p == y).mean()), "f1_macro": f1_macro(cm),
                              "confusion": cm.tolist()}
            print(f"  {tag:7s} acc={res[name][tag]['acc']:.3f}  F1={res[name][tag]['f1_macro']:.3f}")
        models[name] = (net, ch, stats)

    full = "Fusi optik+SAR"
    plot_cm(np.array(res[full]["clear"]["confusion"]), f"{OUT}/confusion_fusi_cerah.png",
            "Fusi optik+SAR (cerah)")
    plot_cm(np.array(res[full]["cloudy"]["confusion"]), f"{OUT}/confusion_fusi_berawan.png",
            "Fusi optik+SAR (berawan)")
    plot_ablation(res, f"{OUT}/ablasi_sensor.png")

    # 3. Analisis musiman: simulasi 1 tahun pemantauan bulanan, diklasifikasi model fusi
    net, ch, (mu, sd) = models[full]
    counts = np.zeros((12, 4), int)
    for m in range(1, 13):
        X, _, _ = make_dataset(per_month, a.seed + 100 + m, cloud_frac=0.4,
                               class_probs=monthly_class_probs(m))
        pred = net.predict((X[:, ch] - mu) / sd)
        counts[m - 1] = np.bincount(pred, minlength=4)
    plot_monthly(counts, f"{OUT}/pola_musiman.png")
    res["_monthly_counts"] = counts.tolist()

    with open(f"{OUT}/metrics.json", "w") as f:
        json.dump(res, f, indent=2)
    print(f"\nSelesai. Hasil tersimpan di ./{OUT}/")


if __name__ == "__main__":
    main()
