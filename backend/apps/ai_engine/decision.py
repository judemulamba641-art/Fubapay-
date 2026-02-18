# backend/apps/ai_engine/decision.py

import os
import json
from decimal import Decimal

from django.conf import settings
from apps.agents.models import AgentProfile
from apps.transactions.models import Transaction

from openai import OpenAI


class AIDecisionEngine:
    """
    Moteur de décision IA FubaPay basé sur ChatGPT.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    # ==========================================
    # DÉCISION PRINCIPALE
    # ==========================================

    def evaluate_transaction(self, transaction: Transaction):
        """
        Analyse une transaction et retourne :
        APPROVE / REVIEW / BLOCK
        """

        agent_profile = AgentProfile.objects.get(user=transaction.agent)

        payload = self._build_payload(transaction, agent_profile)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial fraud detection AI for a crypto fintech "
                        "called FubaPay operating in Africa. "
                        "Return ONLY valid JSON in this format: "
                        '{"decision": "APPROVE|REVIEW|BLOCK", "risk_score": 0-100, "reason": "short explanation"}'
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(payload)
                }
            ],
            temperature=0.2
        )

        try:
            decision_data = json.loads(response.choices[0].message.content)
        except Exception:
            return {
                "decision": "REVIEW",
                "risk_score": 50,
                "reason": "AI parsing error"
            }

        return decision_data

    # ==========================================
    # PAYLOAD POUR IA
    # ==========================================

    def _build_payload(self, transaction, agent_profile):

        return {
            "transaction": {
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "created_at": str(transaction.created_at)
            },
            "agent": {
                "reputation_score": agent_profile.reputation_score,
                "trust_level": agent_profile.trust_level,
                "total_volume": float(agent_profile.total_volume),
                "total_transactions": agent_profile.total_transactions,
                "dispute_count": agent_profile.dispute_count,
                "is_frozen": agent_profile.is_frozen
            }
        }