from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
from bcrypt import hashpw, gensalt
import mysql.connector
import urllib.request
import json
import math

import os, encodings

cnx = mysql.connector.connect(  # Here I connect to the database that is setup in xampp running apache.
  host="localhost",
  user="root",
  passwd="",
  database="usersdatabase"
)

app = Flask(__name__)
app.secret_key = '\xf1q=\xac\x98b\x1f\\\xf2\x95MGj\xe4g:\x0b\x0fP\xdb\xe4\x93\xae\xa1'  # Secret key used for sessions!


'''
In the signup route I use a form from html using the post method to grab the data. I then generate my salt wich I use
to hash the password I just recieved. I then save the hashed password, salt, email and username to the database
After that I then redirect them to login!
'''
@app.route('/signup', methods=['POST'])
def signup():
    try:
        name = request.form['name']
        email = request.form['e-mail']      # Grabbing the users inputs from the html form!
        password = request.form['password']
        salt = gensalt(12)
        hashed = hashpw(password.encode('utf8'), salt)  # Hashing the Password
        cursor = cnx.cursor(buffered=True)
        sql = "INSERT INTO `users`(`email`, `display_name`, `password`, `salt`) VALUES (%s, %s, %s, %s)"     # Saving their credentials to the database!
        val = (email, name, hashed, salt)
        cursor.execute(sql, val)
        cnx.commit()
        return redirect('/LoginLoad', code=302)     # Redirecting them to the login screen.
    except ValueError:
        return "A user with those credentials already exists"


'''
In the login route I first check if there in a session if not I then hash the password they gave me and compare that
password to the hashed password I have saved in my database. After that is done I create a session and then render the
dashboard template that fills up with all the posts I grabbed from my database.
'''
@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'username' in session:   # Checking if they are in a session and if so loading up the homepage!
        return render_template('dashboard.html', username=session['username'])
    else:
        try:
            name_entered = request.form['name']             #Grabbing there details off of login form.
            password_entered = request.form['password']
            cursor = cnx.cursor(buffered=True)
            sql_select_query = "select `password` from `users` where `display_name` = %s"
            cursor.execute(sql_select_query, (name_entered,))
            record, = cursor.fetchone()                                                 #Grabbing Salt and Hash from database
            salt_query = "select `salt` from `users` where `display_name` = %s"
            cursor.execute(salt_query, (name_entered,))
            salt = cursor.fetchone()[0]
            if hashpw(password_entered.encode('utf8'), salt) == record:     # Then comparing both hashed passwords.
                session['username'] = name_entered
                return render_template('dashboard.html', username=name_entered)     # Renders the homepage
            else:
                return 'Incorrect Username or Password'
        except:
            return 'There was an error! please try logging in again. Or message Nolsters#1038 on discord!'



'''
This loads up the login html file.
'''
@app.route('/LoginLoad')
def LoginLoad():
    return render_template('login.html')


'''
This module logs the users out by canceling there session and redirecting them back to the login screen.
'''
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/LoginLoad')


@app.route('/stock', methods=['POST', 'GET'])
def stock_info():
    if 'username' in session:
        stock = request.form['stock']
        price = 'https://cloud.iexapis.com/stable/stock/'+stock+'/price?token=sk_7b92c602fb5c4a24a1e0eb4161b961bc'
        logo = 'https://cloud.iexapis.com/stable/stock/'+stock+'/logo?token=sk_7b92c602fb5c4a24a1e0eb4161b961bc'
        print(price, logo)
        logo_json = json.loads(urllib.request.urlopen(logo).read().decode("utf-8"))
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select `stock_values` from `holdings` where `display_name` = (%s) and `stock_name` = (%s)"
        cursor.execute(sql_select_query,(session['username'], stock))
        record = cursor.fetchall()
        print(record)
        price_final = float(urllib.request.urlopen(price).read().decode("utf-8"))
        listOfValues = [element for tupl in record for element in tupl]
        return render_template('stock.html', price=price_final, logo=logo_json['url'], holdings=(sum(listOfValues)*price_final))
    else:
        return redirect('/LoginLoad', code=302)




'''
Loads up the html signup file.
'''
@app.route('/')
def hello_world():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return render_template('signup.html')


@app.route('/buy', methods=['POST', 'GET'])
def buy():
    try:
        stock_ammount = request.form['buy']
        stock = request.form['stock']
        cursor = cnx.cursor(buffered=True)
        sql = "UPDATE `holdings` SET `stock_values` = `stock_values`+(%s) WHERE `stock_name` = (%s) AND `display_name` = (%s);"
        val = (stock_ammount, stock, session['username'])
        cursor.execute(sql, val)
        cnx.commit()
        return redirect('/stock')
    except:
        print('broke')
        stock_ammount = request.form['buy']
        stock = request.form['stock']
        cursor = cnx.cursor(buffered=True)
        sql = "INSERT INTO `holdings`(`display_name`, `stock_name`, `stock_values`) VALUES (%s, %s, %s)"
        val = (session['username'], stock, stock_ammount)
        cursor.execute(sql, val)
        cnx.commit()
        return redirect('/stock')

@app.route('/sell', methods=['POST', 'GET'])
def sell():
    stock_ammount = request.form['sell']
    stock = request.form['stock']
    cursor = cnx.cursor(buffered=True)
    sql = "DELETE FROM `holdings` [WHERE `stock_name` = stock];"
    val = (session['username'], stock, stock_ammount)
    cursor.execute(sql, val)
    cnx.commit()
    return redirect('/stock', code=302)


'''
This starts the application
'''
if __name__ == '__main__':
    app.run(debug=True)
