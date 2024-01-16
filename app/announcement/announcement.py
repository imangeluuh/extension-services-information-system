from app.announcement import bp
from flask import render_template, url_for, request, redirect, flash, session, current_app
from flask_login import current_user
from ..decorators.decorators import login_required
from ..models import Project, ExtensionProgram,  Announcement, Registration, User, Course
from .forms import AnnouncementForm
from ..email import sendEmail
import string, os
from app import db
from ..programs.programs import saveImage
from ..store import uploadImage, purgeImage
from werkzeug.utils import secure_filename
from sqlalchemy import desc, select

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
    program = Course.query.filter_by(CourseCode=program_abbreviation).first()
    ext_programs = [ext_program for ext_program in program.ExtensionPrograms]
    return render_template('announcement/ext_program_options.html', ext_programs=ext_programs)

@bp.route('filter/project')
@login_required(role=["Admin", "Faculty"])
def project():
    ext_program_id = request.args.get('extension-program')
    ext_program = ExtensionProgram.query.filter_by(ExtensionProgramId=ext_program_id).first()
    projects = None
    if current_user.RoleId == 1:
        projects = [project for project in ext_program.Projects]
    else:
        projects = [project for project in Project.query.filter_by(ExtensionProgramId=ext_program_id, LeadProponentId=current_user.UserId).all()]
    return render_template('announcement/project_options.html', projects=projects)

@bp.route('filter/announcement')
@login_required(role=["Admin", "Faculty"])
def filterAnnouncement():
    project_id = request.args.get('project')
    if project_id:
        if current_user.RoleId == 4:
            published_announcements = Announcement.query.join(Project) \
                                                        .filter(Announcement.IsLive==True
                                                                , Announcement.ProjectId==project_id
                                                                , Project.LeadProponentId==current_user.UserId).order_by(Announcement.Updated.desc()).all()
            draft_announcements = Announcement.query.join(Project) \
                                                        .filter(Announcement.IsLive==False
                                                                , Announcement.ProjectId==project_id
                                                                , Project.LeadProponentId==current_user.UserId).order_by(Announcement.Updated.desc()).all()
        else:
            published_announcements = Announcement.query.filter_by(IsLive=True, ProjectId=project_id).order_by(Announcement.Updated.desc()).all()
            draft_announcements = Announcement.query.filter_by(IsLive=False, ProjectId=project_id).order_by(Announcement.Updated.desc()).all()
    else:
        if current_user.RoleId == 4:
            published_announcements = Announcement.query.join(Project) \
                                                        .filter(Announcement.IsLive==True
                                                                , Project.LeadProponentId==current_user.UserId).order_by(Announcement.Updated.desc()).all()
            draft_announcements = Announcement.query.join(Project) \
                                                        .filter(Announcement.IsLive==False
                                                                , Project.LeadProponentId==current_user.UserId).order_by(Announcement.Updated.desc()).all()
        else:
            published_announcements = Announcement.query.filter_by(IsLive=True).order_by(Announcement.Updated.desc()).all()
            draft_announcements = Announcement.query.filter_by(IsLive=False).order_by(Announcement.Updated.desc()).all()

    return render_template('announcement/announcements_list.html', published_announcements=published_announcements, draft_announcements=draft_announcements)
# End: Announcement filter

@bp.route('/announcements/<string:project>')
@bp.route('/announcements', defaults={'project': None})
@login_required(role=["Admin", "Faculty"])
def manageAnnouncements(project):    
    programs = Course.query.all()
    return render_template('announcement/announcement_management.html', programs=programs)

@bp.route('/announcement/create', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def createAnnouncement():
    form = AnnouncementForm()
    recipients_string = ""
    if request.method == "POST":
        if form.validate_on_submit():
            str_image_url = None
            str_image_id = None
            if form.image.data is not None:
                # Get the input image path
                imagepath = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], secure_filename(form.image.data.filename)
                    )
                # Save image
                status = saveImage(form.image.data, imagepath)
                if status.error is not None:
                    flash("File Upload Error", category='error')
                    return redirect(request.referrer)
                else:
                    str_image_url = status.url
                    str_image_id = status.file_id
                # Delete file from local storage
                if os.path.exists(imagepath):
                    os.remove(imagepath)

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
            if 'Bulletin' in form.medium.data and form.recipient.data and is_live == 1:
                # Extract the selected recipients from the form
                selected_recipients = form.recipient.data
                # Convert the selected recipients into a string to store in the database
                recipients_string = ",".join(selected_recipients)
            announcement_to_create = Announcement(Title=form.title.data,
                                                Content=form.content.data,
                                                CreatorId=current_user.UserId,
                                                IsLive=is_live,
                                                Slug=generateSlug(form.title.data),
                                                ImageUrl=str_image_url,
                                                ImageId=str_image_id,
                                                ProjectId=form.project.data,
                                                Recipient=recipients_string)
            db.session.add(announcement_to_create)
            db.session.commit()
            # If announcement session is not empty, clear the session after saving to database
            if 'announcement_title' in session:
                session.pop('announcement_title', None)
            if 'announcement_body' in session:
                session.pop('announcement_body', None)
            # If Email checkbox is checked, send the announcement to desired recipients
            if 'Email' in form.medium.data and form.recipient.data is not [] and is_live == 1:
                emails = []
                if '2' in form.recipient.data:
                    query = (
                        select(Beneficiary.Email)
                        .join(User, Beneficiary.BeneficiaryId == User.BeneficiaryId)
                        .join(Registration, User.UserId == Registration.UserId)
                        .join(Project, Registration.ProjectId == Project.ProjectId)
                        .filter(Project.ProjectId == form.project.data)
                    )

                    beneficiary_emails = db.session.execute(query).scalars().all()
                    emails += beneficiary_emails
                if '3' in form.recipient.data:
                    query = (
                        select(Student.Email)
                        .join(User, Student.StudentId == User.StudentId)
                        .join(Registration, User.UserId == Registration.UserId)
                        .join(Project, Registration.ProjectId == Project.ProjectId)
                        .filter(Project.ProjectId == form.project.data)
                    )

                    student_emails = db.session.execute(query).scalars().all()
                    emails += student_emails
                sendEmail(form.title.data, emails, form.content.data, form.content.data)
                flash('Announcement is successfully sent to email', category='success')
            flash('Announcement is successfully inserted.', category='success')
            return redirect(url_for('announcement.manageAnnouncements'))
        if form.errors != {}: # If there are errors from the validations
            for err_msg in form.errors.values():
                flash(err_msg, category='error')
    faculty_projects = None
    # If current user is faculty, get their project only
    if current_user.RoleId == 4:
        faculty_projects = [(project.ProjectId, project.Title) for project in Project.query.filter_by(LeadProponentId=current_user.UserId).all()]
    if 'announcement_title' in session:
        form.title.data = session['announcement_title']
    if 'announcement_body' in session:
        form.content.data = session['announcement_body']
    return render_template('announcement/announcement_form.html', form=form, faculty_projects=faculty_projects)

@bp.route('/announcement/<int:id>/<string:slug>')
def viewAnnouncement(id, slug):
    announcement = Announcement.query.filter_by(AnnouncementId=id, Slug=slug).first()
    print(announcement)
    return render_template('announcement/view_announcement.html', announcement=announcement)

@bp.route('/unpublish/announcement/<int:id>', methods=['POST'])
@login_required(role=["Admin", "Faculty"])
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
@login_required(role=["Admin", "Faculty"])
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

            if 'Bulletin' in form.medium.data and form.recipient.data and is_live == 1:
                selected_recipients = form.recipient.data
                recipients_string = ",".join(selected_recipients)
                announcement.Recipient = recipients_string

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

@bp.route('/announcement')
def announcement():
    user_role_id = current_user.RoleId if current_user.is_authenticated else None

    if user_role_id == 3:  # Student
        announcements = Announcement.query.filter(
            (Announcement.Recipient.contains('3') | Announcement.Recipient.contains('2,3')) &
            Announcement.IsLive
        ).order_by(desc(Announcement.Created)).all()
    elif user_role_id == 2:  # Beneficiary
        announcements = Announcement.query.filter(
            (Announcement.Recipient.contains('2') | Announcement.Recipient.contains('2,3')) &
            Announcement.IsLive
        ).order_by(desc(Announcement.Created)).all()
    else:
        # Non-authenticated users see only live announcements
        announcements = Announcement.query.filter_by(IsLive=True).order_by(desc(Announcement.Created)).all()

    return render_template('announcement/announcements.html', announcements=announcements)

