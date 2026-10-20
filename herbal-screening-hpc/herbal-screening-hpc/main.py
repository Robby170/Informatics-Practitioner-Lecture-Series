"""CLI: python main.py --n 1000 --poses 5000 --benchmark"""
import argparse
import csv
import json
import os

from herbal_screening.data import buat_senyawa
from herbal_screening.pipeline import tapis_serial, tapis_paralel, peringkat


def main():
    p = argparse.ArgumentParser(description="Penapisan senyawa herbal paralel")
    p.add_argument("--n", type=int, default=1000, help="jumlah senyawa")
    p.add_argument("--poses", type=int, default=5000, help="pose per senyawa")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--benchmark", action="store_true",
                   help="bandingkan serial vs paralel")
    a = p.parse_args()

    os.makedirs("results", exist_ok=True)
    senyawa = buat_senyawa(a.n, a.seed)
    print(f"[i] {a.n} senyawa | {a.poses} pose | {a.workers} worker")

    hasil, t_par = tapis_paralel(senyawa, a.poses, a.workers)
    print(f"[+] Paralel : {t_par:.2f} detik")

    if a.benchmark:
        _, t_ser = tapis_serial(senyawa, a.poses)
        speedup = t_ser / t_par
        efisiensi = speedup / a.workers * 100
        print(f"[+] Serial  : {t_ser:.2f} detik")
        print(f"[*] Speedup : {speedup:.2f}x | Efisiensi: {efisiensi:.0f}%")
        with open("results/benchmark.json", "w") as f:
            json.dump({"n": a.n, "poses": a.poses, "workers": a.workers,
                       "serial_s": round(t_ser, 3), "paralel_s": round(t_par, 3),
                       "speedup": round(speedup, 2),
                       "efisiensi_persen": round(efisiensi, 1)}, f, indent=2)

    top = peringkat(hasil, a.top)
    with open("results/kandidat_teratas.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=top[0].keys())
        w.writeheader()
        w.writerows(top)

    print(f"\nTop {a.top} kandidat:")
    print(f"{'#':<3}{'Nama':<11}{'Sumber':<14}{'Energi':>8}{'Lip':>5}{'Ver':>5}{'Skor':>8}")
    for i, r in enumerate(top, 1):
        print(f"{i:<3}{r['nama']:<11}{r['sumber']:<14}{r['energi']:>8}"
              f"{r['lipinski']:>5}{r['veber']:>5}{r['skor']:>8}")


if __name__ == "__main__":
    main()
