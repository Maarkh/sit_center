# core/rule_engine.py
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine
from core.metadata_service import metadata_service, RuleDTO


@dataclass
class ParsedCondition:
    metric_name: str
    labels: Dict[str, str]
    operator: str
    threshold: float


@dataclass
class EvalResult:
    rule_id: str
    rule_name: str
    metric_name: str
    dimensions: Dict[str, str]
    current_value: float
    threshold: float
    operator: str
    fired: bool


_CONDITION_RE = re.compile(
    r'^([a-zA-Z0-9_\-\.]+)'       # metric name
    r'(?:\{([^}]*)\})?'           # optional {label='val', ...}
    r'\s*([><=!]+)\s*'            # operator
    r'([\d.]+)$'                  # threshold
)

_ALLOWED_OPS = {">", "<", ">=", "<=", "==", "!="}


class PromQLParser:
    @staticmethod
    def parse(expr: str) -> Optional[ParsedCondition]:
        expr = expr.strip()
        m = _CONDITION_RE.match(expr)
        if not m:
            logger.warning("Failed to parse rule expression: %s", expr)
            return None

        metric_name, labels_str, operator, threshold_str = m.groups()

        if operator not in _ALLOWED_OPS:
            logger.warning("Invalid operator in rule: %s", operator)
            return None

        labels: Dict[str, str] = {}
        if labels_str:
            for pair in labels_str.split(","):
                pair = pair.strip()
                if "=" not in pair:
                    continue
                k, v = pair.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if re.match(r'^[a-zA-Z0-9_\-]{1,50}$', k):
                    labels[k] = v

        return ParsedCondition(
            metric_name=metric_name,
            labels=labels,
            operator=operator,
            threshold=float(threshold_str),
        )


class RuleEngine:
    def __init__(self):
        self.parser = PromQLParser()

    def evaluate_all_rules(self) -> List[EvalResult]:
        rules = metadata_service.list_active_rules()
        results: List[EvalResult] = []

        for rule in rules:
            try:
                rule_results = self._evaluate_rule(rule)
                results.extend(rule_results)
            except Exception as e:
                logger.error("Error evaluating rule %s: %s", rule.name, mask_secrets(str(e)))

        return results

    def _evaluate_rule(self, rule: RuleDTO) -> List[EvalResult]:
        condition = rule.condition
        expr = condition.get("expr") if isinstance(condition, dict) else getattr(condition, "expr", None)
        if not expr:
            return []

        parsed = self.parser.parse(expr)
        if not parsed:
            return []

        # Query the latest values for this metric, grouped by dimensions
        engine = get_engine()
        where_parts = ["metric_name = :metric_name", "timestamp >= NOW() - INTERVAL '5 minutes'"]
        params: Dict[str, Any] = {"metric_name": parsed.metric_name}

        for i, (k, v) in enumerate(parsed.labels.items()):
            where_parts.append(f"dimensions->>:key_{i} = :val_{i}")
            params[f"key_{i}"] = k
            params[f"val_{i}"] = v

        query = text(f"""
            SELECT dimensions, AVG(value) AS avg_value
            FROM canonical_metrics
            WHERE {" AND ".join(where_parts)}
            GROUP BY dimensions
            LIMIT 1000
        """)

        results: List[EvalResult] = []
        try:
            with engine.connect() as conn:
                rows = conn.execute(query, params).mappings().all()

            for row in rows:
                avg_val = float(row["avg_value"])
                fired = _compare(avg_val, parsed.operator, parsed.threshold)
                results.append(EvalResult(
                    rule_id=str(rule.id),
                    rule_name=rule.name,
                    metric_name=parsed.metric_name,
                    dimensions=row["dimensions"] or {},
                    current_value=avg_val,
                    threshold=parsed.threshold,
                    operator=parsed.operator,
                    fired=fired,
                ))
        except Exception as e:
            logger.error("Rule evaluation query failed for %s: %s", rule.name, mask_secrets(str(e)))

        return results


def _compare(value: float, op: str, threshold: float) -> bool:
    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    return ops.get(op, lambda a, b: False)(value, threshold)


rule_engine = RuleEngine()
