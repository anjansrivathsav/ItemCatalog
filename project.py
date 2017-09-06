from flask import Flask, render_template, url_for, request, jsonify, render_template, redirect, flash
from sqlalchemy import create_engine,asc,desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base,CatalogItem,Items,User
import json
from flask import session as login_session
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
APPLICATION_NAME = "Sportsapp"

##connecting to the database

engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
session = DBsession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    #flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output



def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        result = session.query(Items).join(CatalogItem).order_by(desc(Items.id)).all()
        catalog = session.query(CatalogItem).all()
        return render_template('publicsports.html',result = result,catalog = catalog)
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


#json functions to return the json response
@app.route('/catalog/items/json')
def catalogjson():
    result = session.query(CatalogItem).all()
    return jsonify(Catalog=[i.serialize for i in result])

@app.route('/catalog/<int:catalog_id>/json')
def catalogitemjson(catalog_id):
    result = session.query(CatalogItem).filter_by(id = catalog_id).all()
    return jsonify(totalitems = [i.serialize for i in result])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/json')
def Itemjson(catalog_id,item_id):
    result = session.query(Items).filter_by(id = item_id).one()
    return jsonify(result.serialize)

# The main page to display the catalogitems and items latestly added
@app.route('/')
def Catalog():
    result = session.query(Items).join(CatalogItem).order_by(desc(Items.id)).all()
    catalog = session.query(CatalogItem).all()
    return render_template('publicsports.html',result = result,catalog = catalog )


# the function which displays the catalogs and their items
@app.route('/catalogitem/<int:catalog_id>/items')
def Catalogi(catalog_id):
    result = session.query(Items).filter_by(catalog_id= catalog_id).all()
    catalog = session.query(CatalogItem).all()
    return render_template('catalogitems.html',result = result,catalog = catalog)


#the fuction to display the the particular item
@app.route('/catalogitem/<int:catalog_id>/item/<int:item_id>/')
def Catalogdes(catalog_id,item_id):
    result = session.query(Items).filter_by(id =item_id).one()
    return render_template('descriptionitem.html',result = result)

#adding the new catalog
@app.route('/catalogitem/new', methods=['GET', 'POST'])
def newcatalog():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = CatalogItem(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCatalog)
        flash('new catalog %s is successfully created' %newCatalog.name)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('newCatalog.html')

#editing the catalog
@app.route('/catalogitem/<int:catalog_id>/edit' , methods=['GET','POST'])
def editcatalog(catalog_id):
    editCatalog = session.query(CatalogItem).filter_by(id = catalog_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editCatalog.user_id != login_session['user_id']:
        return "<script>you cant make the changes as you are not the actual creator of this</script>"
    if request.method == 'POST':
        if request.form['name']:
            editCatalog.name = request.form['name']
            flash("succesfully edited")
            return redirect(url_for('Catalog'))
    else:
        return render_template('editcatalog.html')

#deleting the catalog
@app.route('/catalogitem/<int:catalog_id>/delete/' , methods=['GET','POST'])
def deletecatalog(catalog_id):
    deletecatalog = session.query(CatalogItem).filter_by(id = catalog_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if deletecatalog.user_id != login_session['user_id']:
        return "<script>you are not the actual actual creator </script>"
    else:
        session.delete(deletecatalog)
        flash("successfully deleted")
        session.commit()
        return render_template('publicsports.html')


#adding  a new item in a particular catalog
@app.route('/catalogitem/<int:catalog_id>/item/new/',methods=['GET','POST'])
def additem(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Items(name=request.form['name'], description = request.form['description'],catalog_id = catalog_id,user_id=login_session['user_id'])
        session.add(newItem)
        flash("added item succesfully")
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('additem.html')

#editiing the already existing item
@app.route('/catalogitem/<int:catalog_id>/item/<int:item_id>/edit',methods=['GET','POST'])
def edititem(catalog_id,item_id):
    if 'username' not in login_session:
        return redirect('/login')
    edititem = session.query(Items).filter_by(id = item_id).one()
    if edititem.user_id != login_session['user_id']:
        return "<script>you can't make changes to this as you are not the original creator</script>"
    if request.method == 'POST':
        if request.form['name'] or request.form['description']:
            edititem.name = request.form['name']
            edititem.description  = request.form['description']
            session.add(edititem)
            flash("successfully edited")
            session.commit()
            return redirect(url_for('Catalog'))
    else:
        return render_template('edititem.html')

#deleting the item from a particular catalog
@app.route('/catalogitem/<int:catalog_id>/item/<int:item_id>/delete',methods=['GET','POST'])
def deleteitem(catalog_id,item_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteitem = session.query(Items).filter_by(id = item_id).one()
    if deleteitem.user_id != login_session['user_id']:
        return "<script>you are not the actual owner of this item</script>"
    else:
        session.delete(deleteitem)
        flash("item delete succesfully")
        session.commit()
        return render_template('publicsports.html')





if __name__ == '__main__':
    app.secret_key = "secret_key"
    app.debug = True
    app.run(host='0.0.0.0',port=8000)
