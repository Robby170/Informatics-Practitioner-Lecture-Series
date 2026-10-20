import unittest
from herbal_screening.data import Senyawa, buat_senyawa
from herbal_screening.scoring import (pelanggaran_lipinski, pelanggaran_veber,
                                      energi_docking)
from herbal_screening.pipeline import tapis_serial, tapis_paralel


def contoh(**kw):
    d = dict(id=1, nama="X", sumber="Jahe", mw=300, logp=2, hbd=2, hba=5,
             rotb=4, tpsa=80)
    d.update(kw)
    return Senyawa(**d)


class TestScoring(unittest.TestCase):
    def test_lipinski_bersih(self):
        self.assertEqual(pelanggaran_lipinski(contoh()), 0)

    def test_lipinski_melanggar(self):
        self.assertEqual(pelanggaran_lipinski(contoh(mw=600, logp=6)), 2)

    def test_veber(self):
        self.assertEqual(pelanggaran_veber(contoh(rotb=12, tpsa=150)), 2)

    def test_deterministik(self):
        s = contoh()
        self.assertEqual(energi_docking(s, 200), energi_docking(s, 200))

    def test_data_reproducible(self):
        self.assertEqual(buat_senyawa(20, 1), buat_senyawa(20, 1))

    def test_serial_sama_dengan_paralel(self):
        data = buat_senyawa(40, 3)
        a, _ = tapis_serial(data, 100)
        b, _ = tapis_paralel(data, 100, 2)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
