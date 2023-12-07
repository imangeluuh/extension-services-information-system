from app.models import Announcement, ExtensionProgram, Activity, Project
from flask import render_template
from sqlalchemy import desc
from datetime import datetime
from app.main import bp

@bp.route("/")
def home():
    latest_announcements = Announcement.query.order_by(desc(Announcement.Updated)).limit(5).all()
    extension_programs = ExtensionProgram.query.all()
    events = Activity.query.with_entities(Activity.ActivityName, Activity.Date, Project.Title).join(Project).filter(Activity.Date >= datetime.now().date()).all()
    events_list = Activity.query.join(Project).filter(Activity.Date >= datetime.now().date()).limit(5).all()
    return render_template('index.html', latest_announcements=latest_announcements, extension_programs=extension_programs, events=events, events_list=events_list)