from app.announcement import bp
from flask import render_template, url_for, request, redirect, flash, session
from flask_login import login_user, logout_user, current_user
from ..decorators.decorators import login_required
from ..models import Project, ExtensionProgram, Program, Announcement, Registration, User
from .forms import AnnouncementForm
from ..email import sendEmail
import string
from datetime import datetime
from sqlalchemy import desc
from app import db


def generateSlug(title, separator='-', lower=True):
    title = title.translate(str.maketrans('', '', string.punctuation))
    if lower:
        title = title.lower()
    return separator.join(title.split())

# Announcement filter
@bp.route('filter/extension-program')
@login_required(role=["Admin", "Faculty"])
def extensionProgram():
    program_abbreviation = request.args.get('program')
    program = Program.query.filter_by(Abbreviation=program_abbreviation).first()
    ext_programs = [ext_program for ext_program in program.ExtensionPrograms]
    return render_template('announcement/ext_program_options.html', ext_programs=ext_programs)

@bp.route('filter/project')
@login_required(role=["Admin", "Faculty"])
def project():
    ext_program_id = request.args.get('extension-program')
    ext_program = ExtensionProgram.query.filter_by(ExtensionProgramId=ext_program_id).first()
    projects = [project for project in ext_program.Projects]
    return render_template('announcement/project_options.html', projects=projects)

@bp.route('filter/announcement')
@login_required(role=["Admin", "Faculty"])
def filterAnnouncement():
    project_id = request.args.get('project')
    if project_id:
        published_announcements = Announcement.query.filter_by(IsLive=True, ProjectId=project_id).order_by(Announcement.Updated.desc()).all()
        draft_announcements = Announcement.query.filter_by(IsLive=False, ProjectId=project_id).order_by(Announcement.Updated.desc()).all()
    else:
        published_announcements = Announcement.query.filter_by(IsLive=True).order_by(Announcement.Updated.desc()).all()
        draft_announcements = Announcement.query.filter_by(IsLive=False).order_by(Announcement.Updated.desc()).all()

    return render_template('announcement/announcements_list.html', published_announcements=published_announcements, draft_announcements=draft_announcements)
# End: Announcement filter

@bp.route('/announcements/<string:project>')
@bp.route('/announcements', defaults={'project': None})
@login_required(role=["Admin"])
def manageAnnouncements(project):    
    programs = Program.query.all()
    return render_template('announcement/announcement_management.html', programs=programs)

@bp.route('/announcement/create', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def createAnnouncement():
    form = AnnouncementForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if 'publish' in request.form:
                if not all(request.form.values()):
                    # Save the input to session
                    session['announcement_title']= form.title.data
                    session['announcement_body'] = form.content.data
                    flash('Please fill out all the fields before publishing.', category='error')
                    return redirect(url_for('announcement.createAnnouncement'))
                is_live = 1
            elif 'draft' in request.form:
                is_live = 0
            announcement_to_create = Announcement(Title=form.title.data,
                                                Content=form.content.data,
                                                CreatorId=current_user.UserId,
                                                IsLive=is_live,
                                                Slug=generateSlug(form.title.data),
                                                ProjectId=form.project.data)
            db.session.add(announcement_to_create)
            db.session.commit()
            # If announcement session is not empty, clear the session after saving to database
            if 'announcement_title' in session:
                session.pop('announcement_title', None)
            if 'announcement_body' in session:
                session.pop('announcement_body', None)
            # If Email checkbox is checked, send the announcement to desired recipients
            if 'Email' in form.medium.data and form.recipient.data is not [] and is_live == 1:
                if len(form.recipient.data) == 2:
                    emails = (
                        User.query
                        .join(Registration)
                        .join(Project)
                        .filter(Project.ProjectId == 10)
                        .with_entities(User.Email)
                        .all()
                    )
                else:
                    emails = (
                        User.query
                        .join(Registration)
                        .join(Project)
                        .filter(Project.ProjectId == 10, User.RoleId == form.recipient.data[0])
                        .with_entities(User.Email)
                        .all()
                    )
                # Extract the emails from the query result
                list_email = [email for (email,) in emails]
                sendEmail(form.title.data, list_email, form.content.data, form.content.data)
                flash('Announcement is successfully sent to email', category='success')
            flash('Announcement is successfully inserted.', category='success')
            return redirect(url_for('announcement.manageAnnouncements'))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    if 'announcement_title' in session:
        form.title.data = session['announcement_title']
    if 'announcement_body' in session:
        form.content.data = session['announcement_body']
    return render_template('announcement/announcement_form.html', form=form)

@bp.route('/announcement/<int:id>/<string:slug>')
def viewAnnouncement(id, slug):
    announcement = Announcement.query.filter_by(AnnouncementId=id, Slug=slug).first()
    print(announcement)
    return render_template('announcement/view_announcement.html', announcement=announcement)

@bp.route('/unpublish/announcement/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def unpublishAnnouncement(id):
    announcement = Announcement.query.get_or_404(id)
    announcement.IsLive = 0
    try:
        db.session.commit()
        flash('Announcement is successfully unpublished.', category='success')
    except:
        flash('There was an issue unpublishing the announcement.', category='error')

    return redirect(url_for('announcement.manageAnnouncements'))

@bp.route('/delete/announcement/<int:id>', methods=['POST'])
@login_required(role=["Admin"])
def deleteAnnouncement(id):
    announcement = Announcement.query.get_or_404(id)
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement is successfully deleted.', category='success')
    except:
        flash('There was an issue deleting the announcement.', category='error')

    return redirect(url_for('announcement.manageAnnouncements'))



@bp.route('/announcement/update/<int:id>', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def updateAnnouncement(id):
    form = AnnouncementForm()
    announcement = Announcement.query.get_or_404(id)
    current_url_path = request.path

    if request.method == "POST":
        if form.validate_on_submit():
            if 'publish' in request.form:
                if not all(request.form.values()):
                    flash('Please fill out all the fields before publishing.', category='error')
                    return redirect(url_for('announcement.updateAnnouncement', id=id))
                is_live = 1
            elif 'draft' in request.form:
                is_live = 0

            announcement.Title=form.title.data
            announcement.Content=form.content.data
            announcement.IsLive=is_live
            announcement.Slug=generateSlug(form.title.data)

            try:
                db.session.commit()
                flash('Announcement is successfully updated.', category='success')
            except Exception as e:
                flash('There was an issue updating the announcement.', category='error')

            return redirect(url_for('announcement.viewAnnouncement', id=id, slug=announcement.Slug))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    
    form.title.data = announcement.Title
    form.content.data = announcement.Content
    form.project.data = announcement.ProjectId

    return render_template('announcement/announcement_form.html', form=form, announcement=announcement, current_url_path=current_url_path)


# @bp.route('/announcement')
# def announcement():
#     announcements = Announcement.query.order_by(desc(Announcement.Updated)).all()
#     return render_template('announcement/announcements.html', announcements=announcements)

