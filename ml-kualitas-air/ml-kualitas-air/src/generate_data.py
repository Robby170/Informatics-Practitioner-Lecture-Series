"""Membuat dataset sintetis kualitas air sungai (data mentah, sengaja 'kotor')."""
import numpy as np
import pandas as pd


def buat_data(n=800, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "ph": rng.normal(7.0, 0.9, n),
        "kekeruhan_ntu": rng.gamma(2.0, 4.0, n),
        "oksigen_terlarut_mgl": rng.normal(6.0, 1.8, n),
        "suhu_c": rng.normal(27.5, 2.0, n),
        "bod_mgl": rng.gamma(2.5, 1.8, n),
        "konduktivitas_us": rng.normal(350, 120, n).clip(50),
    })
    # Aturan "layak" + noise agar tidak terlalu sempurna
    skor = (
        (df.ph.between(6.5, 8.5)).astype(int)
        + (df.kekeruhan_ntu < 10).astype(int)
        + (df.oksigen_terlarut_mgl > 5).astype(int)
        + (df.bod_mgl < 6).astype(int)
        + (df.konduktivitas_us < 500).astype(int)
    )
    layak = (skor >= 4).astype(int)
    flip = rng.random(n) < 0.07
    df["layak"] = np.where(flip, 1 - layak, layak)
    # Nilai hilang (~8%) pada fitur
    for kol in df.columns[:-1]:
        df.loc[rng.random(n) < 0.08, kol] = np.nan
    return df


if __name__ == "__main__":
    df = buat_data()
    df.to_csv("data/kualitas_air.csv", index=False)
    print("Dataset dibuat:", df.shape)
