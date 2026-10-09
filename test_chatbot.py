import unittest
from chatbot import MotorInferencia

CASOS = [
    ("¿Qué es el Día de Muertos?", "que_es"), ("¿Qué día se celebra?", "fecha"),
    ("¿Qué día cae?", "fecha"), ("¿Cuál es el origen del Día de Muertos?", "historia"),
    ("¿Cuál es la historia?", "historia"), ("¿Cómo pongo una ofrenda?", "como_ofrenda"),
    ("¿Qué lleva una ofrenda?", "elementos"), ("¿Cuántos niveles tiene el altar?", "niveles"),
    ("¿Cómo es la ofrenda de los angelitos?", "ofrenda_ninos"), ("¿Qué significa el cempasúchil?", "cempasuchil"),
    ("¿Qué es el pan de muerto?", "pan_muerto"), ("¿Qué son las calaveritas de azúcar?", "calaveras_azucar"),
    ("¿Cómo se celebra en Oaxaca?", "regiones"), ("¿Es lo mismo que Halloween?", "halloween"),
    ("¿Es Patrimonio de la Humanidad por la UNESCO?", "unesco"), ("¿Dónde coloco el altar en mi casa?", "ubicacion_altar"),
    ("¿Qué comida se pone en la ofrenda?", "comida_ofrenda"), ("¿Cómo se hace el pan de muerto?", "receta_pan_muerto"),
    ("¿Qué significa el papel picado?", "papel_picado"), ("¿Qué es el Mictlán?", "mictlan"),
    ("¿Quién creó a la Catrina?", "catrina"), ("¿Qué es una calavera literaria?", "calavera_literaria"),
    ("¿Quién es el xoloitzcuintle?", "xoloitzcuintle"), ("¿Quién eres?", "quien_eres"), ("Hola", "saludo"),
    ("¿En Marte se hace Día de Muertos?", "fuera_de_dominio"), ("¿Y en Júpiter?", "fuera_de_dominio"),
    ("¿Se celebra en jupitr?", "fuera_de_dominio"), ("¿Qué es el pan de muerot?", "pan_muerto"),
    ("¿Qué significa el cempasuchl?", "cempasuchil"), ("como pongo una ofrnda", "como_ofrenda"),
    ("¿Qué es el mictlna?", "mictlan"), ("¿Quién creó a la catirna?", "catrina"), ("¿Cuál es tu color favorito?", "sin_coincidencia"),
]

class TestMotor(unittest.TestCase):
    def test_casos(self):
        motor = MotorInferencia()
        for pregunta, esperada in CASOS:
            with self.subTest(pregunta=pregunta):
                self.assertEqual(motor.responder(pregunta)[2], esperada)

if __name__ == "__main__":
    unittest.main()
