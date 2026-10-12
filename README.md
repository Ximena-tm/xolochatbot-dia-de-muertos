# Xolo, chatbot experto sobre el Día de Muertos

Sistema experto conversacional basado en reglas que responde preguntas sobre el Día de Muertos en México. El personaje es **Xolo**, un xoloitzcuintle: según la leyenda, el perro que guía a las almas al Mictlán.

**Pruébalo en línea:** [Xolo en GitHub Pages](https://ximena-tm.github.io/xolochatbot-dia-de-muertos/) 

Proyecto individual de la materia de Sistemas Inteligentes (unidad de Sistemas Expertos). **El experto del dominio son las fuentes documentales** listadas abajo: el sistema no usa conocimiento externo y cada respuesta indica de qué fuentes proviene.

## Público y alcance (MVP / demo)

- **Usuarios:** estudiantes de **secundaria** (12 a 15 años). Las respuestas están escritas en lenguaje sencillo y cortas; el texto completo y más técnico de cada fuente está disponible con el botón **"Ver más detalle"**. Los pasos con fuego u horno incluyen un aviso de seguridad.
- **Entregable:** una **demo funcional** (MVP) publicada en GitHub Pages, con un árbol de 4 ramas y 21 temas.
- **Fuera del MVP** (siguientes iteraciones): más temas, voz, otros idiomas, pruebas con estudiantes reales y ajuste del vocabulario según sus preguntas.

## Reto

Mucha gente (sobre todo las generaciones jóvenes y quienes nunca han armado una ofrenda) desconoce el significado, el origen y la forma de celebrar el Día de Muertos. Xolo responde estas dudas de forma **consistente y justificada**, y declara cuando no tiene información (por ejemplo, si le preguntas si se celebra en Marte).

## Arquitectura

Sigue la estructura básica de un sistema experto:

```mermaid
flowchart LR
    F[Fuentes documentales<br/>experto del dominio] --> K[Adquisición del conocimiento<br/>ingeniero del conocimiento]
    K --> B[(Base de conocimientos<br/>base_conocimientos.json)]
    B <--> M[Motor de inferencia<br/>chatbot.py / motor.js]
    M <--> I[Interfaz<br/>página web con Xolo]
    I <--> U((Usuario))
```

| Componente de un SE | En este proyecto |
|---|---|
| Experto del dominio | Las fuentes documentales |
| Ingeniero del conocimiento | La ingeniera extrae y contrasta la información |
| Base de conocimientos | `base_conocimientos.json`: árbol de marcos (palabras clave, respuesta, detalle, fuentes, avisos), más filtros de dominio y respuestas de cortesía |
| Motor de inferencia | `motor.js` (el que corre en la página web) y `chatbot.py` (la misma lógica en Python, usada para las pruebas automáticas) |
| Interfaz | Página web publicada en GitHub Pages (`index.html`) |

## El árbol de conocimiento

La base de conocimientos es un **árbol de marcos** (*slot-and-filler*). Cada nodo es un marco con slots (`etiqueta`, `keywords`, `respuesta`, `detalle`, `fuentes`, `aviso`, `icono`) y `hijos` son los nodos que lo tienen como **isa**. Va de lo general (arriba) a lo específico (abajo):

```mermaid
flowchart TD
    R["🌼 Día de Muertos<br/>(raíz)"] --> T["📅 Fechas e historia"]
    R --> O["🕯️ La ofrenda"]
    R --> S["💀 Personajes y creencias"]
    R --> C["🌎 Hoy y en el mundo"]
    T --> fecha[Cuándo se celebra]
    T --> hist[De dónde viene] --> sinc[Sincretismo]
    O --> como["Cómo armarla ⚠️"] --> ub[Dónde ponerla]
    como --> niv[Cuántos niveles]
    O --> el[Qué lleva]
    el --> cemp[Cempasúchil]
    el --> pp[Papel picado]
    el --> cal[Calaveritas de azúcar]
    el --> pan[Pan de muerto] --> rec["Receta ⚠️"]
    O --> com[Comida y bebida]
    O --> nin[Ofrenda de niños]
    S --> mic[Mictlán]
    S --> xol[Xoloitzcuintle]
    S --> cat[Catrina]
    S --> cl[Calavera literaria]
    C --> reg[Regiones]
    C --> hal[Halloween]
    C --> une[UNESCO]
```

(⚠️ = nodo con aviso de seguridad. `saludo` y `quien_eres` son nodos ocultos bajo la raíz: se encuentran al escribir, no salen en el menú.)

**Herencia.** Un nodo hereda los slots que no define, subiendo por `isa` (el algoritmo "propiedad de herencia"): se busca el valor en el nodo; si no lo tiene, se pasa al padre, y así hasta la raíz; si nadie lo tiene, falla. Ejemplos: *Cuántos niveles lleva* y *Dónde ponerla* heredan el `aviso` de las veladoras de *Cómo armarla*; todos los temas de la rama *La ofrenda* heredan su `icono`. Cada nodo declara sus propias `fuentes` para que cada respuesta cite solo lo que le corresponde.

**Dos formas de recorrerlo:** escribiendo una pregunta (el motor baja por el árbol) o tocando los botones (el usuario baja, y puede subir con "Volver a…"). En ambos casos se muestra la **ruta** recorrida, por ejemplo *Día de Muertos › La ofrenda › Qué lleva › Pan de muerto*.

### Cómo razona el motor

1. **Normaliza** la pregunta: minúsculas, sin acentos ni signos, y corrige errores de ortografía comparándola con el vocabulario de la base.
2. **Cortesía:** quita frases como "gracias" o "por favor" para que no estorben. Si la pregunta es solo de cortesía (por ejemplo, "gracias"), Xolo responde con amabilidad.
3. **Filtro de dominio:** si menciona algo ajeno (Marte, la Luna…), responde que no tiene información.
4. **Puntaje:** cada nodo suma la longitud de las palabras clave que aparecen en la pregunta (las específicas pesan más).
5. **Baja por el árbol:** desde la raíz entra al hijo cuyo subárbol puntúa más, mientras supere al nodo actual. Se detiene en el nodo más específico que explica la pregunta; si no alcanza el umbral (3), responde "sin coincidencia". (Los filtros de dominio actúan como **poda**: esas preguntas nunca entran al árbol.)
6. **Justifica:** devuelve la respuesta, la ruta, las fuentes, el aviso heredado y los temas hijos para seguir explorando.

## Estructura del repositorio

```
.
├── base_conocimientos.json   # árbol de conocimiento, fuentes, filtros y cortesía
├── index.html                # interfaz web con Xolo (la página publicada)
├── motor.js                  # motor de inferencia que usa la página web
├── chatbot.py                # el mismo motor en Python (base de las pruebas)
├── test_chatbot.py           # pruebas del motor y de la estructura del árbol
└── README.md
```

## Uso

**En línea (recomendado):** abre la página publicada con GitHub Pages, escribe tu pregunta o elige una de las sugeridas.

**En tu computadora (opcional):** la página carga `base_conocimientos.json`, así que necesita un servidor local; abrir `index.html` con doble clic no funciona.

```bash
python -m http.server 8000
# abre http://localhost:8000
```

**Pruebas automáticas** (requieren Python 3.8+, sin dependencias externas):

```bash
python test_chatbot.py
```

También hay modo consola: `python chatbot.py`.

## Preguntas que responde

| Tema | Ejemplo |
|---|---|
| Definición | ¿Qué es el Día de Muertos? |
| Fechas | ¿Qué día se celebra? |
| Origen | ¿Cuál es el origen del Día de Muertos? |
| Ofrenda | ¿Cómo pongo una ofrenda? · ¿Qué lleva una ofrenda? · ¿Cuántos niveles tiene el altar? · ¿Dónde coloco el altar en mi casa? · ¿Cómo es la ofrenda de los angelitos? |
| Comida | ¿Qué comida se pone en la ofrenda? · ¿Qué es el pan de muerto? · ¿Cómo se hace el pan de muerto? |
| Símbolos | ¿Qué significa el cempasúchil? · ¿Qué significa el papel picado? · ¿Qué son las calaveritas de azúcar? · ¿Quién creó a la Catrina? · ¿Qué es una calavera literaria? |
| Creencias | ¿Qué es el Mictlán? · ¿Quién es el xoloitzcuintle? |
| Contexto | ¿Cómo se celebra en Oaxaca? · ¿Es lo mismo que Halloween? · ¿Es Patrimonio de la Humanidad por la UNESCO? |
| Explorar con botones | Tocar *La ofrenda* › *Qué lleva* › *Pan de muerto* › *Receta del pan* |
| Fuera de dominio | ¿En Marte se hace Día de Muertos? |
| Personaje y cortesía | ¿Quién eres? · Hola · Gracias · Por favor |

## Fuentes (el experto)

| Clave | Fuente |
|---|---|
| INAH | V. J. Santos Ramírez, *El origen del Día de Muertos*, INAH |
| INPI | *Antología: El Día de Muertos entre los pueblos indígenas de México*, INPI, 2020 |
| SRE | SRE-AMEXCID, *Día de Muertos* (elementos de la ofrenda y recetario) |
| INAFED | *Día de Muertos, tradición mexicana que trasciende en el tiempo*, gob.mx, 2019 |
| SADER | *Día de Muertos, la fiesta más emotiva de México*, gob.mx, 2021 |
| UNAM | UNAM, Dirección de CENDI, *Día de Muertos: elementos de la ofrenda* |
| EMBAJADA | Embajada de México en Uruguay, *Día de Muertos*, 2020 |
| CNN | CNN en Español, *¿Cuál es el origen e historia del Día de Muertos?*, 31/10/2025 |
| ECONOMISTA | *El Economista*, *Cómo armar tu ofrenda de Día de Muertos*, 27/10/2024 |
| XOLO | SADER-DGSIAP, *La leyenda del Xoloitzcuintle, el perro azteca*, gob.mx |

### Conocimiento en conflicto

Cuando las fuentes discrepan, el sistema presenta ambas posturas en lugar de elegir una:

- **Origen:** INAFED, SADER y CNN hablan de sincretismo prehispánico-católico; el INAH sostiene que las fiestas del 1 y 2 de noviembre son de origen europeo medieval.
- **UNESCO:** 2003 (proclamación) o 2008 (inscripción en la Lista Representativa).
- **Niveles del altar:** tres (SRE, UNAM) o dos, tres o siete (El Economista).

## Fases de desarrollo

El proyecto sigue las fases de construcción de un sistema experto vistas en clase, de forma incremental:

| Fase | Qué se hizo |
|---|---|
| Identificación | Reto: jóvenes que desconocen el Día de Muertos; público de secundaria |
| Conceptualización | Conceptos clave y relaciones extraídos de las fuentes |
| Formalización | Estructura elegida: árbol *isa* de marcos con herencia |
| Implementación | `chatbot.py` / `motor.js` e `index.html` |
| Testeo | `test_chatbot.py` (casos del motor y validez del árbol) |

## Limitaciones

- El método por palabras clave no entiende el significado: una pregunta que mezcla dos temas se resuelve hacia una sola regla.
- Solo cubre lo que dicen las fuentes; fuera de ellas responde "no tengo información".

## Agregar conocimiento

Añade un nodo en la lista `hijos` del nodo que lo generaliza (su *isa*) dentro de `arbol`, con `id` único, `etiqueta` (texto del botón), `keywords` (minúsculas, sin acentos), `respuesta` (lenguaje sencillo, para secundaria), `detalle` (opcional, texto completo) y `fuentes` (claves de la sección `fuentes`). Si no defines `aviso` o `icono`, los hereda del padre. Agrega un caso a `test_chatbot.py` y corre las pruebas (verifican que el árbol sea válido y que las fuentes existan). Las respuestas de cortesía ("gracias", "por favor") están en la sección `cortesia` del mismo archivo.
