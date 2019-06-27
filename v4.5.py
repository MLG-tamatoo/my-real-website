from flask import Flask, render_template, request, redirect, session, flash, jsonify
import json
from passlib.hash import pbkdf2_sha256


'''loading in all of the json files'''

app = Flask(__name__)
file2 = open('users.json')
file1 = open('codes.json')
file4 = open('usermoney.json')
app.config['SECRET_KEY'] = "tamatoo"

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
users = json.load(file2)
file2.close()
codes = json.load(file1)
file1.close()
money = json.load(file4)
file4.close()

'''the following are the endpoints'''

'''making the home page endpoint'''
@app.route('/')
def index():
    return render_template("index.html")

'''making the login endpoint'''
@app.route('/login')
def login():
    return render_template("login.html")

'''making the loginattempt endpoint'''
@app.route('/loginattempt', methods=['POST'])
def loginattempt():
    #this takes the user input
    attempted_id = request.form['loginid']
    attempted_pass = request.form['loginpass']
    #checks to see if the username is not empty
    if attempted_id=='' or attempted_pass=='':
        return redirect('/login')
    #checks to see if the the username is in users
    if attempted_id in users:
        #checkign the pass with hash
        if pbkdf2_sha256.verify(attempted_pass, users[attempted_id]):
            session['logged_in'] = True
            session['username'] = attempted_id
            return redirect('/profile')
        else:
            return redirect('/login')
    else:
        return redirect('/login')

'''making the register endpoint'''
@app.route('/register')
def rigister():
    return render_template("register.html")

'''making the registerattempt endpoint'''
@app.route('/registerattempt', methods=['POST'])
def registerattempt():
    #user input
    register_id = request.form['registerid']
    register_pass = request.form['registerpass']
    #checks if it is empty
    if (register_id == '') or (register_pass == ''):
        return redirect('/register')
    #checks if it has a space
    if ' ' in register_id:
        return redirect('/register')
    #hashes the password
    register_pass_hashed = pbkdf2_sha256.hash(register_pass)
    #checks if it has been used before
    if register_id in users:
        return redirect('/register')
    else:
        #this adds the user to the json of users
        users.update({register_id: register_pass_hashed})
        session['username'] = register_id
        session['logged_in'] = True
        file2 = open('users.json', 'w')
        json.dump(users, file2, indent=4)
        file2.close()

        #this adds teh user to the usermoney json
        money.update({register_id: "0"})
        file4 = open('usersmoney.json', 'w')
        json.dump(money, file4, indent=4)
        file4.close()

        return redirect('/profile')



'''making the profile endpoint'''
@app.route('/profile')
def profileredirect():
    #checks if the user is logged in
    if session['logged_in'] == False:
        return redirect('/login')
    return redirect('/profile/'+session['username'])

'''making the user profile endpoint'''
#this is the endpoint that follows the profile endpoint
@app.route('/profile/<user>')
def profile(user):
    usermoney = money[session['username']]
    return render_template('profile.html', user = user, usermoney = usermoney)

'''making the code attempt endpoint'''
#where the user sends the code to check it
@app.route('/codeattempt', methods=['POST'])
def codeattempt():
    #sees if the user is logged in
    if session['logged_in'] == False:
        return redirect('/login')
    #recieves the users input
    attempted_code = request.form['codeid']
    # checks if the input is empty or contains a space
    if attempted_code=='' or attempted_code==' ':
        return redirect('/profile')
    #looks if it is in codes
    if attempted_code in codes:
        newmoney = int(money[session['username']]) + int(codes[attempted_code])

        #updates the users money
        money.update({session['username']: newmoney})
        file4 = open('usersmoney.json', 'w')
        json.dump(money, file4, indent=4)
        file4.close()
        return redirect('/profile')
    else:
        return redirect('/profile')


if __name__ == "__main__":
    app.run(debug=True)
