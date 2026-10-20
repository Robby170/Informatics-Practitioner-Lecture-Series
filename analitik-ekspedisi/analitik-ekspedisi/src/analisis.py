"""Pipeline 4 tingkat analitik: Descriptive -> Diagnostic -> Predictive -> Prescriptive."""
import hashlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

SEED = 42
OUT = "output"


# ---------- 0. PERSIAPAN DATA (60-70% pekerjaan) ----------
def siapkan_data(df):
    log = {"baris_awal": len(df)}
    df = df.drop_duplicates(subset="resi_id").copy()
    log["duplikat_dibuang"] = log["baris_awal"] - len(df)

    log["jarak_negatif_diperbaiki"] = int((df.jarak_km < 0).sum())
    df["jarak_km"] = df["jarak_km"].abs()

    df.loc[df.berat_kg > 100, "berat_kg"] = float("nan")   # anomali: mustahil >100 kg
    log["berat_hilang_diimputasi"] = int(df.berat_kg.isna().sum())
    df["berat_kg"] = df.berat_kg.fillna(df.berat_kg.median())

    # Etika privasi: hapus PII, ganti dengan hash anonim
    df["id_anonim"] = df.no_hp.map(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:8])
    df = df.drop(columns=["nama_penerima", "no_hp"])
    log["baris_bersih"] = len(df)
    return df, log


# ---------- 1. DESCRIPTIVE ----------
def descriptive(df):
    print(f"\n[DESCRIPTIVE] Tingkat keterlambatan keseluruhan: {df.telat.mean():.1%}")
    por_layanan = df.groupby("layanan").telat.mean().sort_values()
    print(por_layanan.map("{:.1%}".format).to_string())
    por_layanan.plot.bar(color="#2a6fdb", rot=0, title="Tingkat Keterlambatan per Layanan")
    plt.ylabel("Proporsi telat"); plt.tight_layout()
    plt.savefig(f"{OUT}/1_descriptive_layanan.png", dpi=120); plt.close()


# ---------- 2. DIAGNOSTIC ----------
def diagnostic(df):
    pivot = df.pivot_table(index="cuaca", columns="layanan", values="telat", aggfunc="mean")
    print("\n[DIAGNOSTIC] Telat berdasarkan cuaca x layanan:")
    print(pivot.map("{:.1%}".format).to_string())
    jam = df.assign(malam=df.jam_kirim >= 18).groupby("malam").telat.mean()
    print(f"Kirim sebelum 18.00: {jam[False]:.1%} | setelah 18.00: {jam[True]:.1%}")
    pivot.plot.bar(rot=0, title="Akar Masalah: Cuaca x Layanan")
    plt.ylabel("Proporsi telat"); plt.tight_layout()
    plt.savefig(f"{OUT}/2_diagnostic_cuaca_layanan.png", dpi=120); plt.close()


# ---------- 3. PREDICTIVE ----------
def predictive(df):
    X = pd.get_dummies(df[["jarak_km", "berat_kg", "layanan", "cuaca", "jam_kirim"]])
    y = df.telat
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=SEED, stratify=y)
    model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=SEED).fit(Xtr, ytr)
    proba = model.predict_proba(Xte)[:, 1]
    print(f"\n[PREDICTIVE] ROC-AUC: {roc_auc_score(yte, proba):.3f}")
    print(classification_report(yte, model.predict(Xte), digits=3))
    imp = pd.Series(model.feature_importances_, X.columns).sort_values().tail(8)
    imp.plot.barh(color="#e07b00", title="Faktor Paling Berpengaruh")
    plt.tight_layout(); plt.savefig(f"{OUT}/3_predictive_importance.png", dpi=120); plt.close()
    return df.loc[Xte.index].assign(prob_telat=proba)


# ---------- 4. PRESCRIPTIVE ----------
def rekomendasi(r):
    if r.cuaca == "Badai":
        return "Tunda/alihkan rute & kabari penerima"
    if r.layanan == "Reguler" and r.jarak_km > 700:
        return "Tawarkan upgrade ke Express"
    if r.jam_kirim >= 18:
        return "Jadwalkan ulang ke batch pagi"
    return "Prioritaskan di sortir (pantau manual)"


def prescriptive(hasil):
    risiko = hasil[hasil.prob_telat >= 0.6].copy()
    risiko["rekomendasi"] = risiko.apply(rekomendasi, axis=1)
    risiko.sort_values("prob_telat", ascending=False).to_csv(f"{OUT}/rekomendasi_tindakan.csv", index=False)
    print(f"\n[PRESCRIPTIVE] {len(risiko)} paket berisiko tinggi (prob >= 60%). Ringkasan tindakan:")
    print(risiko.rekomendasi.value_counts().to_string())


def main():
    raw = pd.read_csv("data/pengiriman_raw.csv")
    df, log = siapkan_data(raw)
    print("[PERSIAPAN DATA]", log)
    df.to_csv("data/pengiriman_bersih.csv", index=False)
    descriptive(df); diagnostic(df)
    prescriptive(predictive(df))


if __name__ == "__main__":
    main()
