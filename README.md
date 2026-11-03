# Asistente RAG para gestión médica y administrativa (piloto Club Laureles F.C.)

Consulta en lenguaje natural sobre los protocolos médicos y administrativos de un club deportivo, con
**datos personales enmascarados antes de indexar**, **citas verificadas en código** y **abstención cuando no
hay sustento**.

> Piloto técnico. El corpus (`data/synthetic/`) y el padrón (`data/roster.example.json`) son **ficticios**.
> No es un dispositivo médico ni sustituye el criterio clínico.

## Respaldo institucional

Este proyecto surge de una solicitud directa de la Presidencia del Club Laureles F.C. para abordar desafíos
reales de gestión de datos sensibles (salud deportiva) y eficiencia operativa. Se desarrolla bajo un esquema
de Piloto Controlado (PoC).

## Cómo funciona

```
documentos ─► anonimizar (reglas + padrón) ─► ¿queda algo del padrón? ─sí─► ABORTA, no escribe el índice
                                                       │ no
                                                       ▼
                                           fragmentos por sección ─► índice (solo texto anonimizado)

pregunta ─► anonimizar ─► recuperar ─► ¿cobertura ≥ 0,6? ─no─► ABSTENCIÓN (sin llamar al modelo)
                                              │ sí
                                      generar (extractivo | LLM)
                                              │
              ¿modelo se abstuvo / sin cita válida / cifra inventada? ─sí─► DESCARTADA (queda en el registro)
                                              │ no
              respuesta + fuentes + aviso de revisión humana si el tema es clínico
```

| Decisión | Motivo |
|---|---|
| El texto original **nunca** se guarda en el índice | El índice es lo que se consulta y, opcionalmente, se envía a un modelo |
| La **pregunta** también se anonimiza, antes de buscar y de llamar a un modelo | Quien pregunta puede escribir un nombre o una cédula |
| La ingesta **falla** si queda algún alias del padrón | La anonimización se verifica, no se supone |
| Citas `[n]` y cifras **validadas en código** | Un prompt que "obliga a citar" no alcanza: se comprueba que cada cita apunte a un fragmento recuperado y que cada cifra de la respuesta esté en los fragmentos citados |
| Abstención por **cobertura de términos** antes de generar | Ahorra costo y evita respuestas fuera del corpus |
| Temas clínicos (alta, retorno, medicación, dosis…) → **revisión humana** siempre | Un error ahí es caro |
| `ingest` exige `--roster` (o `--no-roster` explícito) | Sin padrón los nombres no se enmascaran; no debe pasar en silencio |

## Anonimización: qué hace y qué no

Reglas + **padrón** de personas (`Roster`: nombre completo, apellido, apodos). **No es un reconocedor de
entidades (NER).**

- Con formato: cédula (con y sin etiqueta), teléfonos, correos, fecha de nacimiento (solo en ese contexto).
- Nombres: **solo los del padrón** (sin distinguir mayúsculas ni tildes; la variante más larga primero).
  **Un nombre que no esté en el padrón pasa sin enmascarar** (hay una prueba que lo documenta).
- Se conservan fechas de episodios, montos y cifras clínicas. Combinadas con otros datos podrían permitir
  reidentificar a alguien: el resultado sigue siendo información sensible.

## Resultados medidos

`python -m evals.run_evals` sobre `evals/golden_dataset.json`: **36 preguntas** (25 con respuesta en el corpus,
8 sin respuesta y 3 sondas de datos personales), escritas por el autor sobre el corpus ficticio. Generador
extractivo, sin LLM. Informe en [`results/eval_bm25.md`](results/eval_bm25.md).

| Métrica | Valor [IC95 % Wilson] |
|---|---|
| Recuperación hit@1 / hit@3 | 24/25 = 0,96 [0,80; 0,99] / 25/25 = 1,00 [0,87; 1,00] |
| Contenido correcto (respondibles) | 19/25 = 0,76 [0,57; 0,89] |
| Falsa abstención (respondibles) | 4/25 = 0,16 [0,06; 0,35] |
| Respuesta incorrecta (respondibles) | 2/25 = 0,08 [0,02; 0,25] |
| Abstención correcta (sin respuesta) | 8/8 = 1,00 [0,68; 1,00] |
| Cifras respaldadas por las citas | 23/23 = 1,00 [0,86; 1,00] |
| **Fugas de datos personales** | **0** |

Con ChromaDB y embeddings TF-IDF ([`results/eval_chroma.md`](results/eval_chroma.md)) los resultados son iguales.

**Cómo se eligió 0,6 de cobertura mínima.** No es un óptimo estadístico: se barrió con este mismo set
([`results/sweep_cobertura.md`](results/sweep_cobertura.md)) y se eligió por criterio, prefiriendo abstenerse
a responder fuera del corpus:

| Cobertura mínima | Correcto | Incorrecto | Falsa abstención | Abstención correcta | Respondió sin sustento |
|---|---|---|---|---|---|
| 0,34 | 20/25 | 4/25 | 1/25 | 6/8 | 2/8 |
| 0,5 | 20/25 | 3/25 | 2/25 | 6/8 | 2/8 |
| **0,6 (por defecto)** | 19/25 | 2/25 | 4/25 | 8/8 | 0/8 |
| 0,67 | 13/25 | 0/25 | 12/25 | 8/8 | 0/8 |

**Lo que fallaría con un usuario real** (casos concretos de este set):
- **Brecha léxica:** "se reintegran" vs "reintegro", "se estimaron" vs "estimado", "músculo" vs "muscular" →
  falsa abstención o fragmento equivocado. BM25 no entiende morfología verbal ni sinónimos.
- **Fragmento equivocado dentro del documento correcto** (`q12`, `q25`): el hit@3 cuenta el documento, pero la
  respuesta extractiva devuelve el fragmento mejor puntuado, que no siempre es el que contesta.
- Con umbrales más bajos aparecen respuestas a preguntas fuera del corpus que comparten vocabulario
  ("vigencia del carné de manejo" respondida con la vigencia del certificado de aptitud).
- Con 36 preguntas los intervalos son anchos: **una diferencia de un par de casos no significa nada**.

### Compuerta de regresión (reemplaza a la de la primera versión)

La primera versión decía que ningún cambio se fusionaba si la *faithfulness* de Ragas caía bajo 85 %, pero ese
script nunca se ejecutó. Ahora `python -m evals.run_evals --gate` (corre en CI) falla si cae: hit@3 < 0,90,
contenido correcto < 0,70, abstención correcta < 0,85, cifras respaldadas < 1,00 o **si aparece cualquier fuga
de datos personales**. Son **umbrales de regresión** fijados bajo lo medido, no metas de calidad. **No es Ragas
ni mide fidelidad semántica:** se verifican citas y cifras, no que el sentido de la respuesta sea correcto.

## Ejecutar

```bash
pip install -r requirements-dev.txt
pytest                                                     # 66 pruebas, sin red ni claves
python -m evals.run_evals --gate                           # la compuerta de CI

python -m src.cli ingest --docs data/synthetic --roster data/roster.example.json --out index/chunks.jsonl
python -m src.cli ask "¿Cuánto dura la vigencia del certificado de aptitud física?"

cp .env.example .env
streamlit run src/app.py
```

Con Docker: `docker compose up --build` y abrir http://localhost:8501 (construye el índice al arrancar y **se
niega a hacerlo sin `ROSTER_PATH`**).

Opcionales: `requirements-chroma.txt` (`RETRIEVAL_BACKEND=chroma`), `requirements-minilm.txt`
(`chroma-minilm`), `requirements-llm.txt` (`LLM_MODEL` + `ANTHROPIC_API_KEY`: redacta con un modelo; solo
sale texto ya anonimizado).

## Privacidad y uso responsable

- Los datos de salud son datos sensibles. Antes de usar datos reales: base legal y consentimientos (en
  Uruguay, Ley 18.331), acuerdo con cualquier proveedor externo de LLM y revisión del padrón. Esto no es
  asesoramiento legal.
- **La app de Streamlit no tiene autenticación.** Con datos reales debe ir detrás de un control de acceso.
- El registro de consultas (`QUERY_LOG`) guarda solo la pregunta anonimizada.
- El padrón real **no se versiona** (`.gitignore`); el de este repo es ficticio.

## Qué se verificó y qué no

**Verificado** (66 pruebas y ejecuciones reales): anonimización y sus casos de borde, ingesta que no escribe
datos originales y aborta ante fugas, recuperación BM25 y ChromaDB (con embeddings TF-IDF), pipeline completo
(abstención, citas inválidas, cifras inventadas, anonimización de la pregunta), CLI, app de Streamlit
(`AppTest` y arranque real con el entrypoint del contenedor), compuerta de evaluación. Se comprobó por
mutación que las pruebas fallan si se rompe cualquiera de esas garantías.

**No verificado:**
- **Un LLM real:** el generador de Anthropic solo se probó con un cliente simulado; la calidad de sus
  respuestas no se midió.
- **Embeddings semánticos** (`chroma-minilm`): no hay acceso a Hugging Face en el entorno de desarrollo.
- **`docker build` / `docker compose`:** no había daemon de Docker. Sí se probó el `entrypoint.sh` por separado.
- **Presidio:** se reemplazó por reglas + padrón; no se pudo ejecutar la versión original (requiere un modelo
  de spaCy en español) y no se probó una integración con él.
- Rendimiento y comportamiento con documentos reales: el corpus tiene 7 documentos y 21 fragmentos.

## Qué cambió respecto del piloto inicial

El primer commit tenía un anonimizador que importaba Presidio sin configurarlo, un script de evaluación
que dependía de un archivo de 2 preguntas (el README decía 50), un Dockerfile que apuntaba a `src/app.py`
inexistente y no había ingesta, recuperación ni cadena RAG. Esta versión los implementa, y en el camino
**se quitaron o cambiaron** cosas que el README original afirmaba:

| Decía | Ahora |
|---|---|
| LangChain | No se usa: BM25 propio y sin dependencias. LangChain está cubierto en `centro-ia-rag-data-pipeline` |
| LLaMA-3 / GPT-4 | No implementado. Hay una interfaz `Generator`; el generador con LLM es el de Anthropic (opcional) |
| Ragas / dataset de 50 preguntas | 36 preguntas sintéticas; compuerta determinista, sin Ragas |
| Presidio | Reglas + padrón de personas (ver límites arriba) |
| "System prompt obliga a citar la fuente" | Además, las citas se **verifican en código** |

## Autor

Fernando León Moloney — Ingeniero en Sistemas, especialización en Ingeniería Biomédica (UdelaR). Licencia MIT.
