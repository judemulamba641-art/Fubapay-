# backend/apps/ai_engine/risk.py

from apps.ai_engine.fraud import FraudDetectionEngine
from apps.ai_engine.scoring import AIScoringEngine
from apps.ai_engine.decision import AIDecisionEngine


class RiskEngine:
    """
    Moteur global de gestion du risque FubaPay.
    Combine règles locales + scoring + IA externe.
    """

    def __init__(self, transaction):
        self.transaction = transaction
        self.agent = transaction.agent

        self.fraud_engine = FraudDetectionEngine(self.agent)
        self.scoring_engine = AIScoringEngine(self.agent)
        self.ai_engine = AIDecisionEngine()

    # ====================================================
    # ÉVALUATION GLOBALE
    # ====================================================

    def evaluate(self):
        """
        Retourne décision finale structurée :
        {
            decision: APPROVE | REVIEW | BLOCK,
            risk_score: int,
            details: {...}
        }
        """

        # 1️⃣ RÈGLES RAPIDES (LOCAL)
        fraud_result = self.fraud_engine.analyze_transaction(self.transaction)

        if fraud_result["decision"] == "BLOCK":
            return {
                "decision": "BLOCK",
                "risk_score": fraud_result["risk_score"],
                "details": {
                    "source": "fraud_engine",
                    "flags": fraud_result["flags"]
                }
            }

        # 2️⃣ SCORING ACTUEL
        current_score = self.scoring_engine.calculate_score()

        # Si score extrêmement bas → blocage direct
        if current_score < 15:
            return {
                "decision": "BLOCK",
                "risk_score": 90,
                "details": {
                    "source": "scoring_engine",
                    "reason": "Very low reputation score"
                }
            }

        # 3️⃣ IA CONTEXTUELLE (ChatGPT)
        ai_result = self.ai_engine.evaluate_transaction(self.transaction)

        # ====================================================
        # FUSION DES DÉCISIONS
        # ====================================================

        final_decision = self._merge_decisions(
            fraud_result,
            ai_result
        )

        return {
            "decision": final_decision,
            "risk_score": ai_result.get("risk_score", 50),
            "details": {
                "fraud_flags": fraud_result["flags"],
                "ai_reason": ai_result.get("reason", ""),
                "agent_score": current_score
            }
        }

    # ====================================================
    # LOGIQUE DE FUSION
    # ====================================================

    def _merge_decisions(self, fraud_result, ai_result):

        # Si l’IA bloque → blocage
        if ai_result.get("decision") == "BLOCK":
            return "BLOCK"

        # Si fraud medium + IA review → review
        if (
            fraud_result["decision"] == "REVIEW"
            or ai_result.get("decision") == "REVIEW"
        ):
            return "REVIEW"

        return "APPROVE"