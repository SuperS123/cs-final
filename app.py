import datetime
import re

from flask import Flask, render_template, request, session
import json
import random
import math
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session management

# Load questions from JSON file
with open('questions.json', encoding="utf-8") as f:
    questions = json.load(f)


def get_question_by_difficulty(difficulty):
    return random.choice(
        [q for q in questions if q['difficulty'] == difficulty and "following notes" not in q['prompt'] and "underline" not in q["question"]])


@app.template_filter('format_text')
def format_text(text):
    formatted_text = text.replace('Text 1', '<b>Text 1</b><br>').replace('Text 2', '<br> <b>Text 2</b> <br>')
    print(re.split(r"([A-Z][a-z]+)([A-Z][a-z]+)", formatted_text))
    formatted_text = re.sub(r"([A-Z][a-z]+)([A-Z][a-z]+)", "\1<br><br>\2", formatted_text)
    return formatted_text


@app.route('/', methods=['GET', 'POST'])
def quiz():
    if 'score' not in session:
        session['score'] = 0
        session['question_count'] = 0
        session['correct_count'] = 0
        session['difficulty'] = 1
        session['start_time'] = time.time()
        session['selected_choices'] = {}  # Initialize selected_choices

    if request.method == 'POST':
        selected_choice = int(request.form['choice'])
        correct_answer = int(request.form['correct_answer'])
        explanation = request.form['explanation']
        question_id = request.form['question_id']
        end_time = time.time()
        time_spent = end_time - session['start_time']

        session['selected_choices'][question_id] = selected_choice  # Store the selected choice

        if selected_choice == correct_answer:
            session['correct_count'] += 1
            session['difficulty'] = min(3, session['difficulty'] + 1)
        else:
            session['difficulty'] = max(1, session['difficulty'] - 1)

        session['question_count'] += 1
        question = next(q for q in questions if q['id'] == question_id)
        return render_template('question.html', question=question, selected_choice=selected_choice,
                               correct_answer=correct_answer, explanation=explanation, time_spent=time_spent)

    question = get_question_by_difficulty(session['difficulty'])
    session['start_time'] = time.time()
    return render_template('question.html', question=question)


@app.route('/end')
def end():
    score = calculate_score(session['question_count'], session['correct_count'])
    selected_choices = session.get('selected_choices', {})
    questions_this_session = [q for q in questions if q['id'] in selected_choices]
    session.clear()  # Clear the session
    current_date = datetime.date.today()
    return render_template('end.html', score=score, questions=questions_this_session, selected_choices=selected_choices, date=current_date)


def calculate_score(questions, correct_count):
    total_questions = questions
    base_score = (correct_count / total_questions) if total_questions > 0 else 0
    curved_score = 200 + (600 * base_score ** 2)
    return str(round(curved_score, -1)).split(".")[0]


if __name__ == '__main__':
    app.run(debug=False, port=5000, host="0.0.0.0")
