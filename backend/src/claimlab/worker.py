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
    job_id = job.id
    db = SessionLocal()
    try:
        db_job = db.get(Job, job_id)
        if not db_job:
            logger.error(f"Job {job_id} not found in database")
            return
        logger.info(f"Processing job {db_job.id} (kind: {db_job.kind}) for session {db_job.session_id}")

        # Cooperative cancellation check
        if db_job.cancelled:
            logger.info(f"Job {db_job.id} was cancelled before execution")
            db_job.status = JobStatus.CANCELLED.value
            db.commit()
            return

        # Extend lease for turn execution (180s)
        db_job.lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=180)
        db.commit()

        if db_job.kind == JobKind.TUTOR_TURN.value:
            if not db_job.session_id:
                raise ValueError("tutor_turn job requires session_id")
            orchestrator = AgentOrchestrator(db)
            orchestrator.execute_tutor_turn(db_job.session_id, db_job.id)

        db.refresh(db_job)
        if db_job.cancelled or db_job.status == JobStatus.CANCELLED.value:
            logger.info(f"Job {db_job.id} was cancelled during execution; preserving CANCELLED status")
        else:
            db_job.status = JobStatus.SUCCEEDED.value
            db_job.progress = 1.0
        db.commit()
        logger.info(f"Job {db_job.id} completed with status {db_job.status}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        try:
            db_job = db.get(Job, job_id)
            if db_job:
                db_job.status = JobStatus.FAILED.value
                db_job.error_code = "EXECUTION_ERROR"
                db_job.error_message = str(e)
                db.commit()
        except Exception:
            pass

    finally:
        # Atomically release active session slot if held by this job
        try:
            db_job = db.get(Job, job_id)
            if db_job and db_job.session_id:
                sess = db.query(LearningSession).filter(LearningSession.id == db_job.session_id).first()
                if sess and sess.active_job_id == db_job.id:
                    sess.active_job_id = None
                    db.commit()
        except Exception:
            pass
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
