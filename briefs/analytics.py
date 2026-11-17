"""Product analytics as structured log lines (one JSON object per event).

Ship logs to any log drain / warehouse to compute the brief adoption rate:
    count(brief_copied) / count(brief_generated), joined on request_id.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("briefs.analytics")

CLIENT_EVENTS = frozenset({"brief_copied", "brief_edited", "brief_regenerated"})


def track(event: str, **props: Any) -> None:
    record = {"event": event, "ts": datetime.now(UTC).isoformat(timespec="seconds"), **props}
    logger.info(json.dumps(record, sort_keys=True))
