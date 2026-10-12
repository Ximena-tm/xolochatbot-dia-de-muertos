"""Xolo: chatbot experto sobre Día de Muertos.
La base de conocimientos es un ÁRBOL de marcos (slot-and-filler) unidos por la relación isa."""
import json
import re
import unicodedata


def normalizar(texto):
    """Minúsculas, sin acentos ni signos de puntuación."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9ñ ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def distancia(a, b):
    """Distancia de edición (Damerau-Levenshtein simplificada)."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


class MotorInferencia:
    def __init__(self, ruta="base_conocimientos.json", umbral=3):
        with open(ruta, encoding="utf-8") as f:
            self.kb = json.load(f)
        self.umbral = umbral
        self.nodos, self.padre = {}, {}
        self._indexar(self.kb["arbol"], None)
        self.vocab = self._construir_vocab()

    # ---------- el árbol ----------
    def _indexar(self, nodo, padre):
        """Guarda cada nodo por id y recuerda su padre (su enlace isa)."""
        self.nodos[nodo["id"]] = nodo
        self.padre[nodo["id"]] = padre
        for h in nodo.get("hijos", []):
            self._indexar(h, nodo["id"])

    def ruta(self, id_):
        """Camino desde la raíz hasta el nodo: ['dia_de_muertos', 'ofrenda', ...]."""
        camino = []
        while id_:
            camino.insert(0, id_)
            id_ = self.padre[id_]
        return camino

    def heredar(self, id_, slot):
        """Propiedad de herencia: busca el valor del slot en el nodo; si no lo tiene,
        sube por isa al padre y repite. Si llega a la raíz sin valor, devuelve None."""
        while id_:
            nodo = self.nodos[id_]
            if slot in nodo:
                return nodo[slot]
            id_ = self.padre[id_]
        return None

    def _construir_vocab(self):
        """Todas las palabras que aparecen en alguna keyword."""
        listas = [self.kb["fallback"]["fuera_de_dominio"]["keywords"]]
        listas += [n["keywords"] for n in self.nodos.values()]
        listas += [r["keywords"] for r in self.kb.get("cortesia", {}).get("reglas", [])]
        return {w for kws in listas for k in kws for w in k.split()}

    # ---------- lenguaje ----------
    def corregir(self, pregunta):
        """Corrige ortografía: cada palabra desconocida de 5+ letras se cambia por la más
        parecida del vocabulario (máx. 1 error; 2 si tiene 9+ letras) que empiece igual."""
        salida = []
        for w in pregunta.split():
            if w in self.vocab or len(w) < 5:
                salida.append(w)
                continue
            tope = 2 if len(w) >= 9 else 1
            mejor, mejor_d = w, tope + 1
            for v in self.vocab:
                if v[0] != w[0] or abs(len(v) - len(w)) > tope:
                    continue
                d = distancia(w, v)
                if d < mejor_d:
                    mejor, mejor_d = v, d
            salida.append(mejor)
        return " ".join(salida)

    def _puntaje(self, pregunta, keywords):
        """Cada keyword encontrada suma tantos puntos como caracteres tenga."""
        texto = f" {pregunta} "
        return sum(len(k) for k in keywords if f" {k} " in texto)

    def _quitar_cortesia(self, q):
        """Quita "gracias", "por favor"... Devuelve (pregunta limpia, regla de cortesía o None)."""
        regla_c = None
        for regla in self.kb.get("cortesia", {}).get("reglas", []):
            for k in sorted(regla["keywords"], key=len, reverse=True):
                if f" {k} " in f" {q} ":
                    q = f" {q} ".replace(f" {k} ", " ")
                    regla_c = regla_c or regla
        return re.sub(r"\s+", " ", q).strip(), regla_c

    # ---------- búsqueda en el árbol ----------
    def _mejor_en_subarbol(self, nodo, q):
        """Puntaje más alto de todo el subárbol que cuelga de este nodo."""
        mejor = self._puntaje(q, nodo["keywords"])
        for h in nodo.get("hijos", []):
            mejor = max(mejor, self._mejor_en_subarbol(h, q))
        return mejor

    def buscar(self, q):
        """Baja desde la raíz: en cada nodo entra al hijo cuyo subárbol puntúa más, siempre
        que supere al propio nodo. Se detiene cuando ningún hijo mejora. Devuelve (id, puntaje)."""
        nodo = self.kb["arbol"]
        while True:
            propio = self._puntaje(q, nodo["keywords"])
            mejor_hijo, mejor_p = None, 0
            for h in nodo.get("hijos", []):
                p = self._mejor_en_subarbol(h, q)
                if p > mejor_p:
                    mejor_hijo, mejor_p = h, p
            if mejor_hijo is None or mejor_p <= propio:
                return nodo["id"], propio
            nodo = mejor_hijo

    def _fuentes(self, claves):
        return [self.kb["fuentes"][c] for c in claves]

    def abrir(self, id_):
        """Resultado de visitar un nodo (por búsqueda o por tocar un botón del menú)."""
        n = self.nodos[id_]
        return {
            "respuesta": n["respuesta"],
            "detalle": n.get("detalle"),
            "fuentes": self._fuentes(self.heredar(id_, "fuentes") or []),
            "aviso": self.heredar(id_, "aviso"),
            "icono": self.heredar(id_, "icono"),
            "regla": id_,
            "ruta": self.ruta(id_),
            "hijos": [{"id": h["id"], "etiqueta": h["etiqueta"]}
                      for h in n.get("hijos", []) if not h.get("oculto")],
        }

    def _simple(self, respuesta, fuentes, regla):
        return {"respuesta": respuesta, "detalle": None, "fuentes": fuentes, "aviso": None,
                "icono": None, "regla": regla, "ruta": [], "hijos": []}

    def consultar(self, pregunta):
        q = self.corregir(normalizar(pregunta))
        q, cortesia = self._quitar_cortesia(q)
        fb = self.kb["fallback"]
        # Poda: preguntas fuera del dominio no entran al árbol
        if self._puntaje(q, fb["fuera_de_dominio"]["keywords"]) > 0:
            return self._simple(fb["fuera_de_dominio"]["respuesta"], [], "fuera_de_dominio")
        op = fb.get("otros_paises")
        if op and self._puntaje(q, op["keywords"]) > 0:
            return self._simple(op["respuesta"], self._fuentes(op["fuentes"]), "otros_paises")
        id_, puntaje = self.buscar(q)
        if puntaje < self.umbral:
            if cortesia:
                return self._simple(cortesia["respuesta"], [], cortesia["id"])
            return self._simple(fb["sin_coincidencia"]["respuesta"], [], "sin_coincidencia")
        return self.abrir(id_)

    def responder(self, pregunta):
        """Versión simple: (respuesta, fuentes, id de la regla)."""
        r = self.consultar(pregunta)
        return r["respuesta"], r["fuentes"], r["regla"]


def main():
    motor = MotorInferencia()
    print(motor.kb["personaje"]["saludo_inicial"], "(escribe 'salir' para terminar)")
    while True:
        pregunta = input("> ")
        if normalizar(pregunta) == "salir":
            break
        r = motor.consultar(pregunta)
        print(r["respuesta"])
        if r["aviso"]:
            print("Ojo:", r["aviso"])
        if r["fuentes"]:
            print("Fuentes:", "; ".join(f.split(",")[0] for f in r["fuentes"]))
        if r["ruta"]:
            print("Ruta:", " > ".join(motor.nodos[i]["etiqueta"] for i in r["ruta"]))
        if r["hijos"]:
            print("Puedes seguir con:", ", ".join(h["etiqueta"] for h in r["hijos"]))


if __name__ == "__main__":
    main()
