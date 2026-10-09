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


class MotorInferencia:
    def __init__(self, ruta="base_conocimientos.json", umbral=3):
        with open(ruta, encoding="utf-8") as f:
            self.kb = json.load(f)
        self.umbral = umbral

    def _puntaje(self, pregunta, keywords):
        """Cada keyword encontrada suma tantos puntos como caracteres tenga
        (las keywords largas y específicas pesan más)."""
        texto = f" {pregunta} "
        return sum(len(k) for k in keywords if f" {k} " in texto)

    def responder(self, pregunta):
        q = normalizar(pregunta)
        fb = self.kb["fallback"]
        # 1) Preguntas fuera del dominio (p. ej. "¿en Marte?")
        if self._puntaje(q, fb["fuera_de_dominio"]["keywords"]) > 0:
            return fb["fuera_de_dominio"]["respuesta"], [], "fuera_de_dominio"
        # 2) Regla con mayor puntaje
        mejor, mejor_p = None, 0
        reglas = self.kb["reglas"] + self.kb.get("personaje", {}).get("reglas", [])
        for regla in reglas:
            p = self._puntaje(q, regla["keywords"])
            if p > mejor_p:
                mejor, mejor_p = regla, p
        if mejor is None or mejor_p < self.umbral:
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
