// Port a JavaScript del motor de inferencia de chatbot.py (misma lógica).
function normalizar(texto) {
  return texto.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "")
    .replace(/[^a-z0-9ñ ]+/g, " ").replace(/\s+/g, " ").trim();
}

class MotorInferencia {
  constructor(kb, umbral = 3) { this.kb = kb; this.umbral = umbral; }

  puntaje(pregunta, keywords) {
    const texto = ` ${pregunta} `;
    return keywords.reduce((a, k) => a + (texto.includes(` ${k} `) ? k.length : 0), 0);
  }

  fuentesDe(clave) {
    return clave.map(c => ({ clave: c, texto: this.kb.fuentes[c] }));
  }

  responder(pregunta) {
    const q = normalizar(pregunta);
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
