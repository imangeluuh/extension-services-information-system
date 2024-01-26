from app.models import Announcement, ExtensionProgram, Activity, Project
from flask import render_template
from flask_login import current_user
from datetime import datetime
from app.main import bp
from ..decorators.decorators import role_excluded

@bp.route("/")
@role_excluded(role=["Admin", "Faculty"])
def home():
    user_role_id = current_user.RoleId if current_user.is_authenticated else None
    latest_announcements = None
    if user_role_id == 3:  # Student
        latest_announcements = Announcement.query.filter(
            (Announcement.Recipient.contains('3') | Announcement.Recipient.contains('2,3')) &
            Announcement.IsLive
        ).order_by(Announcement.Created.desc()).limit(5).all()
    elif user_role_id == 2:  # Beneficiary
        latest_announcements = Announcement.query.filter(
            (Announcement.Recipient.contains('2') | Announcement.Recipient.contains('2,3')) &
            Announcement.IsLive
        ).order_by(Announcement.Created.desc()).limit(5).all()
    extension_programs = ExtensionProgram.query.all()
    events = Activity.query.filter(Activity.Date > datetime.utcnow().date()).order_by(Activity.Date.asc()).limit(5).all()
    return render_template('index.html', latest_announcements=latest_announcements, extension_programs=extension_programs, events=events)