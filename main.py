from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from functools import wraps
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from database_setup import Base, Item, User, Category
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///itemswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, categories=getAllCat())


# Google login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token == access_token and gplus_id == stored_gplus_id:
        msg = 'Current user is already connected.'
        response = make_response(json.dumps(msg),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    output += '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You have successfully logged out.")
        return response and redirect('/')
    else:
        msg = 'Failed to revoke token for given user.'
        response = make_response(json.dumps(msg, 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON APIs to view items information
@app.route('/item/<int:itemid>/JSON')
def oneItemJSON(itemid):
    item = session.query(Item).filter_by(id=itemid).one()
    return jsonify(item=item.serialize)


@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])


# JSON APIs to view categories
@app.route('/categories/JSON')
def allCatJSON():
    categories = session.query(Category)
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/<cat>/JSON')
def oneCatJSON(cat):
    category = session.query(Category).filter_by(name=cat).one()
    return jsonify(category=category.serialize)


# helper functions for frequent querying
def getAllCat():
    return session.query(Category).order_by(asc(Category.name))


# login check decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You must log in first.")
            return redirect('/login')
    return decorated_function


# shows all items ordered by latest items
@app.route('/')
@app.route('/items')
def showItems():
    items = session.query(Item).order_by(desc(Item.time_added))
    return render_template("items.html", items=items,
                           categories=getAllCat(),
                           header="Latest items:")


# show items of a specific category
@app.route('/categories/<cate>')
def showCategorizedItems(cate):
    category = session.query(Category).filter_by(name=cate).one()
    items = category.items

    return render_template("items.html", items=items,
                           categories=getAllCat(),
                           header=cate.title() +
                           " Items ("+str(len(items))+" items)")


# create a new item
@app.route('/newitem', methods=['GET', 'POST'])
@login_required
def addItem():
    if request.method == 'POST':
        name = request.form['name']
        c_name = request.form['cate'].lower()
        category = None
        existing_c = session.query(Category).filter_by(name=c_name)
        # check if a category already exists
        if existing_c.first():
            category = existing_c.one()
        else:
            category = Category(name=c_name)
            session.add(category)

        description = request.form['description']
        user_id = login_session['user_id']
        item = Item(name=name, category=category,
                    user_id=user_id, description=description)
        session.add(item)
        session.commit()
        flash("Item successfully added!")
        return redirect(url_for('singleItem', itemid=item.id))
    else:
        return render_template("new-item.html",
                               categories=getAllCat(),
                               header="Add a new item:")


# shows a single item
@app.route('/item/<int:itemid>')
def singleItem(itemid):
    item = session.query(Item).filter_by(id=itemid).one()
    return render_template("one-item.html", item=item, categories=getAllCat())


# edit an item
@app.route('/<int:itemid>/edititem', methods=['GET', 'POST'])
@login_required
def editItem(itemid):
    item = session.query(Item).filter_by(id=itemid).one()
    if item.user_id != login_session['user_id']:
        error = "You cannot edit other people's items!"
        return render_template("one-item.html", item=item,
                               categories=getAllCat(), error=error)
    if request.method == 'POST':
        item.name = request.form['name']
        category = None
        c_name = request.form['cate']
        existing_c = session.query(Category).filter_by(name=c_name.lower())
        # check if a category already exists
        if existing_c.first():
            category = existing_c.one()
        else:
            category = Category(name=c_name)
            session.add(category)
        item.category = category
        item.description = request.form['description']
        session.commit()
        flash("You have successfully edited this item!")
        return redirect('/item/' + str(item.id))
    else:
        return render_template('new-item.html',
                               categories=getAllCat(),
                               header="Edit item:",
                               name=item.name,
                               category=item.category.name,
                               description=item.description
                               )


# delete an item
@app.route('/<int:itemid>/deleteitem', methods=['GET', 'POST'])
@login_required
def deleteItem(itemid):
    item = session.query(Item).filter_by(id=itemid).one()
    if item.user_id != login_session['user_id']:
        error = "You cannot delete other people's items!"
        return render_template("one-item.html", item=item,
                               categories=getAllCat(), error=error)

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("You have successfully deleted your item!")
        return redirect('/')
    else:
        return render_template('delete-item.html', item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
