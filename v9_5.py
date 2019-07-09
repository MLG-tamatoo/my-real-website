from flask import Flask, render_template, request, redirect, session, flash, jsonify
import json
from passlib.hash import pbkdf2_sha256
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import random

"""configuration"""

UPLOAD_FOLDER = '/Users/shakeandbakeforever/tamatoowebsite/static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
file1 = open('codes.json')
app.config['SECRET_KEY'] = "tamatoo"
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)
codes = json.load(file1)
file1.close()
tokendict = {}
tokendict2 = {}
'''making the sqlDB models'''
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    money = db.Column(db.String(300), default="0", nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="/static/default.png")
    password = db.Column(db.String(60), nullable=False)
    usedcodes = db.relationship('Usedcode', backref='author', lazy=True)
    rank = db.Column(db.String(20), nullable=False, default="Bronze")
    email = db.Column(db.String(60), nullable=False, default="None")

    def __repr__(self):
        return f"User('{self.username}, {self.money}')"


class Usedcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Usedcodes('{self.code}')"

@app.template_global()
def static_include(filename):
    fullpath = os.path.join(app.static_folder, filename)
    with open(fullpath, 'r') as f:
        return f.read()


'''the following are the misc endpoints'''

'''making the home page endpoint'''
@app.route('/')
def index():
    return render_template("index.html")



"""login"""



'''making the login endpoint'''
@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/login/<validation>')
def loginerror(validation):
    return render_template("login.html", validation = validation)

'''making the loginattempt endpoint'''
@app.route('/loginattempt', methods=['POST'])
def loginattempt():
    #this takes the user input
    attempted_id = request.form['loginid']
    attempted_pass = request.form['loginpass']
    #checks to see if the username is not empty
    if attempted_id=='' or attempted_pass=='':
        return redirect('/login/unfilled')
    #checks to see if the the username is in users
    user = User.query.filter_by(username=attempted_id).first()
    if user:
        if pbkdf2_sha256.verify(attempted_pass, user.password):
            session['logged_in'] = True
            session['username'] = attempted_id
            return redirect('/profile')
        else:
            return redirect('/login/wrongpass')
    else:
        return redirect('/login/nouser')
    return redirect('/login')



"""register"""



'''making the register endpoint'''
@app.route('/register')
def rigister():
    return render_template("register.html")

@app.route('/register/<validation>')
def rigistererror(validation):
    return render_template("register.html", validation = validation)

'''making the registerattempt endpoint'''
@app.route('/registerattempt', methods=['POST'])
def registerattempt():
    #user input
    register_id = request.form['registerid']
    register_pass = request.form['registerpass']
    register_email = request.form['registeremail']
    #checks if it is empty
    if (register_id == '') or (register_pass == ''):
        return redirect('/register/unfilled')
    #checks if it has a space
    if ' ' in register_id or " " in register_email:
        return redirect('/register/space')

    #hashes the password
    register_pass_hashed = pbkdf2_sha256.hash(register_pass)
    #checks if it has been used before
    user = User.query.filter_by(username=register_id).first()
    if user:
        return redirect('/register/usedusername')

    if register_email == "":
        register_email = "None"
    if register_email != "None":
        if "@gmail.com" not in register_email:
            return redirect('/register/emailerror')
        templist = register_email.split("@")
        if len(templist) != 2:
            return redirect('/register/emailerror')
        if templist[0] == "":
            return redirect('/register/emailerror')
        if templist[1] != "gmail.com":
            return redirect('/register/emailerror')

    #making the user
    user = User(username=register_id, password=register_pass_hashed, email=register_email)
    db.session.add(user)
    db.session.commit()
    session['logged_in'] = True
    session['username'] = register_id
    return redirect('/profile')


"""profile"""


'''making the profile endpoint'''
@app.route('/profile')
def profileredirect():
    #checks if the user is logged in
    if not session.get('logged_in'):
        return redirect('/login')
    return redirect('/profile/'+session['username'])

'''making the user profile endpoint'''
#this is the endpoint that follows the profile endpoint
@app.route('/profile/<user>')
def profile(user):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    #need to put the users money here
    sqluser = User.query.filter_by(username=session['username']).first()
    userimage = sqluser.image_file
    usermoney = sqluser.money
    userrank = sqluser.rank
    if int(usermoney) >= 2 and int(usermoney) <= 4:
        sqluser.rank = "Silver"
        db.session.commit()
        userrank = sqluser.rank
    if int(usermoney) >= 5:
        sqluser.rank = "Gold"
        db.session.commit()
        userrank = sqluser.rank
    return render_template('profile.html', user = user, usermoney = usermoney, userimage = userimage, userrank = userrank)



"""codeattempt"""



'''making the code attempt endpoint'''
#where the user sends the code to check it
@app.route('/codeattempt', methods=['POST'])
def codeattempt():
    #sees if the user is logged in
    if not session.get('logged_in'):
        return redirect('/login')
    #recieves the users input
    attempted_code = request.form['codeid']
    # checks if the input is empty or contains a space
    if attempted_code=='' or attempted_code==' ':
        return redirect('/profile')
    #looks if it is in codes
    if attempted_code in codes:
        #finds the user then updates the users money
        user = User.query.filter_by(username=session['username']).first()
        #checks if the user has already used the code
        if Usedcode.query.filter_by(code=attempted_code, user_id=user.id).first():
            return redirect('/profile')

        newmoney = int(user.money) + int(codes[attempted_code])
        user.money = str(newmoney)
        #adding to the list of used codes
        codeused = Usedcode(code=attempted_code, user_id=user.id)
        db.session.add(codeused)
        db.session.commit()
        return redirect('/profile')
    else:
        return redirect('/profile')

@app.route('/logout')
def logout():
	if not session.get('logged_in'):
		return redirect('/login')
	session.pop('logged_in', None)
	session.pop('username', None)
	return redirect('/login')



""""settings"""



'''making the settings endpoint'''
@app.route('/settings')
def settingsdirect():
    #checks if the user is logged in
    if session['logged_in'] == False:
        return redirect('/login')
    return redirect('/settings/'+session['username'])

'''making the user settings endpoint'''
#this is the endpoint that follows the settings endpoint
@app.route('/settings/<user>')
def settings(user):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    #need to put the users money here
    sqluser = User.query.filter_by(username=session['username']).first()
    userimage = sqluser.image_file
    return render_template('settings.html', username = user, userimage = userimage,)



"""change pass section"""



@app.route('/settings/<user>/changepass')
def settingschangepassdirect(user):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    return render_template('changepass.html')


@app.route('/changepassattempt', methods=['POST'])
def changepassattempt():
    attempted_old = request.form['oldpass']
    attempted_pass = request.form['newpass']
    #checks to see if the username is not empty
    if attempted_old=='' or attempted_pass=='':
        return redirect('/settings/'+session['username'])
    #checks to see if the the username is in users
    user = User.query.filter_by(username=session['username']).first()
    if user:
        if pbkdf2_sha256.verify(attempted_old, user.password):
            user.password =  pbkdf2_sha256.hash(attempted_pass)
            db.session.commit()
            return redirect('/settings/'+session['username'])
        else:
            return redirect('/settings/'+session['username']+'/changepass')
    else:
        return redirect('/settings/'+session['username']+'/changepass')


"""change username section"""


@app.route('/settings/<user>/changeusername')
def settingschangeusernamedirect(user):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    return render_template('changeusername.html')

@app.route('/settings/<user>/changeusername/<validation>')
def changedusernameerror(user, validation):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    return render_template('changeusername.html', validation = validation)

@app.route('/changeusernameattempt', methods=['POST'])
def changeusernameattempt():
    attempted_old = request.form['oldusername']
    attempted_username = request.form['newusername']
    #checks to see if the username is not empty
    if attempted_old=='' or attempted_username=='':
        return redirect('/settings/'+session['username'])

    if " " in attempted_username:
                return redirect('/settings/'+session['username']+'/changeusername/space')

    #checks to see if the the username is in users
    user = User.query.filter_by(username=session['username']).first()
    if user:
        if user.username == attempted_old:
            user2 = User.query.filter_by(username=attempted_username).first()
            if user2:
                return redirect('/settings/'+session['username']+'/changeusername/usedusername')
            user.username =  attempted_username
            db.session.commit()
            session['username'] = user.username
            return redirect('/settings/'+session['username'])
        else:
            return redirect('/settings/'+session['username']+'/changeusername/notuser')

    return redirect('/settings/'+session['username']+'/changeusername')


"""change profile picture"""

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/settings/<user>/changeprofilepic', methods=['GET', 'POST'])
def upload_file(user):
    if not session.get('logged_in'):
        return redirect('/login')
    if session['username'] != user:
        return redirect('/profile')
    sqluser = User.query.filter_by(username=user).first()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if sqluser.image_file != "/static/default.png":
            os.remove("/Users/shakeandbakeforever/tamatoowebsite"+ sqluser.image_file)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            sqluser.image_file = "/static/"+ filename
            db.session.commit()
            return redirect('/settings/'+ user)
    return render_template('changeprofilepic2.html')


"""leaderboard"""


@app.route('/leaderboard')
def leaderboard():
    userlist = [[r.username, r.money, r.rank, r.image_file] for r in User.query.all()]
    userlist.sort(key=lambda tup: tup[1], reverse=True)
    result = []
    if len(userlist) < 5:
        return render_template('leaderboard0.html')

    if len(userlist) < 10:
        limit = 5
    else:
        limit = 10
    for i in range(0, limit):
        templist = userlist[i]
        usernametemp = templist[0]
        moneytemp = templist[1]
        imagetemp = templist[2]
        ranktemp = templist[3]
        result.append(usernametemp)
        result.append(moneytemp)
        result.append(imagetemp)
        result.append(ranktemp)

    if len(userlist) >= 5 and len(userlist) <=9:
        return render_template('leaderboard5.html', result = result)

    if len(userlist) >= 10:
        return render_template('leaderboard10.html', result = result)

"""password recovery"""
@app.route('/recoverpasswordemail')
def recoverpasswordemail():
    return render_template("recoverpasswordemail.html")

@app.route('/recoverpasswordemailattempt', methods=['POST'])
def recoverpasswordemailattempt():
    username = request.form['username']
    if " " in username:
        return redirect("/recoverpasswordemail/nouser")
    user = User.query.filter_by(username=username).first()
    if user:
        if user.email != "None":
            global tokendict
            reciever_email = user.email
            msg = EmailMessage()
            msg['Subject'] = "Recovery"
            msg['From'] = 'nothingtodowithtamatoo1!@gmail.com'
            msg['To'] = reciever_email

        # Add the html version.  This converts the message into a multipart/alternative
        # container, with the original text message as the first part and the new html
        # message as the second part.
            token = ""
            size = random.randint(1, 9)
            for i in range(0, size):
                token = token + str(random.randint(0, 9))
            tokendict[token] = username
            test = "register"
            body = 'http://localhost:5000/recoverpassword/' + token
            msg.set_content(body)
        # note that we needed to peel the <> off the msgid for use in the html.

        # Make a local copy of what we are going to send.
            with open('outgoing.msg', 'wb') as f:
                f.write(bytes(msg))

        # Send the message via local SMTP server.
            with smtplib.SMTP('smtp.gmail.com:587') as s:
                username = 'tamatootech@gmail.com'
                password = 'nothingtodowithtamatoo1!'
                s.ehlo()
                s.starttls()
                s.login(username,password)
                s.send_message(msg)

            return redirect('/recoverpasswordemail')
        return redirect('/recoverpasswordemail/noemail')
    return redirect('/recoverpasswordemail/nouser')

@app.route('/recoverpasswordemail/<failure>')
def recoverpasswordemailfailure(failure):
    return render_template("recoverpasswordemail.html", failure=failure)


@app.route('/recoverpassword/<token>')
def recoverpassword(token):
    global tokendict
    if token in tokendict:
        tokendict.pop(token, None)
        return render_template("recoverpassword.html", token=token)
    return '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtmll/DTD/xhtmll-transitional.dtd">
    <html>
    <style>
    body {
    background-color:#ffb6c1;
    }


      h1 {
      font-family:arial;
      color:#000000;

      font-weight: bold;
    }
    </style>
    <head>
     <title>Fail</title>
     <center>
     <h1>This link has already been used.</h1>
    </center>
    </head>
    </html>'''

@app.route('/recoverpasswordattempt', methods=['POST'])
def recoverpasswordattempt():
    token = request.form['token']
    username = tokendict.get(token, 'None')
    if username == 'None':
        return redirect('/recoverpasswordemail/incorrecttoken')
    attempted_pass = request.form['newpassword']
    #checks to see if the username is not empty
    if (username == '') or (attempted_pass == ''):
        return redirect('/recoverpasswordemail/unfilled')
    #checks if it has a space
    if ' ' in username:
        return redirect('/recoverpasswordemail/space')

    #hashes the password
    attempted_pass_hashed = pbkdf2_sha256.hash(attempted_pass)
    #checks if it has been used before
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = attempted_pass_hashed
        db.session.commit()
        session['logged_in'] = True
        session['username'] = username
        return redirect('/profile')
    return redirect('/register')



"""delete account"""



@app.route('/deleteemail')
def deleteemail():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template("deleteemail.html")

@app.route('/deleteemailattempt', methods=['POST'])
def deleteemailattempt():
    if not session.get('logged_in'):
        return redirect('/login')
    username = request.form['username']
    if " " in username:
        return redirect("/deleteemail/space")
    user = User.query.filter_by(username=username).first()
    if user:
        if user.email != "None":
            global tokendict2
            reciever_email = user.email
            msg = EmailMessage()
            msg['Subject'] = "Delete Account"
            msg['From'] = 'nothingtodowithtamatoo1!@gmail.com'
            msg['To'] = reciever_email

        # Add the html version.  This converts the message into a multipart/alternative
        # container, with the original text message as the first part and the new html
        # message as the second part.
            token = ""
            size = random.randint(1, 9)
            for i in range(0, size):
                token = token + str(random.randint(0, 9))
            tokendict2[token] = username
            test = "register"
            body = 'Are you sure that you would like to delete your account all of your information will be deleted. http://localhost:5000/deleteaccount/' + token
            msg.set_content(body)
        # note that we needed to peel the <> off the msgid for use in the html.

        # Make a local copy of what we are going to send.
            with open('outgoing.msg', 'wb') as f:
                f.write(bytes(msg))

        # Send the message via local SMTP server.
            with smtplib.SMTP('smtp.gmail.com:587') as s:
                username = 'tamatootech@gmail.com'
                password = 'nothingtodowithtamatoo1!'
                s.ehlo()
                s.starttls()
                s.login(username,password)
                s.send_message(msg)

            return redirect('/deleteemail')
        return redirect('/deleteemail/noemail')
    return redirect('/deleteemail/nouser')

@app.route('/deleteaccount/<token>')
def deleteaccount(token):
    global tokendict2
    if token in tokendict2:
        tokendict2.pop(token, None)
        return render_template("deleteaccount.html", token=token)
    return '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtmll/DTD/xhtmll-transitional.dtd">
    <html>
    <style>
    body {
    background-color:#ffb6c1;
    }


      h1 {
      font-family:arial;
      color:#000000;

      font-weight: bold;
    }
    </style>
    <head>
     <title>Fail</title>
     <center>
     <h1>This link has already been used.</h1>
    </center>
    </head>
    </html>'''

@app.route('/deleteaccountattempt', methods=['POST'])
def deleteaccountattempt():
    token = request.form['token']
    username = tokendict2.get(token, 'None')
    if username == 'None':
        return redirect('/deleteaccountemail/incorrecttoken')
    attempted_pass = request.form['password']
    #checks to see if the username is not empty
    if (username == '') or (attempted_pass == ''):
        return redirect('/deleteaccountemail/unfilled')
    #checks if it has a space
    if ' ' in username:
        return redirect('/deleteaccountemail/space')
    #checks if it has been used before
    user = User.query.filter_by(username=username).first()
    if user:
        if pbkdf2_sha256.verify(attempted_pass, user.password):
            db.session.delete(user)
            db.session.commit()
            return redirect('/register')
        return redirect('/deleteemail/wrongpass')
    return redirect('/deleteemail/nouser')

@app.route('/deleteemail/<failure>')
def deleteemailfailure(failure):
    return render_template("deleteemail.html", failure=failure)

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
