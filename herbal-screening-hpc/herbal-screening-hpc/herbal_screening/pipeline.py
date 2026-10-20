"""Pipeline penapisan: versi serial dan paralel."""
import time
from multiprocessing import Pool

from .scoring import _kerja


def tapis_serial(senyawa, poses):
    t0 = time.perf_counter()
    hasil = [_kerja((s, poses)) for s in senyawa]
    return hasil, time.perf_counter() - t0


def tapis_paralel(senyawa, poses, workers):
    t0 = time.perf_counter()
    tugas = [(s, poses) for s in senyawa]
    chunk = max(1, len(tugas) // (workers * 4))
    with Pool(processes=workers) as pool:
        hasil = list(pool.imap(_kerja, tugas, chunksize=chunk))
    return hasil, time.perf_counter() - t0


def peringkat(hasil, top):
    return sorted(hasil, key=lambda r: r["skor"], reverse=True)[:top]
