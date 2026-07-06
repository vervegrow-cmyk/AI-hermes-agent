from src.app.runners.tasks import DECISION_LOG_REPOSITORY
from src.shared.contracts.screening import ScreeningDecision as PublishDecision


def build_decision_log(decision: PublishDecision) -> dict:
    return DECISION_LOG_REPOSITORY.save(decision)
