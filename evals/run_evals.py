import json
from ragas import evaluate
from ragas.metrics import faithfulness, context_relevancy, answer_relevancy

def run_evaluation_pipeline():
    """
    Suite de evaluación continua. Ningún cambio de prompt o modelo 
    se mergea a main si la faithfulness cae por debajo del 85%.
    """
    with open('evals/golden_dataset.json', 'r') as f:
        dataset = json.load(f)
    
    # Evaluación de métricas críticas para el sector salud
    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_relevancy, answer_relevancy]
    )
    
    print(f"Faithfulness Score: {results['faithfulness']}")
    assert results['faithfulness'] >= 0.85, "ALERTA: Tasa de alucinación inaceptable."
