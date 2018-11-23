from flask import Flask, render_template, request, redirect, session, flash, jsonify
import json
from passlib.hash import pbkdf2_sha256



app = Flask(__name__)
file2 = open('users.json')
file1 = open('codes.json')
file3 = open('mycodes.json')
app.config['SECRET_KEY'] = "tamatoo"

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
users = json.load(file2)
file2.close()
codes = json.load(file1)
file1.close()
mycodes = json.load(file3)
file3.close()

@app.route('/')
def index():
    return "you have registered or code went through"

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/loginattempt', methods=['POST'])
def loginattempt():
    attempted_id = request.form['loginid']
    attempted_pass = request.form['loginpass']
    if attempted_id=='' or attempted_pass=='':
        return redirect('/login')
    if attempted_id in users:
        if pbkdf2_sha256.verify(attempted_pass, users[attempted_id]):
            session['logged_in'] = True
            session['username'] = attempted_id
            return redirect('/profile')
        else:
            return redirect('/login')
            print("wrong pass")
    else:
        return redirect('/login')
        print("no username")



@app.route('/registerattempt', methods=['POST'])
def registerattempt():
    register_id = request.form['registerid']
    register_pass = request.form['registerpass']
    if (register_id == '') or (register_pass == ''):
        return redirect('/register')
    if ' ' in register_id:
        return redirect('/register')
    register_pass_hashed = pbkdf2_sha256.hash(register_pass)
    if register_id in users:
        return redirect('/register')
    else:

        users.update({register_id: register_pass_hashed})
        mycodes.update({register_id: {}})
        session['username'] = register_id
        session['logged_in'] = True
        file2 = open('users.json', 'w')
        json.dump(users, file2, indent=4)
        file2.close()
        file3 = open('mycodes.json', 'w')
        json.dump(users, file3, indent=4)
        file3.close()
        return redirect('/login')

@app.route('/register')
def rigister():
    return render_template("input.html")

@app.route('/profile')
def profileredirect():
    if session['logged_in'] == False:
        return redirect('/login')
    return redirect('/profile/'+session['username'])

@app.route('/profile/<user>')
def profile(user):
    mycodeslen = len(mycodes[user])
    return render_template('profile.html', user = user, mycodeslen = mycodeslen)


@app.route('/codeattempt', methods=['POST'])
def codeattempt():
    if session['logged_in'] == False:
        return redirect('/login')

    global mycodes
    global codes
    attempted_code = request.form['codeid']
    if attempted_code=='':
        return redirect('/profile')
    if attempted_code==' ':
        return redirect('/profile')
    if attempted_code in codes:
        if attempted_code in mycodes:
            return redirect('/profile')
        mycodes['test'].update({attempted_code: {}})
        file3 = open('mycodes.json', 'w')
        json.dump(users, file3, indent=4)
        file3.close()
        return redirect('/profile')
    else:
        return redirect('/profile')


if __name__ == "__main__":
    app.run(debug=True)
