"""Durable single-instance job worker with heartbeat leasing and cooperative cancellation."""
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from claimlab.database import SessionLocal
from claimlab.models import Job, LearningSession
from claimlab.contracts.common import JobStatus, JobKind
from claimlab.services.agent_orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("claimlab.worker")

HEARTBEAT_INTERVAL_SECONDS = 5
LEASE_DURATION_SECONDS = 30


def claim_next_job(db) -> Optional[Job]:
    """Atomically claims the next available queued job."""
    now = datetime.now(timezone.utc)
    job = (
        db.query(Job)
        .filter(Job.status == JobStatus.QUEUED.value, Job.cancelled.is_(False))
        .order_by(Job.created_at.asc())
        .first()
    )
    if job:
        job.status = JobStatus.RUNNING.value
        job.lease_expires_at = now + timedelta(seconds=LEASE_DURATION_SECONDS)
        db.commit()
        db.refresh(job)
        return job
    return None


def execute_job(job: Job) -> None:
    """Dispatches execution based on job kind."""
    db = SessionLocal()
    try:
        logger.info(f"Processing job {job.id} (kind: {job.kind}) for session {job.session_id}")

        # Cooperative cancellation check
        db.refresh(job)
        if job.cancelled:
            logger.info(f"Job {job.id} was cancelled before execution")
            job.status = JobStatus.CANCELLED.value
            db.commit()
            return

        if job.kind == JobKind.TUTOR_TURN.value:
            if not job.session_id:
                raise ValueError("tutor_turn job requires session_id")
            orchestrator = AgentOrchestrator(db)
            orchestrator.execute_tutor_turn(job.session_id, job.id)

        job.status = JobStatus.SUCCEEDED.value
        job.progress = 1.0
        db.commit()
        logger.info(f"Job {job.id} succeeded")

    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}", exc_info=True)
        db.refresh(job)
        job.status = JobStatus.FAILED.value
        job.error_code = "EXECUTION_ERROR"
        job.error_message = str(e)
        db.commit()

    finally:
        # Atomically release active session slot if held by this job
        if job.session_id:
            sess = db.query(LearningSession).filter(LearningSession.id == job.session_id).first()
            if sess and sess.active_job_id == job.id:
                sess.active_job_id = None
                db.commit()
        db.close()


def run_worker_loop(poll_interval: float = 1.0, once: bool = False) -> None:
    """Continuously polls for and executes durable jobs."""
    logger.info("ClaimLab Durable Worker started. Waiting for jobs...")
    while True:
        db = SessionLocal()
        try:
            # Check for expired running leases (WORKER_LOST)
            now = datetime.now(timezone.utc)
            stale_jobs = (
                db.query(Job)
                .filter(
                    Job.status == JobStatus.RUNNING.value,
                    Job.lease_expires_at.isnot(None),
                    Job.lease_expires_at < now,
                )
                .all()
            )
            for sj in stale_jobs:
                logger.warning(f"Marking stale job {sj.id} as FAILED (WORKER_LOST)")
                sj.status = JobStatus.FAILED.value
                sj.error_code = "WORKER_LOST"
                sj.error_message = "Worker lease expired before job completed"
                if sj.session_id:
                    sess = db.query(LearningSession).filter(LearningSession.id == sj.session_id).first()
                    if sess and sess.active_job_id == sj.id:
                        sess.active_job_id = None
                        sess.fencing_generation += 1
                db.commit()

            # Claim next job
            job = claim_next_job(db)
            if job:
                execute_job(job)
                if once:
                    break
            else:
                if once:
                    break
                time.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(poll_interval)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker_loop()
