const $ = (id) => document.getElementById(id);
const ambang = 25; // menit: di atas ini dianggap lama
const state = { poli: "Semua", hari: "Semua" };

const rata = (a, f) => (a.length ? a.reduce((s, x) => s + f(x), 0) / a.length : 0);
const saring = (opsi = {}) =>
  DATA.filter((d) =>
    (opsi.abaikanPoli || state.poli === "Semua" || d.poli === state.poli) &&
    (state.hari === "Semua" || d.hari === state.hari));

function isiPilihan() {
  [["f-poli", POLI, "poli"], ["f-hari", HARI, "hari"]].forEach(([id, daftar, kunci]) => {
    const el = $(id);
    ["Semua", ...daftar].forEach((n) => el.add(new Option(n === "Semua" ? "Semua " + kunci : n, n)));
    el.addEventListener("change", () => { state[kunci] = el.value; render(); });
  });
  $("reset").addEventListener("click", () => {
    state.poli = state.hari = "Semua";
    $("f-poli").value = $("f-hari").value = "Semua";
    render();
  });
}

function ringkasPoli(poli, data) {
  const d = data.filter((x) => x.poli === poli);
  return { poli, pasien: d.reduce((s, x) => s + x.pasien, 0), tunggu: Math.round(rata(d, (x) => x.tunggu)) };
}

function renderKpi() {
  const d = saring();
  $("kpi-pasien").textContent = d.reduce((s, x) => s + x.pasien, 0).toLocaleString("id-ID");
  $("kpi-tunggu").textContent = Math.round(rata(d, (x) => x.tunggu));
  const per = POLI.map((p) => ringkasPoli(p, saring({ abaikanPoli: true }))).sort((a, b) => b.tunggu - a.tunggu);
  $("kpi-sibuk").textContent = per[0].poli;
}

function renderBar() {
  const per = POLI.map((p) => ringkasPoli(p, saring({ abaikanPoli: true })));
  const maks = Math.max(...per.map((x) => x.tunggu), ambang);
  const wadah = $("bar");
  wadah.replaceChildren();
  per.forEach((x) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "bar" + (x.tunggu > ambang ? " lama" : "");
    b.setAttribute("aria-pressed", String(state.poli === x.poli));
    b.setAttribute("aria-label", `${x.poli}, ${x.tunggu} menit${x.tunggu > ambang ? ", tergolong lama" : ""}`);
    b.innerHTML = `<span></span><span class="jalur"><span class="isi"></span></span><span class="angka"></span>`;
    b.children[0].textContent = x.poli;
    b.querySelector(".isi").style.width = (x.tunggu / maks) * 100 + "%";
    b.children[2].textContent = x.tunggu + " mnt" + (x.tunggu > ambang ? " (lama)" : "");
    b.addEventListener("click", () => {
      state.poli = state.poli === x.poli ? "Semua" : x.poli;
      $("f-poli").value = state.poli;
      render();
    });
    wadah.append(b);
  });
}

function renderGaris() {
  const d = saring();
  const titik = JAM.map((j) => Math.round(rata(d.filter((x) => x.jam === j), (x) => x.tunggu)));
  $("garis-ket").textContent = `Rata-rata menit menunggu per jam. ${state.poli}, ${state.hari === "Semua" ? "semua hari" : state.hari}.`;
  const W = 600, H = 220, m = { l: 36, r: 16, t: 12, b: 28 };
  const maks = Math.ceil(Math.max(...titik, 10) / 10) * 10;
  const x = (i) => m.l + (i * (W - m.l - m.r)) / (JAM.length - 1);
  const y = (v) => H - m.b - (v / maks) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Grafik garis waktu tunggu per jam" width="100%">`;
  [0, maks / 2, maks].forEach((v) => {
    s += `<line class="g-kisi" x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}"/><text x="${m.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
  });
  s += `<polyline class="g-garis" points="${titik.map((v, i) => `${x(i)},${y(v)}`).join(" ")}"/>`;
  titik.forEach((v, i) => {
    s += `<circle class="g-titik" cx="${x(i)}" cy="${y(v)}" r="5"><title>Pukul ${JAM[i]}.00: ${v} menit</title></circle>`;
    s += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${JAM[i]}.00</text>`;
    s += `<text x="${x(i)}" y="${y(v) - 10}" text-anchor="middle">${v}</text>`;
  });
  $("garis").innerHTML = s + "</svg>";
}

function renderDetail() {
  const el = $("detail");
  if (state.poli === "Semua") {
    el.innerHTML = `<p class="petunjuk">Belum ada poli yang dipilih. Pilih salah satu poli pada daftar di atas.</p>`;
    return;
  }
  const d = saring();
  const total = d.reduce((s, x) => s + x.pasien, 0);
  const rataTunggu = Math.round(rata(d, (x) => x.tunggu));
  const perJam = JAM.map((j) => {
    const dj = d.filter((x) => x.jam === j);
    return { jam: j, pasien: dj.reduce((s, x) => s + x.pasien, 0), tunggu: Math.round(rata(dj, (x) => x.tunggu)) };
  });
  const terbaik = perJam.reduce((a, b) => (b.tunggu < a.tunggu ? b : a));
  let html = `<p><strong>${state.poli}</strong>: ${total} pasien, rata-rata menunggu ${rataTunggu} menit.</p>`;
  html += `<p class="catatan">Saran: datang sekitar pukul ${terbaik.jam}.00. Rata-rata menunggu hanya ${terbaik.tunggu} menit.</p>`;
  html += `<table><caption class="sr-only">Rincian per jam</caption><thead><tr><th scope="col">Jam</th><th scope="col">Pasien</th><th scope="col">Menunggu (mnt)</th></tr></thead><tbody>`;
  perJam.forEach((r) => (html += `<tr><th scope="row">${r.jam}.00</th><td>${r.pasien}</td><td>${r.tunggu}</td></tr>`));
  el.innerHTML = html + "</tbody></table>";
}

function render() { renderKpi(); renderBar(); renderGaris(); renderDetail(); }

// --- Evaluasi usability: System Usability Scale ---
const SUS = [
  "Saya ingin sering memakai dasbor ini.", "Dasbor ini terasa rumit tanpa perlu.",
  "Dasbor ini mudah dipakai.", "Saya butuh bantuan orang lain untuk memakainya.",
  "Fitur-fiturnya terpadu dengan baik.", "Ada terlalu banyak hal yang tidak konsisten.",
  "Kebanyakan orang akan cepat belajar memakainya.", "Dasbor ini merepotkan dipakai.",
  "Saya merasa percaya diri memakainya.", "Saya perlu belajar banyak hal sebelum bisa memakainya.",
];
function bangunSus() {
  const f = $("sus");
  SUS.forEach((t, i) => {
    const fs = document.createElement("fieldset");
    fs.innerHTML = `<legend>${i + 1}. ${t}</legend>` +
      [1, 2, 3, 4, 5].map((n) => `<label><input type="radio" name="s${i}" value="${n}"> ${n}</label>`).join("");
    f.append(fs);
  });
  f.addEventListener("change", hitungSus);
}
function hitungSus() {
  const v = SUS.map((_, i) => document.querySelector(`input[name="s${i}"]:checked`));
  if (v.some((x) => !x)) { $("sus-hasil").textContent = `Terjawab ${v.filter(Boolean).length} dari 10.`; return; }
  const skor = v.reduce((s, el, i) => s + (i % 2 === 0 ? +el.value - 1 : 5 - +el.value), 0) * 2.5;
  const ket = skor >= 68 ? "di atas rata-rata (baik)" : "di bawah rata-rata (perlu diperbaiki)";
  $("sus-hasil").textContent = `Skor SUS: ${skor} dari 100, ${ket}.`;
}

isiPilihan(); bangunSus(); render();
