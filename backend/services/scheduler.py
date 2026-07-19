"""
RetailMind AI - Scheduler Service using APScheduler
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_announcement_jobs = {}
_app = None


def init_scheduler(app):
    """Initialize the scheduler with the Flask app."""
    global _app
    _app = app
    with app.app_context():
        # Job: Expire old offers (run every hour)
        scheduler.add_job(
            func=expire_old_offers,
            trigger='interval',
            hours=1,
            id='expire_offers',
            replace_existing=True,
            kwargs={'app': app}
        )
        
        # Start scheduler
        if not scheduler.running:
            scheduler.start()
            logger.info('APScheduler started')


def expire_old_offers(app=None):
    """Automatically expire offers past their end date."""
    if app is None:
        return
    
    with app.app_context():
        from models import db, Offer
        
        now = datetime.utcnow()
        expired = Offer.query.filter(
            Offer.is_active == True,
            Offer.end_date != None,
            Offer.end_date <= now
        ).all()
        
        for offer in expired:
            offer.is_active = False
            logger.info(f'Offer "{offer.title}" auto-expired')
        
        if expired:
            db.session.commit()
            logger.info(f'{len(expired)} offers auto-expired')


def register_announcement_schedule(announcement_id, interval_minutes):
    """Register a scheduled announcement job."""
    job_id = f'announcement_{announcement_id}'
    
    # Remove existing job if any
    if job_id in _announcement_jobs:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
    
    # Add new scheduled job
    scheduler.add_job(
        func=play_announcement,
        trigger='interval',
        minutes=interval_minutes,
        id=job_id,
        replace_existing=True,
        kwargs={'announcement_id': announcement_id, 'app': _app}
    )
    
    _announcement_jobs[job_id] = announcement_id
    logger.info(f'Announcement {announcement_id} scheduled every {interval_minutes} min')


def unregister_announcement_schedule(announcement_id):
    """Remove a scheduled announcement job."""
    job_id = f'announcement_{announcement_id}'
    
    try:
        scheduler.remove_job(job_id)
        logger.info(f'Announcement {announcement_id} schedule removed')
    except Exception:
        pass
    
    _announcement_jobs.pop(job_id, None)


def play_announcement(announcement_id, app=None):
    """Mark announcement as played (actual audio playback handled by frontend)."""
    if app is None:
        return
    
    with app.app_context():
        from models import db, Announcement
        
        announcement = Announcement.query.get(announcement_id)
        if announcement and announcement.is_active:
            announcement.last_played = datetime.utcnow()
            db.session.commit()
            logger.info(f'Announcement {announcement_id} marked as played')
        else:
            # Auto-unregister if inactive
            unregister_announcement_schedule(announcement_id)


def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info('APScheduler shutdown')
