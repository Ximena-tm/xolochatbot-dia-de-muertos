"""Chatbot experto sobre Día de Muertos (sistema basado en reglas)."""
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
    """Distancia de edición (Damerau-Levenshtein simplificada):
    inserción, borrado, sustitución y transposición de letras cuentan 1."""
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
        self.vocab = self._construir_vocab()

    def _construir_vocab(self):
        """Todas las palabras que aparecen en alguna keyword."""
        listas = [self.kb["fallback"]["fuera_de_dominio"]["keywords"]]
        listas += [r["keywords"] for r in self.kb["reglas"]]
        listas += [r["keywords"] for r in self.kb.get("personaje", {}).get("reglas", [])]
        listas += [r["keywords"] for r in self.kb.get("cortesia", {}).get("reglas", [])]
        return {w for kws in listas for k in kws for w in k.split()}

    def corregir(self, pregunta):
        """Corrige errores de ortografía: cada palabra desconocida se cambia por
        la palabra más parecida del vocabulario (máx. 1 error; 2 si tiene 9+ letras). Solo corrige palabras de 5+ letras
        que empiecen con la misma letra, para no alterar palabras comunes como "solo"."""
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
        """Cada keyword encontrada suma tantos puntos como caracteres tenga
        (las keywords largas y específicas pesan más)."""
        texto = f" {pregunta} "
        return sum(len(k) for k in keywords if f" {k} " in texto)

    def _quitar_cortesia(self, q):
        """Quita frases de cortesía ("gracias", "por favor") de la pregunta para que
        no estorben al buscar la regla. Devuelve (pregunta limpia, regla de cortesía o None)."""
        regla_c = None
        for regla in self.kb.get("cortesia", {}).get("reglas", []):
            for k in sorted(regla["keywords"], key=len, reverse=True):
                if f" {k} " in f" {q} ":
                    q = f" {q} ".replace(f" {k} ", " ")
                    regla_c = regla_c or regla
        return re.sub(r"\s+", " ", q).strip(), regla_c

    def responder(self, pregunta):
        q = self.corregir(normalizar(pregunta))
        q, cortesia = self._quitar_cortesia(q)
        fb = self.kb["fallback"]
        # 1) Preguntas fuera del dominio (p. ej. "¿en Marte?")
        if self._puntaje(q, fb["fuera_de_dominio"]["keywords"]) > 0:
            return fb["fuera_de_dominio"]["respuesta"], [], "fuera_de_dominio"
        # 1b) Preguntas sobre otros países (las fuentes solo hablan de México)
        op = fb.get("otros_paises")
        if op and self._puntaje(q, op["keywords"]) > 0:
            return op["respuesta"], [self.kb["fuentes"][f] for f in op["fuentes"]], "otros_paises"
        # 2) Regla con mayor puntaje
        mejor, mejor_p = None, 0
        reglas = self.kb["reglas"] + self.kb.get("personaje", {}).get("reglas", [])
        for regla in reglas:
            p = self._puntaje(q, regla["keywords"])
            if p > mejor_p:
                mejor, mejor_p = regla, p
        if mejor is None or mejor_p < self.umbral:
            # Solo cortesía ("gracias", "por favor") o sin otra coincidencia
            if cortesia:
                return cortesia["respuesta"], [], cortesia["id"]
            return fb["sin_coincidencia"]["respuesta"], [], "sin_coincidencia"
        fuentes = [self.kb["fuentes"][f] for f in mejor.get("fuentes", [])]
        return mejor["respuesta"], fuentes, mejor["id"]


def main():
    motor = MotorInferencia()
    print(motor.kb["personaje"]["saludo_inicial"], "(escribe 'salir' para terminar)")
    while True:
        pregunta = input("> ")
        if normalizar(pregunta) == "salir":
            break
        respuesta, fuentes, regla = motor.responder(pregunta)
        print(respuesta)
        if fuentes:
            print("Fuentes:", "; ".join(f.split(",")[0] for f in fuentes))


if __name__ == "__main__":
    main()
