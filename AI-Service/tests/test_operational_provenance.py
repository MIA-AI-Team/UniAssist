from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from ai_tutor.config import Config
from ai_tutor.engine.evaluator import AIEvaluationEngine


def test_parallel_provider_metadata_does_not_cross_calls(monkeypatch):
    monkeypatch.setattr(Config, "MOCK_MODE", True)
    engine = AIEvaluationEngine()
    barrier = Barrier(2)
    def work(provider):
        engine._last_llm_info = {"provider":provider,"model":provider+"-test"}
        barrier.wait(timeout=5)
        return engine._last_llm_info["provider"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(work,["groq","gemini"]))==["groq","gemini"]
    assert engine._last_llm_info["provider"] is None


def test_rubric_metadata_reports_actual_truncation(monkeypatch):
    monkeypatch.setattr(Config, "MOCK_MODE", True)
    monkeypatch.setattr(Config, "MAX_REFERENCE_CHARS", 20)
    response = AIEvaluationEngine().suggest_rubric("Example task", "assignment", "Public instructions", "x"*100)
    assert response.ai_metadata.prompt_truncated is True
