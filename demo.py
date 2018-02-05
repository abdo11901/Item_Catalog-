from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from sqlalchemy import desc

app = Flask(__name__)

#
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Category Application "


# JSON APIs to view Categories and items Information
@app.route('/categoryItem/JSON')
def categoryItemJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(categories=[r.serialize for r in categories],
                   items=[r.serialize for r in items])


@app.route('/Item/JSON/<int:item_id>')
def itemJSON(item_id):
    items = session.query(Item).filter_by(id=item_id).all()
    return jsonify(item=[r.serialize for r in items])


# Connect to Database and create database session
engine = create_engine('sqlite:///categoryitems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# connecting using google API
@app.route('/gconnect', methods=['POST'])
def gconnect():
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
        print
        "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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

    try:
        user = session.query(User).filter_by(email=data['email']).one()
    except:
        user = User(name=data['name'], email=data['email'])
    login_session['user_id'] = user.id
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; ' \
              'height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: ' \
              '150px;-moz-border-radius: 150px;"> '
    print
    "done!"
    return output


# Disconnection using google API
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print
        'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print
    'In gdisconnect access token is %s', access_token
    print
    'User name is: '
    print
    login_session['username']
    url = 'https://accounts.google.com/o/oauth2/' \
          'revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print
    'result is '
    print
    result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['user_id']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('categories'))
    else:
        response = make_response(json.dumps('Failed to revoke token '
                                            'for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('categories'))


# Show all categories
@app.route('/', methods=['GET'])
def categories():
    cats = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.id)).limit(10)
    items = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template('categories.html', categories=cats, items=items)


# Show category by id
@app.route('/category/<int:category_id>/')
def CategoryItem(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template(
        'category.html', categories=categories, items=items, category=category)


# Show item by id
@app.route('/item/<int:item_id>/')
def item(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    thisuser = False
    print(item.user_id)
    try:
        if login_session['user_id'] == item.user_id:
            thisuser = True
        else:
            thisuser = False
    except:
        thisuser = False

    return render_template('item.html', item=item, thisuser=thisuser)


# create Item
@app.route('/item/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect(url_for('categories'))
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            user_id=login_session['user_id'], description=request.form[
                'description'], category_id=request.form[
                'category'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('item', item_id=newItem.id))
    else:
        categories = session.query(Category).all()
        return render_template('newItem.html', categories=categories)


# edit Item
@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('categories'))
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != editedItem.user_id:
        return redirect(url_for('categories'))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('item', item_id=editedItem.id))
    else:
        categories = session.query(Category).all()

        return render_template(
            'editItem.html', item=editedItem, categories=categories)


@app.route('/reset')
def reset():
    login_session['user_id'] = 2
    del login_session['user_id']
    del login_session['username']
    del login_session['gplus_id']
    del login_session['access_token']
    del login_session['email']
    return ""


# Delete item
@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('categories'))
    deleteItem = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != deleteItem.user_id:
        return redirect(url_for('categories'))
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('categories'))
    else:
        return render_template('deleteItem.html', item=deleteItem)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
