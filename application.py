from awscli.errorhandler import ClientError
from awscli.paramfile import logger
from flask import Flask, render_template, flash, redirect, request, jsonify
from secret import Config
from forms import LoginForm
from forms import ProfileForm
from forms import UserForm
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, login_user
from user_placeholder import User
from questionForm import answerForm
import boto3
from boto3.session import Session
import awscli
import json

# initialise application
# make static folder available on the root of the url '', get rid of the static/ part of static/new-admin.js
application = Flask(__name__, static_folder='static', static_url_path='', template_folder='templates')
app = application
login = LoginManager(app)
Bootstrap(app)
login.init_app(app)
app.config.from_object(Config)
user = User()

dynamodb_session = Session(aws_access_key_id='AKIAXOML5L575E3RVL3R',
                           aws_secret_access_key='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',
                           region_name='eu-west-2')
database = dynamodb_session.resource("dynamodb", region_name="eu-west-2")
increment = database.Table('User').item_count
print(increment)

@login.user_loader
def load_user(id):
    return user

@app.route('/')
def home():
    return redirect('/login')

@app.route('/game', methods=['GET', 'POST'])
def game():
    print(current_user.nickname)
    answerform = answerForm()
    flash(f"Hello " + user.nickname)
    if answerform.validate_on_submit():
        if answerform.answer.data == answerform.answers:
            flash("Correct!")
        else:
            flash("Not Quite!")

    return render_template('game.html', title='Game', form=answerform)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/game')
    form = LoginForm()
    if form.validate_on_submit():
        # Grabs the whole table of user from the database
        users = database.Table("User")
        for i in range(increment):
            record = users.get_item(Key={"ID": i})
            # Admin login
            if (form.username.data == record['Item']['Username']) and (form.password.data == record['Item']['Password']) and record['Item']['AccountID']=="Admin":
                login_user(user)
                return redirect('/admin')
            elif (form.username.data == record['Item']['Username']) and (form.password.data == record['Item']['Password']) and record['Item']['AccountID']=="Student":
                login_user(user)
                return redirect('/moduleSelection')
    return render_template('login.html', title='Login', form=form)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm()
    print(user.nickname)
    print(user.photo)
    if request.method == 'POST':
        user.nickname = request.form['nickname']
        user.photo = form.photo.data
        return redirect('/profile')
    return render_template('profile.html', 
                            title="Profile", 
                            form=form,
                            )

# Shows new-admin page as the admin link
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    user_form = UserForm()

    return render_template('new-admin.html', title='Account creation')


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    global increment
    # View payload, print request.form or look at html element name
    print(request.form)
    account_id = request.form['ID']
    dob = request.form['DOB']
    firstname = request.form['FirstName']
    lastname = request.form['LastName']
    #don't make account if blank categories
    if (not account_id or not dob or not firstname or not lastname):
        return render_template('new-admin.html', title='Account creation')
    # Welcome to the ugliest code ive ever written
    modules = []
    try:
        modules.append(request.form['Math'])
    except:
        pass
    try:
        modules.append(request.form['Sci'])
    except:
        pass
    try:
        modules.append(request.form['Eng'])
    except:
        pass

    username = request.form['Username']
    password = request.form['Password']

    user_table = database.Table('User')

    user_table.put_item(
        TableName='User',
        Item={
            'ID' : increment,
            'AccountID': account_id,
            'DOB': dob,
            'FirstName': firstname,
            'LastName': lastname,
            'Modules': modules,
            'Username': username,
            'Password': password
        }
    )
    increment+=1

    return jsonify({'success': 'success'})


@app.route('/moduleSelection', methods=['GET', 'POST'])
def module_selection():
	return render_template('moduleSelection.html', title='Module Selection')


if __name__ == "__main__":
	app.run()
