"""Membuat data sintetis pengiriman paket (seed tetap -> reproducible)."""
import numpy as np
import pandas as pd

SEED = 42
N = 3000


def main(path="data/pengiriman_raw.csv"):
    rng = np.random.default_rng(SEED)
    kota = ["Bengkulu", "Padang", "Palembang", "Jambi", "Lampung", "Medan", "Jakarta"]
    df = pd.DataFrame({
        "resi_id": [f"RSI{100000 + i}" for i in range(N)],
        "nama_penerima": [f"Penerima {rng.integers(1, 900)}" for _ in range(N)],
        "no_hp": [f"08{rng.integers(10**9, 10**10 - 1)}" for _ in range(N)],
        "kota_asal": rng.choice(kota, N),
        "jarak_km": rng.gamma(4, 150, N).round(1),
        "berat_kg": rng.gamma(2, 1.5, N).round(2),
        "layanan": rng.choice(["Reguler", "Express", "Kargo"], N, p=[.6, .25, .15]),
        "cuaca": rng.choice(["Cerah", "Hujan", "Badai"], N, p=[.6, .3, .1]),
        "jam_kirim": rng.integers(7, 22, N),
    })

    # Probabilitas telat dibangun dari aturan "dunia nyata" yang tersembunyi
    z = -2.2 + 0.0018 * df.jarak_km + 0.15 * df.berat_kg
    z += df.cuaca.map({"Cerah": 0, "Hujan": 0.7, "Badai": 1.8})
    z += df.layanan.map({"Reguler": 0.4, "Express": -0.9, "Kargo": 0.8})
    z += (df.jam_kirim >= 18) * 0.9
    df["telat"] = (rng.random(N) < 1 / (1 + np.exp(-z))).astype(int)

    # Menyuntikkan "kotoran" data agar tahap persiapan data bermakna
    df.loc[rng.choice(N, 90, replace=False), "berat_kg"] = np.nan
    df.loc[rng.choice(N, 40, replace=False), "jarak_km"] *= -1
    df.loc[rng.choice(N, 15, replace=False), "berat_kg"] = 999
    df = pd.concat([df, df.sample(60, random_state=SEED)], ignore_index=True)

    df.to_csv(path, index=False)
    print(f"Data mentah dibuat: {len(df)} baris -> {path}")


if __name__ == "__main__":
    main()
