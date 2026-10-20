"""Studi kasus: Klasifikasi Kelayakan Air Minum dengan Machine Learning."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             ConfusionMatrixDisplay, silhouette_score)
from src.generate_data import buat_data

os.makedirs("data", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
laporan = []
def cetak(teks=""):
    print(teks); laporan.append(teks)

# 1. PENGUMPULAN DATA
df = buat_data()
df.to_csv("data/kualitas_air.csv", index=False)
cetak(f"[1] Data: {df.shape[0]} baris, {df.shape[1]} kolom")
cetak(f"    Nilai hilang per kolom:\n{df.isna().sum()[df.isna().sum() > 0].to_string()}")

X, y = df.drop(columns="layak_minum"), df["layak_minum"]

# 2. PEMBAGIAN DATA (sebelum preprocessing -> mencegah data leakage)
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
cetak(f"[2] Split: train={len(X_tr)}, test={len(X_te)}")

# 3. PREPROCESSING + 4. MODEL (supervised learning)
def pipa(model):
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),   # isi nilai hilang
        ("scaler", StandardScaler()),                    # normalisasi
        ("model", model),
    ])

model_uji = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Decision Tree (tanpa batas)": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=150, random_state=42),
}

# 5. EVALUASI
cetak("\n[3] Evaluasi model (data uji):")
hasil = {}
for nama, m in model_uji.items():
    p = pipa(m).fit(X_tr, y_tr)
    pred = p.predict(X_te)
    hasil[nama] = (p, pred)
    cetak(f"    {nama:30s} Acc={accuracy_score(y_te, pred):.3f}  "
          f"F1={f1_score(y_te, pred):.3f}  "
          f"(train Acc={p.score(X_tr, y_tr):.3f})")

terbaik = max(hasil, key=lambda k: accuracy_score(y_te, hasil[k][1]))
cetak(f"    Model terbaik: {terbaik}")
ConfusionMatrixDisplay(confusion_matrix(y_te, hasil[terbaik][1]),
                       display_labels=["Tidak layak", "Layak"]).plot(cmap="Blues")
plt.title(f"Confusion Matrix - {terbaik}")
plt.savefig("outputs/confusion_matrix.png", dpi=130, bbox_inches="tight"); plt.close()

# 6. DEMO OVERFITTING (kedalaman pohon vs akurasi)
kedalaman = range(1, 21)
acc_tr, acc_te = [], []
for d in kedalaman:
    p = pipa(DecisionTreeClassifier(max_depth=d, random_state=42)).fit(X_tr, y_tr)
    acc_tr.append(p.score(X_tr, y_tr)); acc_te.append(p.score(X_te, y_te))
d_opt = list(kedalaman)[int(np.argmax(acc_te))]
cetak(f"\n[4] Overfitting: kedalaman optimal={d_opt} (test Acc={max(acc_te):.3f}); "
      f"kedalaman 20 -> train={acc_tr[-1]:.3f}, test={acc_te[-1]:.3f}")
plt.figure(figsize=(6, 4))
plt.plot(kedalaman, acc_tr, "o-", label="Train")
plt.plot(kedalaman, acc_te, "s-", label="Test")
plt.axvline(d_opt, ls="--", c="gray")
plt.xlabel("Kedalaman pohon"); plt.ylabel("Akurasi"); plt.legend()
plt.title("Overfitting: Train vs Test")
plt.savefig("outputs/overfitting.png", dpi=130, bbox_inches="tight"); plt.close()

# 7. UNSUPERVISED LEARNING (klasterisasi tanpa label)
prep = Pipeline([("imputer", SimpleImputer(strategy="median")),
                 ("scaler", StandardScaler())]).fit(X_tr)
X_all = prep.transform(X)
sil = {k: silhouette_score(X_all, KMeans(k, n_init=10, random_state=42).fit_predict(X_all))
       for k in range(2, 7)}
k_best = max(sil, key=sil.get)
label_k = KMeans(k_best, n_init=10, random_state=42).fit_predict(X_all)
cetak(f"\n[5] Klasterisasi K-Means: k terbaik={k_best} "
      f"(silhouette={sil[k_best]:.3f})")
xy = PCA(n_components=2, random_state=42).fit_transform(X_all)
plt.figure(figsize=(6, 4))
plt.scatter(xy[:, 0], xy[:, 1], c=label_k, cmap="viridis", s=10)
plt.title(f"Klaster K-Means (k={k_best}) - proyeksi PCA")
plt.xlabel("PC1"); plt.ylabel("PC2")
plt.savefig("outputs/klaster.png", dpi=130, bbox_inches="tight"); plt.close()

with open("outputs/hasil.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(laporan))
print("\nSelesai. Hasil tersimpan di folder outputs/")
