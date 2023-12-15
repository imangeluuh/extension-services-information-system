from app.evaluation import bp
from flask import render_template, url_for, request, redirect, flash, current_app
from flask_login import current_user
from ..models import Registration, Activity, Question, Evaluation, Response, Beneficiary
from app import db
from ..store import uploadImage, purgeImage
from werkzeug.utils import secure_filename
from ..decorators.decorators import login_required

# =========================================================
# ||                 ADMIN/FACULTY VIEWS                 ||
# =========================================================


@bp.route('/questions')
@login_required(role=["Admin", "Faculty"])
def questions():
    mandatory_questions = Question.query.filter_by(State = 1, Required = 1).all()
    optional_questions = Question.query.filter_by(State = 1, Required = 0).all()

    return render_template('evaluation/questions.html', mandatory_questions=mandatory_questions, optional_questions=optional_questions)

#delete question - deletest question from pool and redirects back to questions
@bp.route("/questions/delete/<id>")
@login_required(role=["Admin", "Faculty"])
def deleteQuestion(id):

    question = Question.query.filter_by(QuestionId=id).first()

    if question:
        question.State = 0
        db.session.commit()

    flash('The question has been deleted successfully.', category='success')
    return redirect(url_for("evaluation.questions"))


@bp.route('/questions/add', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def addQuestions():
    if request.method == "POST":
        question_text = request.form["question"]
        responses = list(filter(None, request.form.getlist("responses")))
        question_type = 1
        if request.form["type"] == 'Text':
            question_type = 2
            responses = []
        required = 1
        if request.form['optional'] == '1':
            required = 0

        if question_text.isspace() or question_text == "" or question_type == 1 and (len(responses) < 2 or all(responses[i].isspace() for i in range(0, len(responses)-1))):
            flash('Please complete all required fields.', category='error')
            return render_template("evaluation/add_question.html")
        
        if not question_type in range(1,3):
            flash('The application could not complete your request at this moment. Please try again later.', category='error')
            return render_template("evaluation/add_question.html")
        
        try:
            question_to_add = Question(Text=question_text, State=1, Type=question_type, Required=required, Responses=str(responses))
            db.session.add(question_to_add)
            db.session.commit()
            flash('Your question has been successfully added to the pool.', category='success')
        except:
            flash('An error occured whilst adding your question to the pool. Please try again later.', category='error')
    return render_template("evaluation/add_question.html")


@bp.route('/evaluations')
@login_required(role=["Admin", "Faculty"])
def evaluations():
    active_evaluations = None
    inactive_evaluations = None

    if current_user.Role.RoleId == 1:
        active_evaluations = Evaluation.query.filter_by(State = 1).all()
        inactive_evaluations = Evaluation.query.filter_by(State = 0).all()
    else:
        list_activities = [r.Project.Activity for r in Registration.query.filter_by(UserId=current_user.User[0].UserId).all()]
        # Initialize an empty list to store the ActivityIds
        list_activity_ids = []
        
        # Iterate through the outer list
        for sublist in list_activities:
            # Iterate through the inner list
            for activity in sublist:
                list_activity_ids.append(activity.ActivityId)  
        
        active_evaluations = Evaluation.query.filter(Evaluation.ActivityId.in_(list_activity_ids)).filter_by(State = 1).all()
        inactive_evaluations = Evaluation.query.filter(Evaluation.ActivityId.in_(list_activity_ids)).filter_by(State = 0).all()

    return render_template("evaluation/evaluations.html", active_evaluations=active_evaluations, inactive_evaluations=inactive_evaluations)


@bp.route('/evaluations/add', methods=['GET', 'POST'])
@login_required(role=["Admin", "Faculty"])
def addEvaluation():
    questions = Question.query.filter_by(State = 1).all()
    activities = Activity.query.all()
    if request.method == "POST":

        evaluation_name = request.form["name"]
        evaluation_activity = request.form["activity"]
        evaluation_questions = request.form.getlist("questions")

        if evaluation_name.isspace() or evaluation_name == "" or not evaluation_questions or not evaluation_activity:
            flash('Please complete all required fields.', category='error')

        try:
            evaluation_to_add = Evaluation(EvaluationName=evaluation_name, ActivityId=evaluation_activity, State=1, Questions=str(evaluation_questions))
            db.session.add(evaluation_to_add)
            db.session.commit()
            flash('Evaluation is successfully created.', category='success')
        except:
            flash('An error occured whilst creating your evaluation. Please try again later.', category='error')

    return render_template('evaluation/add_evaluation.html', questions=questions, activities=activities)

#close evaluation - makes evaluation inactive and redirects to evaluations page
@bp.route("/evaluations/close/<id>")
@login_required(role=["Admin", "Faculty"])
def closeEvaluation(id):
    evaluation = Evaluation.query.filter_by(EvaluationId=id).first()

    try:
        if evaluation:
            evaluation.State = 0
            db.session.commit()
            flash('The evaluation has been closed successfully.', category='success')
    except:
        flash('The evaluation could not be closed. Please try again later.', category='error')

    return redirect(url_for("evaluation.evaluations"))

#results page - show evaluation results
@bp.route("/results/<id>")
@login_required(["Admin", "Faculty"])
def results(id):

    list_activities = [r.Project.Activity for r in Registration.query.filter_by(UserId=current_user.User[0].UserId).all()]
    # Initialize an empty list to store the ActivityIds
    list_activity_ids = []
    
    # Iterate through the outer list
    for sublist in list_activities:
        # Iterate through the inner list
        for activity in sublist:
            list_activity_ids.append(activity.ActivityId) 

    evaluation = Evaluation.query.filter_by(EvaluationId=id).first()

    if not evaluation: 
        flash('The evaluation you have requested does not exist. Please check if your link is correct.', category='error')
        return render_template("evaluation/results.html")

    questions = []
    for question_id in evaluation.questionsList():
        question = Question.query.filter_by(QuestionId=question_id).first()
        questions.append(question)

    responses = Response.query.filter_by(EvaluationId=id).all()

    return render_template("evaluation/results.html", evaluation=evaluation, questions=questions, responses=responses)


# =========================================================
# ||                      USER VIEWS                     ||
# =========================================================

#evaluatoin page - allows responses to be collected
@bp.route("/evaluation/<id>", methods=["GET", "POST"])
@login_required(role=["Beneficiary"])
def evaluation(id):
    
    #check whether user is registered in project and hasn't already taken evaluation
    list_activities = [r.Project.Activity for r in Registration.query.filter_by(UserId=current_user.User[0].UserId).all()]

    # Initialize an empty list to store the ActivityIds
    list_activity_ids = []

    # Iterate through the outer list
    for sublist in list_activities:
        # Iterate through the inner list
        for activity in sublist:
            list_activity_ids.append(activity.ActivityId)  
    
    evaluation = Evaluation.query.filter_by(EvaluationId=id).first()
    if evaluation.ActivityId not in list_activity_ids:
        print('andito siya', evaluation.ActivityId)
        return redirect(url_for('programs.activity', id=evaluation.ActivityId))

    if not evaluation: 
        flash('The evaluation you have requested does not exist. Please check if your link is correct.', category='error')
        return redirect(url_for('programs.activities'))
    
    if Response.query.filter_by(EvaluationId=id, BeneficiaryId=current_user.User[0].UserId).first():
        evaluation_taken = True
        return render_template("evaluation/evaluation.html", evaluation=evaluation, evaluation_taken=evaluation_taken)

    questions = []
    for question_id in evaluation.questionsList():
        question = Question.query.filter_by(QuestionId=question_id).first()
        questions.append(question)

    if request.method == "POST":
        error = 0

        #check for required fields
        for question in questions:
            response = request.form.get(str(question.QuestionId))
            if question.Required and (response == None or response.isspace() or response == ""):
                flash('Please fill out all the required fields', category='error')
                return render_template("evaluation/evaluation.html", evaluation=evaluation, questions=questions)

        #submit responses
        for question in questions:
            response = request.form.get(str(question.QuestionId))

            if not response is None and not response.isspace() and response != "":
                if question.Type == 1:
                    if not save_response(id, current_user.User[0].UserId, question.QuestionId, None, int(response)):
                        error = 1
                        break

                elif question.Type == 2:
                    if not save_response(id, current_user.User[0].UserId, question.QuestionId, response, None):
                        error = 1
                        break
        if not error:
            flash('Your response has been recorded successfully. Evaluatoin results will be made available to you through your dashboard when the evaluation closes.', category='success')
            return redirect(url_for('evaluation.evaluation', id=evaluation.EvaluationId))
        else:
            flash('An error occured whilst recording your response. Please try again later.', category='error')
        
    return render_template("evaluation/evaluation.html", evaluation=evaluation, questions=questions)



def save_response(evaluation_id, user_id, question_id, text, num):
    if (text is None and num is None):
        return 0 #failure
    if not Evaluation.query.filter_by(EvaluationId=evaluation_id).first():
        return 0 #failure: invalid evaluation id
    if not Beneficiary.query.filter_by(BeneficiaryId=user_id).first():
        return 0 #failure: invalid user id
    if not Question.query.filter_by(QuestionId=question_id).first():
        return 0 #failure: invalid question id

    response_to_add = Response(EvaluationId=evaluation_id, BeneficiaryId=user_id, QuestionId=question_id, Text=text, Num=num)
    db.session.add(response_to_add)
    db.session.commit()
    return 1