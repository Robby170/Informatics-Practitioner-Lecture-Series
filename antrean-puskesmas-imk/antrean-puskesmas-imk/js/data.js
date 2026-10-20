// Data simulasi (fiktif) antrean 4 poli selama 6 hari kerja.
// Dibangkitkan dengan generator acak berbenih supaya hasilnya selalu sama.
const POLI = ["Poli Umum", "Poli Gigi", "KIA", "Lansia"];
const HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
const JAM = [8, 9, 10, 11, 12, 13];

function buatData() {
  let seed = 2026;
  const acak = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const dasarPasien = [30, 14, 18, 12];
  const faktorJam = [0.9, 1.2, 1.3, 1.0, 0.5, 0.6];
  const faktorHari = [1.3, 1.0, 0.95, 0.9, 0.8, 0.7];
  const baris = [];
  POLI.forEach((poli, p) => {
    HARI.forEach((hari, h) => {
      JAM.forEach((jam, j) => {
        const pasien = Math.round(dasarPasien[p] * faktorJam[j] * faktorHari[h] * (0.85 + acak() * 0.3));
        const tunggu = Math.round(5 + pasien * (p === 0 ? 1.1 : 0.8) + acak() * 6);
        baris.push({ poli, hari, jam, pasien, tunggu });
      });
    });
  });
  return baris;
}
const DATA = buatData();
