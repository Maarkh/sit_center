# core/utils.py
import json
from datetime import datetime
from typing import Any, List, Dict
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any: # type: ignore
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_anomalies(anomalies: List[Dict[str, Any]]) -> str:
    return json.dumps(anomalies, cls=NpEncoder, ensure_ascii=False)

def deserialize_anomalies(data_str: str) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = json.loads(data_str)
    for item in data:
        if "timestamp" in item:
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
    return data