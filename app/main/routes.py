from app.models import Announcement, ExtensionProgram, Activity, Project
from flask import render_template
from datetime import datetime
from app.main import bp

@bp.route("/")
def home():
    latest_announcements = Announcement.query.filter_by(IsLive=True).order_by(Announcement.Updated.desc()).limit(5).all()
    extension_programs = ExtensionProgram.query.all()
    events = Activity.query.filter(Activity.Date > datetime.utcnow().date()).limit(5).all()
    return render_template('index.html', latest_announcements=latest_announcements, extension_programs=extension_programs, events=events)