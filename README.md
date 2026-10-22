# 🏥 Asistente RAG para Gestión Médica y Administrativa (Piloto Club Laureles F.C.)

## 🏛️ Respaldo Institucional
Este proyecto surge de una solicitud directa de la Presidencia del Club Laureles F.C. para abordar desafíos reales de gestión de datos sensibles (salud deportiva) y eficiencia operativa. Se desarrolla bajo un esquema de Piloto Controlado (PoC).

## 🏗️ Arquitectura
- **Lenguaje:** Python 3.10+ | **Framework:** LangChain
- **Vector DB:** ChromaDB | **Modelo:** LLaMA-3 / GPT-4 (vía API segura)
- **Evaluación:** Ragas / Golden Dataset personalizado (n=50)

## ⚙️ Decisiones de Ingeniería y Seguridad
1. **Privacidad:** Anonimización de PII (Presidio) en la ingesta.
2. **Trazabilidad:** System prompt obliga a citar fuente exacta.
3. **Evals:** Script de evaluación continua (`evals/run_evals.py`).

## 🚀 Ejecución
1. `cp .env.example .env` (Configurar API Keys)
2. `docker-compose up --build` o `streamlit run src/app.py`
