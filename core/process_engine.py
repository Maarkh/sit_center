# core/process_engine.py
"""DSS M8 (MVP) — executable regulation / workflow engine.

Wave model: assignments are grouped by step_order. The *current wave* is the lowest
step_order that still has a non-terminal assignment (pending / active / in_progress).
Steps within a wave run in parallel; the wave only advances once every step in it is
terminal (done / skipped). This naturally expresses both sequential (increasing
orders) and parallel (shared order) regulations.

The wave arithmetic (current_wave_order / is_instance_complete) is pure and
unit-tested without a DB. Persistence and notifications live in ProcessEngine.
"""
import os
from typing import List, Optional, Dict, Any
from sqlalchemy import text

from core.database import get_engine
from core.audit import log_audit
from config import logger, mask_secrets

TERMINAL = {"done", "skipped"}
NON_TERMINAL = {"pending", "active", "in_progress"}

# Upper bound on the steps a single instance may snapshot. The wave model is flat
# and monotonic (each step is terminal-once, so an instance always finishes in ≤N
# completions — no recursion, no loop construct), but a pathological or hostile
# template could still define an unbounded number of steps and explode the
# step_assignments table on instantiate. Reject those up front. Configurable.
MAX_PROCESS_STEPS = int(os.environ.get("MAX_PROCESS_STEPS", "500"))

# OODA Act→Observe: how long after a deviation-linked process completes to re-measure
# and confirm the breach actually cleared. Gives the remediation time to take effect.
REMEDIATION_VERIFY_DELAY_SECONDS = int(os.environ.get("REMEDIATION_VERIFY_DELAY_SECONDS", "300"))


def current_wave_order(assignments: List[Dict[str, Any]]) -> Optional[int]:
    """Lowest step_order with a non-terminal assignment, or None if all terminal."""
    orders = [a["step_order"] for a in assignments if a["status"] in NON_TERMINAL]
    return min(orders) if orders else None


def is_instance_complete(assignments: List[Dict[str, Any]]) -> bool:
    return current_wave_order(assignments) is None


class ProcessError(Exception):
    """Raised for invalid process transitions (mapped to HTTP 409 by the route)."""


class ProcessEngine:
    # -- instantiation -----------------------------------------------------
    def instantiate(self, template_id, tenant_id: str, *, started_by: str,
                    title: Optional[str] = None, incident_id: Optional[int] = None,
                    deviation_id=None) -> str:
        """Create an instance, snapshot the template's steps into assignments, and
        activate the first wave. Returns the new instance id."""
        engine = get_engine()
        with engine.begin() as conn:
            tmpl = conn.execute(
                text("SELECT id, name FROM process_templates WHERE id = :id AND tenant_id = :tid "
                     "AND is_active = true"),
                {"id": template_id, "tid": tenant_id},
            ).mappings().first()
            if not tmpl:
                raise ProcessError("template not found or inactive")

            steps = conn.execute(
                text(
                    "SELECT id, step_order, name, step_type, assignee_role, checklist, "
                    "due_after_minutes FROM process_steps WHERE template_id = :tid_ ORDER BY step_order"
                ),
                {"tid_": template_id},
            ).mappings().all()
            if not steps:
                raise ProcessError("template has no steps")
            if len(steps) > MAX_PROCESS_STEPS:
                raise ProcessError(
                    f"template has {len(steps)} steps, exceeding the {MAX_PROCESS_STEPS} "
                    f"limit (raise MAX_PROCESS_STEPS to allow)"
                )

            inst_id = conn.execute(
                text(
                    "INSERT INTO process_instances (tenant_id, template_id, incident_id, "
                    "deviation_id, title, status, started_by) "
                    "VALUES (:tid, :tmpl, :inc, :dev, :title, 'running', :by) RETURNING id"
                ),
                {"tid": tenant_id, "tmpl": template_id, "inc": incident_id, "dev": deviation_id,
                 "title": title or tmpl["name"], "by": started_by},
            ).scalar()

            for s in steps:
                checklist = s["checklist"] or []
                state = [{"item": str(i), "done": False} for i in checklist]
                conn.execute(
                    text(
                        "INSERT INTO step_assignments (tenant_id, instance_id, step_id, step_order, "
                        "step_type, name, assignee_role, checklist_state, status, due_after_minutes) "
                        "VALUES (:tid, :inst, :sid, :ord, :type, :name, :role, "
                        "CAST(:state AS jsonb), 'pending', :due)"
                    ),
                    {"tid": tenant_id, "inst": inst_id, "sid": s["id"], "ord": s["step_order"],
                     "type": s["step_type"], "name": s["name"], "role": s["assignee_role"],
                     "state": _json(state), "due": s["due_after_minutes"]},
                )

            self._activate_wave(conn, inst_id, tenant_id)
        log_audit(started_by, tenant_id, "create", "process_instance", resource_id=str(inst_id))
        return str(inst_id)

    # -- wave activation ---------------------------------------------------
    def _activate_wave(self, conn, instance_id, tenant_id: str):
        """Activate pending steps in the current wave; complete the instance if none."""
        rows = conn.execute(
            text(
                "SELECT id, step_order, status, due_after_minutes FROM step_assignments "
                "WHERE instance_id = :id ORDER BY step_order"
            ),
            {"id": instance_id},
        ).mappings().all()
        assignments = [dict(r) for r in rows]
        wave = current_wave_order(assignments)

        if wave is None:
            conn.execute(
                text(
                    "UPDATE process_instances SET status = 'completed', completed_at = NOW() "
                    "WHERE id = :id AND status = 'running'"
                ),
                {"id": instance_id},
            )
            return

        for a in assignments:
            if a["step_order"] == wave and a["status"] == "pending":
                due_expr = (
                    "NOW() + make_interval(mins => :due)" if a["due_after_minutes"] else "NULL"
                )
                conn.execute(
                    text(
                        f"UPDATE step_assignments SET status = 'active', activated_at = NOW(), "
                        f"due_at = {due_expr} WHERE id = :id"
                    ),
                    {"id": a["id"], "due": a["due_after_minutes"]} if a["due_after_minutes"]
                    else {"id": a["id"]},
                )

    # -- step transitions --------------------------------------------------
    def start_step(self, assignment_id, tenant_id: str, *, user: str,
                   assignee: Optional[str] = None) -> dict:
        engine = get_engine()
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM step_assignments WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
                {"id": assignment_id, "tid": tenant_id},
            ).mappings().first()
            if not row:
                raise ProcessError("assignment not found")
            if row["status"] not in ("active", "in_progress"):
                raise ProcessError(f"cannot start a step in '{row['status']}' state")
            conn.execute(
                text(
                    "UPDATE step_assignments SET status = 'in_progress', "
                    "assignee = COALESCE(:assignee, assignee, :user), "
                    "started_at = COALESCE(started_at, NOW()) WHERE id = :id"
                ),
                {"id": assignment_id, "assignee": assignee, "user": user},
            )
            return self._load_assignment(conn, assignment_id)

    def update_checklist(self, assignment_id, tenant_id: str, checklist_state: list) -> dict:
        engine = get_engine()
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status FROM step_assignments WHERE id = :id AND tenant_id = :tid FOR UPDATE"),
                {"id": assignment_id, "tid": tenant_id},
            ).mappings().first()
            if not row:
                raise ProcessError("assignment not found")
            if row["status"] in TERMINAL:
                raise ProcessError("cannot edit a completed step")
            conn.execute(
                text("UPDATE step_assignments SET checklist_state = CAST(:state AS jsonb) WHERE id = :id"),
                {"id": assignment_id, "state": _json(checklist_state)},
            )
            return self._load_assignment(conn, assignment_id)

    def complete_step(self, assignment_id, tenant_id: str, *, user: str,
                      report: Optional[str] = None, force: bool = False) -> dict:
        """Mark a step done, then activate the next wave (or finish the instance)."""
        engine = get_engine()
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT instance_id, status, checklist_state FROM step_assignments "
                    "WHERE id = :id AND tenant_id = :tid FOR UPDATE"
                ),
                {"id": assignment_id, "tid": tenant_id},
            ).mappings().first()
            if not row:
                raise ProcessError("assignment not found")
            if row["status"] in TERMINAL:
                raise ProcessError("step already completed")
            if row["status"] == "pending":
                raise ProcessError("step is not active yet (waiting on an earlier step)")
            if not force:
                undone = [c for c in (row["checklist_state"] or []) if not c.get("done")]
                if undone:
                    raise ProcessError(f"{len(undone)} checklist item(s) not done; pass force=true to override")

            conn.execute(
                text(
                    "UPDATE step_assignments SET status = 'done', report = :report, "
                    "completed_by = :user, completed_at = NOW() WHERE id = :id"
                ),
                {"id": assignment_id, "report": report, "user": user},
            )
            instance_id = row["instance_id"]
            self._activate_wave(conn, instance_id, tenant_id)
            assignment = self._load_assignment(conn, assignment_id)
            # Did THIS completion finish the whole instance, and was it remediating a
            # deviation? Capture inside the txn; schedule the Observe re-check after commit.
            inst = conn.execute(
                text("SELECT status, deviation_id FROM process_instances "
                     "WHERE id = :id AND tenant_id = :tid"),
                {"id": instance_id, "tid": tenant_id},
            ).mappings().first()
        log_audit(user, tenant_id, "complete", "process_step", resource_id=str(assignment_id))
        if inst and inst["status"] == "completed" and inst["deviation_id"]:
            self._schedule_remediation_verify(inst["deviation_id"], tenant_id)
        return assignment

    def _schedule_remediation_verify(self, deviation_id, tenant_id: str):
        """OODA Act→Observe: enqueue a delayed re-measure to confirm the deviation
        this process addressed actually cleared. Best-effort — never block completion."""
        try:
            from celery_app import celery_app
            celery_app.send_task(
                "core.dss_tasks.verify_remediation_task",
                args=[str(deviation_id), tenant_id],
                countdown=REMEDIATION_VERIFY_DELAY_SECONDS,
            )
            logger.info("scheduled remediation verify for deviation %s in %ds",
                        deviation_id, REMEDIATION_VERIFY_DELAY_SECONDS)
        except Exception as e:
            logger.error("could not schedule remediation verify for %s: %s",
                         deviation_id, mask_secrets(str(e)))

    def cancel_instance(self, instance_id, tenant_id: str, *, user: str) -> None:
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE process_instances SET status = 'cancelled', completed_at = NOW() "
                    "WHERE id = :id AND tenant_id = :tid AND status = 'running'"
                ),
                {"id": instance_id, "tid": tenant_id},
            )
            if result.rowcount == 0:
                raise ProcessError("instance not found or not running")
        log_audit(user, tenant_id, "cancel", "process_instance", resource_id=str(instance_id))

    # -- SLA escalation (M8 ↔ M9) -----------------------------------------
    def escalate_overdue_steps(self, tenant_id: str = "default") -> int:
        """Notify on active/in_progress steps past due_at that haven't been escalated."""
        engine = get_engine()
        with engine.begin() as conn:
            overdue = conn.execute(
                text(
                    "SELECT id, name, assignee_role, assignee, instance_id FROM step_assignments "
                    "WHERE tenant_id = :tid AND escalated = false AND due_at IS NOT NULL "
                    "AND due_at < NOW() AND status IN ('active', 'in_progress') FOR UPDATE"
                ),
                {"tid": tenant_id},
            ).mappings().all()
            for a in overdue:
                conn.execute(
                    text("UPDATE step_assignments SET escalated = true WHERE id = :id"),
                    {"id": a["id"]},
                )
        for a in overdue:
            who = a["assignee"] or a["assignee_role"] or "—"
            msg = f"Шаг процесса просрочен: '{a['name']}' (ответственный: {who})"
            try:
                from core.notifications import notify
                notify(msg, "warning")
            except Exception as e:
                logger.error("process step escalation notify failed: %s", mask_secrets(str(e)))
        return len(overdue)

    # -- loaders -----------------------------------------------------------
    def _load_assignment(self, conn, assignment_id) -> dict:
        row = conn.execute(
            text(
                "SELECT id, instance_id, step_id, step_order, step_type, name, assignee_role, "
                "assignee, checklist_state, status, report, due_at, escalated, started_at, "
                "activated_at, completed_at, completed_by FROM step_assignments WHERE id = :id"
            ),
            {"id": assignment_id},
        ).mappings().first()
        return dict(row) if row else {}


def _json(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


process_engine = ProcessEngine()
