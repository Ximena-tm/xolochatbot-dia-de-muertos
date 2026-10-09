// Port a JavaScript del motor de inferencia de chatbot.py (misma lógica).
function normalizar(texto) {
  return texto.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "")
    .replace(/[^a-z0-9ñ ]+/g, " ").replace(/\s+/g, " ").trim();
}

function distancia(a, b) {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 0; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const c = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1])
        d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
    }
  }
  return d[a.length][b.length];
}

class MotorInferencia {
  constructor(kb, umbral = 3) {
    this.kb = kb; this.umbral = umbral;
    const listas = [kb.fallback.fuera_de_dominio.keywords]
      .concat(kb.reglas.map(r => r.keywords))
      .concat(((kb.personaje || {}).reglas || []).map(r => r.keywords));
    this.vocab = new Set(listas.flat().flatMap(k => k.split(" ")));
  }

  // Corrige errores de ortografía: máx. 1 error (2 si la palabra tiene 9+ letras).
  corregir(pregunta) {
    return pregunta.split(" ").map(w => {
      if (this.vocab.has(w) || w.length < 4) return w;
      const tope = w.length >= 9 ? 2 : 1;
      let mejor = w, mejorD = tope + 1;
      for (const v of this.vocab) {
        if (v.length < 4 || Math.abs(v.length - w.length) > tope) continue;
        const d = distancia(w, v);
        if (d < mejorD) { mejor = v; mejorD = d; }
      }
      return mejor;
    }).join(" ");
  }

  puntaje(pregunta, keywords) {
    const texto = ` ${pregunta} `;
    return keywords.reduce((a, k) => a + (texto.includes(` ${k} `) ? k.length : 0), 0);
  }

  fuentesDe(clave) {
    return clave.map(c => ({ clave: c, texto: this.kb.fuentes[c] }));
  }

  responder(pregunta) {
    const q = this.corregir(normalizar(pregunta));
    const fb = this.kb.fallback;
    if (this.puntaje(q, fb.fuera_de_dominio.keywords) > 0)
      return { respuesta: fb.fuera_de_dominio.respuesta, fuentes: [], regla: "fuera_de_dominio" };
    const reglas = this.kb.reglas.concat((this.kb.personaje || {}).reglas || []);
    let mejor = null, mejorP = 0;
    for (const r of reglas) {
      const p = this.puntaje(q, r.keywords);
      if (p > mejorP) { mejor = r; mejorP = p; }
    }
    if (!mejor || mejorP < this.umbral)
      return { respuesta: fb.sin_coincidencia.respuesta, fuentes: [], regla: "sin_coincidencia" };
    return { respuesta: mejor.respuesta, fuentes: this.fuentesDe(mejor.fuentes || []), regla: mejor.id };
  }
}

if (typeof module !== "undefined") module.exports = { normalizar, MotorInferencia };
