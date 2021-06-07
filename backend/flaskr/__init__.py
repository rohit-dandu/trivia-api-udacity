import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  # set up cors
  CORS(app)
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''

  # access control allowed headers and methods
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTION')
    return response
  
  def paginate_questions(request, questions_list):
    # get the page argument from request.args
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in questions_list]
    questions_paginated = questions[start:end]

    return questions_paginated

  def get_category_list():
    categories = Category.query.all()
    category_list = {category.id: category.type for category in categories}
    if len(category_list) == 0:
      abort(404)
    return category_list
  
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  # return categories available
  @app.route('/categories', methods=['GET'])
  def get_categories():
    return jsonify({
      'success': True,
      'categories': get_category_list()
    })
  
  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions', methods=['GET'])
  def get_questions():
    # get all the questions
    questions_list = Question.query.all()
    # paginate questions; 10 per page
    questions_paginated = paginate_questions(request, questions_list)

    if len(questions_paginated) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': questions_paginated,
      'total_questions': len(questions_list),
      'categories': get_category_list(),
      'currentCategory': None
    })
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None:
        abort(404)
      question.delete()
      
      selection = Question.query.order_by(Question.id).all()
      paginate_questions(request, selection)
      return jsonify({
        'success':True
      })
    except:
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def add_question():
    body = request.get_json()

    question = body.get('question')
    answer = body.get('answer')
    category = body.get('category')
    difficulty = body.get('difficulty')

    if question == None or answer == None or category == None or difficulty == None:
      abort(400)
    question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
    try:
      question.insert()
      selection = Question.query.all()
      questions_list = paginate_questions(request, selection)
      return jsonify({
      'success': True
    })
    except:
      abort(400)
  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def get_search_results():
    body = request.get_json()
    search_term = body.get('searchTerm', None)

    if search_term is None:
      abort(404)
    matching_questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
    result = [question.format() for question in matching_questions]

    return jsonify({
      'success': True,
      'questions': result,
      'total_questions': len(matching_questions),
      'currentCategory': None
    })
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_categories(category_id):
    current_category = Category.query.filter(Category.id == category_id).one_or_none()

    if current_category is None:
      abort(404)
    
    selection = Question.query.filter(Question.category == str(current_category.id))

    # current questions
    questions = paginate_questions(request, selection)
    return jsonify({
      'success':True,
      'questions': questions,
      'totalQuestions': len(questions),
      'currentCategory': current_category.format()
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_random_quiz():
    body = request.get_json()
    previous_questions = body.get('previous_questions',[])
    quiz_category = body.get('quiz_category', None)

    try:
      if quiz_category:
        if quiz_category['id'] == 0:
          quiz = Question.query.all()
        else:
          quiz = Question.query.filter_by(category=quiz_category['id']).all()
      if not quiz:
        abort(422)
      
      current_questions = []
      for question in quiz:
        if question.id not in previous_questions:
          current_questions.append(question.format())
      
      if len(current_questions) == 0:
        return jsonify({
          'question': False
        })
      else:
        next_question = random.choice(current_questions)
        return jsonify({
          'question': next_question
        })
    except:
      abort(404)
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  
  return app

    