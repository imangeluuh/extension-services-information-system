from app.reports import bp
from flask import render_template, url_for, request, redirect, flash, current_app
from flask_login import current_user
from ..models import Project, ExtensionProgram, Registration, Agenda, ExtensionProgram, Activity, Response, User, Certificate, Budget, Item, Attendance, Course, Faculty
from datetime import datetime
from app import db, cache
from ..decorators.decorators import login_required
from sqlalchemy import asc
import os, folium
from folium.plugins import MarkerCluster

@bp.route('/extensio-programs-report')
@login_required(role=["Admin"])
def extensionPrograms():
    extension_programs = ExtensionProgram.query.order_by(ExtensionProgram.ExtensionProgramId.asc()).all()
    ext_program = extension_programs[0]
    
    return render_template('reports/extension_program.html'
                        , ext_program=ext_program
                        , extension_programs=extension_programs)

@bp.route('/program-participation')
@login_required(role=["Admin"])
def programParticipation():    
    return render_template('reports/program_participation.html')

@bp.route('/get-details')
@login_required(role=["Admin"])
def getDetails():
    current_date = datetime.utcnow().date()
    filter_value = int(request.args.get("program"))

    if filter_value:
        ext_program = ExtensionProgram.query.filter_by(ExtensionProgramId=filter_value).first()
        upcoming_projects = Project.query.filter(Project.StartDate > current_date, Project.ExtensionProgramId == filter_value).count()
        ongoing_projects = Project.query.filter(Project.StartDate <= current_date, Project.EndDate >= current_date, Project.ExtensionProgramId == filter_value).count()
        completed_projects = Project.query.filter(Project.EndDate < current_date, Project.ExtensionProgramId == filter_value).count()

        upcoming_activities = Activity.query.join(Project).filter(Activity.Date > current_date, Project.ExtensionProgramId == filter_value).count()
        ongoing_activities = Activity.query.join(Project).filter(Activity.Date <= current_date, Activity.Date >= current_date, Project.ExtensionProgramId == filter_value).count()
        completed_activities = Activity.query.join(Project).filter(Activity.Date < current_date, Project.ExtensionProgramId == filter_value).count()
    else:
        upcoming_projects = Project.query.filter(Project.StartDate > current_date).count()
        ongoing_projects = Project.query.filter(Project.StartDate <= current_date, Project.EndDate >= current_date).count()
        completed_projects = Project.query.filter(Project.EndDate < current_date).count()

        upcoming_activities = Activity.query.filter(Activity.Date > current_date).count()
        ongoing_activities = Activity.query.filter(Activity.Date <= current_date, Activity.Date >= current_date).count()
        completed_activities = Activity.query.filter(Activity.Date < current_date).count()

    return render_template('reports/ext_program_details.html', upcoming_projects=upcoming_projects
                        , ongoing_projects=ongoing_projects
                        , completed_projects=completed_projects
                        , upcoming_activities=upcoming_activities
                        , ongoing_activities=ongoing_activities
                        , completed_activities=completed_activities
                        , ext_program=ext_program)