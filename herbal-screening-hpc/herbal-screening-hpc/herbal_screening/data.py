"""Pembangkit data sintetis senyawa herbal.

CATATAN: data bersifat SINTETIS (acak terkontrol dengan seed) untuk tujuan
edukasi. Bukan data kimia nyata dan tidak boleh dipakai untuk klaim medis.
"""
from dataclasses import dataclass
import random

TANAMAN = ["Kunyit", "Jahe", "Temulawak", "Sambiloto", "Meniran",
           "Sirih", "Kumis Kucing", "Mengkudu", "Pegagan", "Serai"]


@dataclass(frozen=True)
class Senyawa:
    id: int
    nama: str
    sumber: str
    mw: float          # berat molekul (Da)
    logp: float        # lipofilisitas
    hbd: int           # H-bond donor
    hba: int           # H-bond acceptor
    rotb: int          # rotatable bonds
    tpsa: float        # topological polar surface area


def buat_senyawa(n: int, seed: int = 42) -> list:
    rng = random.Random(seed)
    data = []
    for i in range(n):
        data.append(Senyawa(
            id=i,
            nama=f"HRB-{i:05d}",
            sumber=rng.choice(TANAMAN),
            mw=round(max(120.0, rng.gauss(380, 110)), 2),
            logp=round(rng.gauss(2.8, 1.8), 2),
            hbd=max(0, int(rng.gauss(2.5, 1.8))),
            hba=max(0, int(rng.gauss(5.5, 2.8))),
            rotb=max(0, int(rng.gauss(5, 3))),
            tpsa=round(max(10.0, rng.gauss(85, 35)), 2),
        ))
    return data
