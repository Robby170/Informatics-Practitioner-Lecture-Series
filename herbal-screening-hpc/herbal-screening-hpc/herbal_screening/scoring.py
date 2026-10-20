"""Aturan drug-likeness dan simulasi docking (stand-in komputasi berat)."""
import math
import random

from .data import Senyawa


def pelanggaran_lipinski(s: Senyawa) -> int:
    """Rule of Five Lipinski: jumlah aturan yang dilanggar."""
    return sum([s.mw > 500, s.logp > 5, s.hbd > 5, s.hba > 10])


def pelanggaran_veber(s: Senyawa) -> int:
    """Aturan Veber: fleksibilitas dan polaritas molekul."""
    return sum([s.rotb > 10, s.tpsa > 140])


def energi_docking(s: Senyawa, poses: int, seed: int = 7) -> float:
    """Simulasi docking: mencari energi ikat terbaik (semakin negatif semakin baik).

    Ini BUKAN docking sungguhan. Fungsi ini sengaja berat secara CPU agar
    manfaat paralelisme terlihat. Hasilnya deterministik per senyawa.
    """
    rng = random.Random(seed * 100003 + s.id)
    dasar = -(0.5 * min(s.hbd, 4) + 0.3 * min(s.hba, 8)
              + 0.15 * max(-2.0, min(s.logp, 5.0))) - s.mw / 200.0
    terbaik = math.inf
    for k in range(poses):
        e = dasar + rng.gauss(0, 1.2) + 0.5 * math.sin(k * 0.37)
        if e < terbaik:
            terbaik = e
    return terbaik


def skor_akhir(s: Senyawa, poses: int) -> dict:
    lip, ver = pelanggaran_lipinski(s), pelanggaran_veber(s)
    energi = energi_docking(s, poses)
    skor = -energi - 1.5 * lip - 1.0 * ver   # penalti drug-likeness
    return {"id": s.id, "nama": s.nama, "sumber": s.sumber,
            "energi": round(energi, 3), "lipinski": lip, "veber": ver,
            "skor": round(skor, 3)}


def _kerja(args):
    s, poses = args
    return skor_akhir(s, poses)
