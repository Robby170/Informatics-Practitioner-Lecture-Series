"""Membuat dataset sintetis kualitas air (dengan nilai hilang & noise)."""
import numpy as np
import pandas as pd

def buat_data(n=1500, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "ph": rng.normal(7.0, 1.2, n),
        "kekerasan": rng.normal(190, 40, n),
        "padatan_terlarut": rng.normal(21000, 8000, n).clip(500),
        "kloramin": rng.normal(7.0, 1.5, n),
        "sulfat": rng.normal(330, 45, n),
        "konduktivitas": rng.normal(420, 70, n),
        "karbon_organik": rng.normal(14, 3, n),
        "kekeruhan": rng.normal(3.9, 0.8, n).clip(0.1),
    })
    # Aturan "kelayakan" + noise agar tidak terlalu mudah
    skor = (
        -np.abs(df["ph"] - 7.2) * 1.2
        - df["padatan_terlarut"] / 12000
        - df["kekeruhan"] * 0.5
        - df["karbon_organik"] / 15
        - np.abs(df["kloramin"] - 7) * 0.3
        + rng.normal(0, 0.9, n)
    )
    df["layak_minum"] = (skor > np.median(skor)).astype(int)
    # Sisipkan nilai hilang (~6%) pada beberapa kolom
    for kol in ["ph", "sulfat", "kloramin"]:
        df.loc[rng.random(n) < 0.06, kol] = np.nan
    return df

if __name__ == "__main__":
    df = buat_data()
    df.to_csv("data/kualitas_air.csv", index=False)
    print(f"Dataset dibuat: {df.shape}")
