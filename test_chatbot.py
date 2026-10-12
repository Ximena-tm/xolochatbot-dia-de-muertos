import unittest
from chatbot import MotorInferencia

CASOS = [
    ("¿Qué es el Día de Muertos?", "dia_de_muertos"), ("¿Qué día se celebra?", "fecha"),
    ("¿Qué día cae?", "fecha"), ("¿Cuál es el origen del Día de Muertos?", "historia"),
    ("¿Cuál es la historia?", "historia"), ("¿Cómo pongo una ofrenda?", "como_ofrenda"),
    ("¿Qué lleva una ofrenda?", "elementos"), ("¿Cuántos niveles tiene el altar?", "niveles"),
    ("¿Cómo es la ofrenda de los angelitos?", "ofrenda_ninos"), ("¿Qué significa el cempasúchil?", "cempasuchil"),
    ("¿Qué es el pan de muerto?", "pan_muerto"), ("¿Qué son las calaveritas de azúcar?", "calaveras_azucar"),
    ("¿Cómo se celebra en Oaxaca?", "regiones"), ("¿Es lo mismo que Halloween?", "halloween"),
    ("¿Es Patrimonio de la Humanidad por la UNESCO?", "unesco"), ("¿Dónde coloco el altar en mi casa?", "ubicacion_altar"),
    ("¿Qué comida se pone en la ofrenda?", "comida_ofrenda"), ("¿Cómo se hace el pan de muerto?", "receta_pan_muerto"),
    ("¿Qué significa el papel picado?", "papel_picado"), ("¿Qué es el Mictlán?", "mictlan"), ("¿Qué es el sincretismo?", "sincretismo"), ("¿Qué es una flor?", "cempasuchil"), ("¿Qué es la democracia?", "sin_coincidencia"), ("¿Qué significa la vida?", "sin_coincidencia"), ("¿Qué es esta fiesta?", "dia_de_muertos"), ("cuéntame sobre eso", "dia_de_muertos"), ("¿Solo se celebra en México?", "otros_paises"), ("¿Se celebra en Guatemala?", "otros_paises"), ("¿Se hace en otros países?", "otros_paises"), ("cuentame mas", "dia_de_muertos"), ("cuéntame sobre las ofrendas", "ofrenda"),
    ("¿Quién creó a la Catrina?", "catrina"), ("¿Qué es una calavera literaria?", "calavera_literaria"),
    ("¿Quién es el xoloitzcuintle?", "xoloitzcuintle"), ("¿Quién eres?", "quien_eres"), ("Hola", "saludo"),
    ("¿En Marte se hace Día de Muertos?", "fuera_de_dominio"), ("¿Y en Júpiter?", "fuera_de_dominio"),
    ("¿Se celebra en jupitr?", "fuera_de_dominio"), ("¿Qué es el pan de muerot?", "pan_muerto"),
    ("¿Qué significa el cempasuchl?", "cempasuchil"), ("como pongo una ofrnda", "como_ofrenda"),
    ("¿Qué es el mictlna?", "mictlan"), ("¿Quién creó a la catirna?", "catrina"), ("¿Cuál es tu color favorito?", "sin_coincidencia"),
    ("Gracias", "gracias"), ("muchas gracias Xolo", "gracias"), ("grcias", "gracias"), ("Por favor", "por_favor"),
    ("porfa", "por_favor"), ("¡Gracias! ¿Qué es el pan de muerto?", "pan_muerto"), ("¿Qué día cae, por favor?", "fecha"),
    ("¿Cómo pongo una ofrenda, por favor?", "como_ofrenda"), ("Hola, gracias", "saludo"),
]

class TestMotor(unittest.TestCase):
    def test_casos(self):
        motor = MotorInferencia()
        for pregunta, esperada in CASOS:
            with self.subTest(pregunta=pregunta):
                self.assertEqual(motor.responder(pregunta)[2], esperada)


class TestArbol(unittest.TestCase):
    def setUp(self):
        self.m = MotorInferencia()

    def test_estructura(self):
        raiz = self.m.kb["arbol"]["id"]
        self.assertIsNone(self.m.padre[raiz])
        for id_, padre in self.m.padre.items():          # todo nodo, salvo la raíz, tiene padre
            self.assertTrue(id_ == raiz or padre in self.m.nodos)
        ids = []
        def recorrer(n):
            ids.append(n["id"])
            for h in n.get("hijos", []):
                recorrer(h)
        recorrer(self.m.kb["arbol"])
        self.assertEqual(len(ids), len(set(ids)))        # ids únicos: es árbol, no grafo

    def test_fuentes_existen(self):
        for n in self.m.nodos.values():
            for f in n.get("fuentes", []):
                self.assertIn(f, self.m.kb["fuentes"])

    def test_ruta(self):
        self.assertEqual(self.m.ruta("pan_muerto"), ["dia_de_muertos", "ofrenda", "elementos", "pan_muerto"])
        self.assertEqual(self.m.consultar("¿Cómo se hace el pan de muerto?")["ruta"][-1], "receta_pan_muerto")

    def test_herencia(self):
        aviso = self.m.nodos["como_ofrenda"]["aviso"]
        self.assertEqual(self.m.heredar("niveles", "aviso"), aviso)          # lo hereda de como_ofrenda
        self.assertEqual(self.m.heredar("ubicacion_altar", "aviso"), aviso)
        self.assertIsNone(self.m.heredar("pan_muerto", "aviso"))              # otra rama: no lo hereda
        self.assertEqual(self.m.heredar("cempasuchil", "icono"), "🕯️")       # icono de la rama ofrenda
        self.assertIsNone(self.m.heredar("fecha", "no_existe"))              # falla si nadie lo tiene

    def test_menu(self):
        hijos = [h["id"] for h in self.m.abrir("dia_de_muertos")["hijos"]]
        self.assertEqual(hijos, ["tiempo", "ofrenda", "simbolos", "contexto"])  # ocultos no salen
        self.assertEqual(self.m.abrir("receta_pan_muerto")["hijos"], [])       # hoja

if __name__ == "__main__":
    unittest.main()
