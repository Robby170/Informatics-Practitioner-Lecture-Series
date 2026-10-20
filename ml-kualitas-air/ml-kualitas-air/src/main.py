"""Studi kasus ML: klasifikasi kelayakan kualitas air sungai.
Alur: data mentah -> preprocessing -> split -> model -> evaluasi
      -> overfitting -> klasterisasi (unsupervised)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             ConfusionMatrixDisplay)
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from generate_data import buat_data

os.makedirs("data", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
SEED = 42

# 1. PENGUMPULAN DATA MENTAH
df = buat_data(seed=SEED)
df.to_csv("data/kualitas_air.csv", index=False)
print("=== 1. Data mentah ===")
print(df.head(), "\n")
print("Nilai hilang per kolom:\n", df.isna().sum(), "\n")

X, y = df.drop(columns="layak"), df["layak"]

# 2. SPLIT DULU (mencegah kebocoran data); preprocessing ada di dalam pipeline
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED, stratify=y)
print(f"=== 2. Split === train={len(X_train)}, test={len(X_test)}\n")


def pipeline(model):
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),  # isi nilai hilang
        ("scaler", StandardScaler()),                   # normalisasi
        ("model", model),
    ])


# 3. PEMILIHAN ALGORITMA (supervised learning - klasifikasi)
kandidat = {
    "Logistic Regression": pipeline(LogisticRegression(max_iter=1000)),
    "Decision Tree (depth=4)": pipeline(
        DecisionTreeClassifier(max_depth=4, random_state=SEED)),
}

# 4. EVALUASI
print("=== 3. Evaluasi model ===")
terbaik, skor_terbaik, nama_terbaik = None, 0, ""
for nama, m in kandidat.items():
    m.fit(X_train, y_train)
    acc = accuracy_score(y_test, m.predict(X_test))
    print(f"{nama}: akurasi test = {acc:.3f}")
    if acc > skor_terbaik:
        terbaik, skor_terbaik, nama_terbaik = m, acc, nama
print(f"\nModel terbaik: {nama_terbaik}\n")
print(classification_report(y_test, terbaik.predict(X_test),
                            target_names=["Tidak layak", "Layak"]))

fig, ax = plt.subplots(figsize=(4.5, 4))
ConfusionMatrixDisplay.from_estimator(
    terbaik, X_test, y_test, display_labels=["Tidak layak", "Layak"],
    cmap="Blues", ax=ax)
ax.set_title(f"Confusion Matrix\n{nama_terbaik}")
plt.tight_layout()
plt.savefig("outputs/confusion_matrix.png", dpi=150)
plt.close()

# 5. DEMONSTRASI OVERFITTING (kedalaman pohon vs akurasi)
depths = range(1, 21)
tr, te = [], []
for d in depths:
    m = pipeline(DecisionTreeClassifier(max_depth=d, random_state=SEED))
    m.fit(X_train, y_train)
    tr.append(m.score(X_train, y_train))
    te.append(m.score(X_test, y_test))
plt.figure(figsize=(6, 4))
plt.plot(depths, tr, "o-", label="Akurasi training")
plt.plot(depths, te, "s-", label="Akurasi testing")
plt.xlabel("Kedalaman pohon")
plt.ylabel("Akurasi")
plt.title("Overfitting: training naik, testing stagnan/turun")
plt.legend()
plt.grid(alpha=.3)
plt.tight_layout()
plt.savefig("outputs/overfitting.png", dpi=150)
plt.close()
print(f"=== 4. Overfitting === depth=20: train={tr[-1]:.3f}, "
      f"test={te[-1]:.3f} (selisih {tr[-1]-te[-1]:.3f})\n")

# 6. UNSUPERVISED: KLASTERISASI TANPA LABEL
prep = Pipeline([("imp", SimpleImputer(strategy="median")),
                 ("sc", StandardScaler())])
Xp = prep.fit_transform(X)
klaster = KMeans(n_clusters=3, n_init=10, random_state=SEED).fit_predict(Xp)
df["klaster"] = klaster
print("=== 5. Klasterisasi (K-Means, k=3) ===")
print(df.groupby("klaster")[list(X.columns)].mean().round(2), "\n")
print("Proporsi 'layak' per klaster:\n",
      df.groupby("klaster")["layak"].mean().round(2), "\n")

p2 = PCA(n_components=2, random_state=SEED).fit_transform(Xp)
plt.figure(figsize=(6, 4.5))
plt.scatter(p2[:, 0], p2[:, 1], c=klaster, cmap="viridis", s=14, alpha=.8)
plt.title("Klaster Kualitas Air (PCA 2D)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.tight_layout()
plt.savefig("outputs/klaster.png", dpi=150)
plt.close()
print("Selesai. Grafik tersimpan di folder outputs/")
