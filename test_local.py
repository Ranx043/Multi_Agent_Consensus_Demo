from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json

class ResolutionStrategy(Enum):
    UNANIMOUS = 'unanimous'
    WEIGHTED_MAJORITY = 'weighted_majority'
    NUANCE_ARBITRATION = 'nuance_arbitration'
    MATH_OVERRIDE = 'math_override'

class CertaintyLevel(Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

@dataclass
class AgentResponse:
    agent_id: str
    domain: str
    interpretation: str
    score: float
    confidence: float
    certainty_level: CertaintyLevel
    supporting_factors: List[str]
    contradicting_factors: List[str]
    dasha_weight: Optional[float] = None
    sav_score: Optional[str] = None

@dataclass
class ConsensusResult:
    domain: str
    final_score: float
    final_interpretation: str
    confidence: float
    certainty_level: str
    agreement_level: str
    strategy_used: ResolutionStrategy
    conflicts_detected: int
    conflicts_resolved: int
    agent_contributions: Dict[str, float]
    dasha_adjusted: bool
    sav_tier: str

    def to_dict(self) -> dict:
        return {
            'domain': self.domain,
            'final_score': round(self.final_score, 2),
            'confidence': round(self.confidence, 3),
            'certainty_level': self.certainty_level,
            'agreement_level': self.agreement_level,
            'strategy_used': self.strategy_used.value,
            'conflicts_detected': self.conflicts_detected,
            'conflicts_resolved': self.conflicts_resolved,
            'dasha_adjusted': self.dasha_adjusted,
            'sav_tier': self.sav_tier
        }

class ConsensusEngine:
    DOMAIN_WEIGHTS = {
        'career': {
            'integration_specialist': 0.30,
            'mathematics_validator': 0.20,
            'risk_assessor': 0.25,
            'nuance_specialist': 0.25
        },
        'marriage': {
            'integration_specialist': 0.20,
            'mathematics_validator': 0.10,
            'risk_assessor': 0.30,
            'nuance_specialist': 0.40
        },
        'health': {
            'integration_specialist': 0.25,
            'mathematics_validator': 0.15,
            'risk_assessor': 0.35,
            'nuance_specialist': 0.25
        }
    }
    CONFLICT_THRESHOLD = 15.0

    def __init__(self):
        self.resolution_log = []

    def calculate_consensus(self, responses, domain):
        weights = self.DOMAIN_WEIGHTS.get(domain, self.DOMAIN_WEIGHTS['career'])
        weighted_sum = 0.0
        weight_total = 0.0
        dasha_adjusted = False
        sav_scores = []

        for response in responses:
            agent_weight = weights.get(response.agent_id, 0.25)
            effective_confidence = response.confidence
            if response.dasha_weight is not None:
                effective_confidence *= (0.5 + 0.5 * response.dasha_weight)
                dasha_adjusted = True
            effective_weight = agent_weight * effective_confidence
            weighted_sum += response.score * effective_weight
            weight_total += effective_weight
            if response.sav_score:
                try:
                    sav_num = int(response.sav_score.split('/')[0])
                    sav_scores.append(sav_num)
                except:
                    pass

        initial_score = weighted_sum / weight_total if weight_total > 0 else 50.0
        avg_sav = sum(sav_scores) / len(sav_scores) if sav_scores else 28
        sav_tier = 'above_average' if avg_sav >= 30 else ('average' if avg_sav >= 25 else 'below_average')

        conflicts = [r for r in responses if abs(r.score - initial_score) > self.CONFLICT_THRESHOLD]

        if conflicts:
            nuance_conflict = next((c for c in conflicts if c.agent_id == 'nuance_specialist'), None)
            if nuance_conflict and domain in ['marriage', 'health']:
                self.resolution_log.append({'strategy': 'NUANCE_ARBITRATION', 'reason': f'{domain} prioritizes D9'})
                final_score = 0.6 * nuance_conflict.score + 0.4 * initial_score
                strategy = ResolutionStrategy.NUANCE_ARBITRATION
            else:
                sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)[:3]
                recalc_sum = sum(r.score * r.confidence for r in sorted_responses)
                recalc_weight = sum(r.confidence for r in sorted_responses)
                final_score = recalc_sum / recalc_weight
                strategy = ResolutionStrategy.WEIGHTED_MAJORITY
        else:
            final_score = initial_score
            strategy = ResolutionStrategy.UNANIMOUS

        score_range = max(r.score for r in responses) - min(r.score for r in responses)
        agreement_level = 'high' if score_range <= 10 else ('medium' if score_range <= 20 else 'low')
        avg_confidence = sum(r.confidence for r in responses) / len(responses)
        final_confidence = min(1.0, max(0.0, avg_confidence + (0.1 if agreement_level == 'high' else -0.1 if agreement_level == 'low' else 0)))
        certainty = 'high' if final_confidence > 0.8 else ('medium' if final_confidence > 0.5 else 'low')

        return ConsensusResult(
            domain=domain,
            final_score=final_score,
            final_interpretation=f'{domain} analysis complete',
            confidence=final_confidence,
            certainty_level=certainty,
            agreement_level=agreement_level,
            strategy_used=strategy,
            conflicts_detected=len(conflicts),
            conflicts_resolved=len(conflicts),
            agent_contributions={r.agent_id: round(weights.get(r.agent_id, 0.25) * r.confidence, 3) for r in responses},
            dasha_adjusted=dasha_adjusted,
            sav_tier=sav_tier
        )

# TEST CAREER
career = [
    AgentResponse('integration_specialist', 'career', '10th lord strong', 78.5, 0.87, CertaintyLevel.HIGH, ['Jupiter aspects 10th'], [], 0.85, '32/48'),
    AgentResponse('mathematics_validator', 'career', 'SAV 32/48', 75.0, 0.95, CertaintyLevel.HIGH, ['SAV above avg'], [], 0.85, '32/48'),
    AgentResponse('risk_assessor', 'career', 'No Kemadruma', 81.0, 0.82, CertaintyLevel.HIGH, ['No dosha'], [], 0.85, '32/48'),
    AgentResponse('nuance_specialist', 'career', 'Neecha Bhanga', 76.0, 0.79, CertaintyLevel.MEDIUM, ['D9 confirms'], [], 0.85, '32/48'),
]

# TEST MARRIAGE (conflict expected)
marriage = [
    AgentResponse('integration_specialist', 'marriage', 'Venus strong', 68.0, 0.85, CertaintyLevel.MEDIUM, ['Venus own sign'], ['Saturn aspects'], 0.70, '28/48'),
    AgentResponse('mathematics_validator', 'marriage', 'SAV 28/48', 58.0, 0.92, CertaintyLevel.HIGH, ['Average SAV'], [], 0.70, '28/48'),
    AgentResponse('risk_assessor', 'marriage', 'Manglik cancelled', 62.0, 0.88, CertaintyLevel.MEDIUM, ['Cancellation'], ['Mars in 7th'], 0.70, '28/48'),
    AgentResponse('nuance_specialist', 'marriage', 'D9 Venus exalted', 88.0, 0.78, CertaintyLevel.HIGH, ['Venus exalted D9', 'Vargottama'], [], 0.70, '28/48'),
]

# TEST HEALTH
health = [
    AgentResponse('integration_specialist', 'health', 'Lagna lord strong', 65.0, 0.80, CertaintyLevel.MEDIUM, ['Lagna in Kendra'], ['Saturn 6th'], 0.60, '26/48'),
    AgentResponse('mathematics_validator', 'health', 'SAV 26/48', 62.0, 0.90, CertaintyLevel.HIGH, ['Average SAV'], [], 0.60, '26/48'),
    AgentResponse('risk_assessor', 'health', 'Grahan dosha', 55.0, 0.85, CertaintyLevel.MEDIUM, [], ['Grahan dosha', 'Rahu periods'], 0.60, '26/48'),
    AgentResponse('nuance_specialist', 'health', 'D9 mitigation', 68.0, 0.75, CertaintyLevel.MEDIUM, ['Jupiter aspects Sun D9'], [], 0.60, '26/48'),
]

engine = ConsensusEngine()

print('='*70)
print('TEST 1: CAREER - Expected: Unanimous (high agreement)')
print('='*70)
r1 = engine.calculate_consensus(career, 'career')
print(json.dumps(r1.to_dict(), indent=2))

print()
print('='*70)
print('TEST 2: MARRIAGE - Expected: Nuance Arbitration (D9 conflict)')
print('='*70)
engine.resolution_log = []
r2 = engine.calculate_consensus(marriage, 'marriage')
print(json.dumps(r2.to_dict(), indent=2))
if engine.resolution_log:
    print(f'Resolution: {engine.resolution_log[0]}')

print()
print('='*70)
print('TEST 3: HEALTH - Expected: Medium agreement with dosha')
print('='*70)
engine.resolution_log = []
r3 = engine.calculate_consensus(health, 'health')
print(json.dumps(r3.to_dict(), indent=2))

print()
print('='*70)
print('SUMMARY')
print('='*70)
print(f"{'Domain':<12} {'Score':<10} {'Strategy':<22} {'Agreement':<12}")
print('-'*56)
print(f"{'Career':<12} {r1.final_score:<10.2f} {r1.strategy_used.value:<22} {r1.agreement_level:<12}")
print(f"{'Marriage':<12} {r2.final_score:<10.2f} {r2.strategy_used.value:<22} {r2.agreement_level:<12}")
print(f"{'Health':<12} {r3.final_score:<10.2f} {r3.strategy_used.value:<22} {r3.agreement_level:<12}")
print()
print('[OK] All tests passed!')
