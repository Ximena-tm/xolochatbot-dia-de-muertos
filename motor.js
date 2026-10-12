// Port a JavaScript de chatbot.py (misma lógica). La base de conocimientos es un ÁRBOL isa de marcos.
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
    this.nodos = {}; this.padre = {};
    this.indexar(kb.arbol, null);
    const listas = [kb.fallback.fuera_de_dominio.keywords]
      .concat(Object.values(this.nodos).map(n => n.keywords))
      .concat(((kb.cortesia || {}).reglas || []).map(r => r.keywords));
    this.vocab = new Set(listas.flat().flatMap(k => k.split(" ")));
  }

  // ---------- el árbol ----------
  indexar(nodo, padre) {
    this.nodos[nodo.id] = nodo; this.padre[nodo.id] = padre;
    (nodo.hijos || []).forEach(h => this.indexar(h, nodo.id));
  }

  ruta(id) {
    const camino = [];
    while (id) { camino.unshift(id); id = this.padre[id]; }
    return camino;
  }

  // Propiedad de herencia: si el nodo no tiene el slot, sube por isa al padre.
  heredar(id, slot) {
    while (id) {
      if (slot in this.nodos[id]) return this.nodos[id][slot];
      id = this.padre[id];
    }
    return null;
  }

  // ---------- lenguaje ----------
  // Corrige errores de ortografía: máx. 1 error (2 si la palabra tiene 9+ letras).
  corregir(pregunta) {
    return pregunta.split(" ").map(w => {
      if (this.vocab.has(w) || w.length < 5) return w;
      const tope = w.length >= 9 ? 2 : 1;
      let mejor = w, mejorD = tope + 1;
      for (const v of this.vocab) {
        if (v[0] !== w[0] || Math.abs(v.length - w.length) > tope) continue;
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

  // Quita frases de cortesía ("gracias", "por favor") para que no estorben al buscar.
  quitarCortesia(q) {
    let reglaC = null;
    for (const regla of (this.kb.cortesia || {}).reglas || []) {
      for (const k of [...regla.keywords].sort((a, b) => b.length - a.length)) {
        if (` ${q} `.includes(` ${k} `)) {
          q = ` ${q} `.split(` ${k} `).join(" ");
          reglaC = reglaC || regla;
        }
      }
    }
    return { q: q.replace(/\s+/g, " ").trim(), cortesia: reglaC };
  }

  // ---------- búsqueda en el árbol ----------
  mejorEnSubarbol(nodo, q) {
    let mejor = this.puntaje(q, nodo.keywords);
    for (const h of nodo.hijos || []) mejor = Math.max(mejor, this.mejorEnSubarbol(h, q));
    return mejor;
  }

  // Baja desde la raíz: entra al hijo cuyo subárbol puntúa más, mientras supere al propio nodo.
  buscar(q) {
    let nodo = this.kb.arbol;
    for (;;) {
      const propio = this.puntaje(q, nodo.keywords);
      let mejorHijo = null, mejorP = 0;
      for (const h of nodo.hijos || []) {
        const p = this.mejorEnSubarbol(h, q);
        if (p > mejorP) { mejorHijo = h; mejorP = p; }
      }
      if (!mejorHijo || mejorP <= propio) return { id: nodo.id, puntaje: propio };
      nodo = mejorHijo;
    }
  }

  fuentesDe(claves) {
    return claves.map(c => ({ clave: c, texto: this.kb.fuentes[c] }));
  }

  // Resultado de visitar un nodo (por búsqueda o por tocar un botón del menú).
  abrir(id) {
    const n = this.nodos[id];
    return {
      respuesta: n.respuesta, detalle: n.detalle || null,
      fuentes: this.fuentesDe(this.heredar(id, "fuentes") || []),
      aviso: this.heredar(id, "aviso"), icono: this.heredar(id, "icono"),
      regla: id, ruta: this.ruta(id),
      padre: this.padre[id],
      hijos: (n.hijos || []).filter(h => !h.oculto).map(h => ({ id: h.id, etiqueta: h.etiqueta, icono: this.heredar(h.id, "icono") }))
    };
  }

  simple(respuesta, fuentes, regla) {
    return { respuesta, detalle: null, fuentes, aviso: null, icono: null, regla, ruta: [], padre: null, hijos: [] };
  }

  responder(pregunta) {
    const { q, cortesia } = this.quitarCortesia(this.corregir(normalizar(pregunta)));
    const fb = this.kb.fallback;
    if (this.puntaje(q, fb.fuera_de_dominio.keywords) > 0)
      return this.simple(fb.fuera_de_dominio.respuesta, [], "fuera_de_dominio");
    const op = fb.otros_paises;
    if (op && this.puntaje(q, op.keywords) > 0)
      return this.simple(op.respuesta, this.fuentesDe(op.fuentes), "otros_paises");
    const { id, puntaje } = this.buscar(q);
    if (puntaje < this.umbral) {
      if (cortesia) return this.simple(cortesia.respuesta, [], cortesia.id);
      return this.simple(fb.sin_coincidencia.respuesta, [], "sin_coincidencia");
    }
    return this.abrir(id);
  }
}

if (typeof module !== "undefined") module.exports = { normalizar, MotorInferencia };
