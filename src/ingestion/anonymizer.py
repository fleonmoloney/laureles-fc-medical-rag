import re
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Uso de Presidio para anonimizar datos sensibles (PII) antes de la ingesta.
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymize_medical_text(text: str) -> str:
    """
    Fallo superado: Inicialmente los LLMs memorizaban nombres de jugadores 
    en los reportes médicos. Solución: Anonimización en la ingesta.
    """
    results = analyzer.analyze(text=text, language='es', entities=["PERSON", "ID", "MEDICAL_CONDITION"])
    anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_text.text
