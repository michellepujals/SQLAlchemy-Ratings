"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
   
    return render_template("homepage.html")

@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route("/users/<user_id>")
def show_user_details(user_id):
    """Show user's age, zipcode, list of movies and ratings."""

    user = User.query.get(user_id)
    age = user.age
    zipcode = user.zipcode
    movies_and_ratings = user.ratings

    return render_template("user_details.html", user=user, age=age,
                            zipcode=zipcode, movies_and_ratings=movies_and_ratings)


@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by("title").all()

    return render_template("movie_list.html", movies=movies)

@app.route("/movies/<title>")
def show_movie_details(title):
    """Show info about a movie, including its list of ratings."""

    movie_object = Movie.query.filter_by(title=title).first()#instantiate a movie object
    movie_id = movie_object.movie_id  # get movie_id(PK) from the movie object
    movie = Movie.query.get(movie_id) # query the database to get a movie object using PK
    released_at = movie.released_at 
    imdb_url = movie.imdb_url
    list_of_ratings = movie.ratings # list of Rating objects for that specific movie

    return render_template("movie_details.html", movie=movie, title=title,
                            released_at=released_at, imdb_url=imdb_url,
                            list_of_ratings=list_of_ratings, 
                            hidden_movie_id=movie_id)


@app.route("/add_new_rating", methods=["POST"])
def add_new_rating():
    """ Add user's new rating."""
    user_id = session['user']
    hidden_movie_id = request.form.get("hidden_movie_id") #gets from the Jinja template/form
    new_score = request.form.get("new_score") #gets from the Jinja template/form
    
    current_user = User.query.filter_by(user_id=user_id).first() #queries db to get current user object
    rating = Rating.query.filter_by(user_id=user_id, movie_id=hidden_movie_id).first() #list of Ratings objects

    if rating: #if the rating already exists
       
        rating.score = new_score #then we update it
   
    else:
        
        rating = Rating(movie_id=hidden_movie_id, user_id=user_id,
                        score=new_score)
    
        db.session.add(rating) #if it does not exist, we add it as a new Rating object

    db.session.commit()

    title = rating.movie.title

    return redirect(f'/movies/{title}')



@app.route("/register", methods=["GET"])
def register_form():
    """User Registration."""


    return render_template("register_form.html")



@app.route("/register", methods=["POST"])
def register_process():

    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    user = User(email=email, password=password,
                 age=age, zipcode=zipcode)

    db.session.add(user)
    db.session.commit()


    return redirect('/')

@app.route("/login", methods =['GET'])
def user_login():
    """Display login page."""

    return render_template("login.html")



@app.route("/login", methods =['POST'])
def check_login_credentials():
    """Check user email and password against the database, login user."""

    email = request.form.get("email")
    password = request.form.get("password")
    user = User.query.filter_by(email=email).first() #queries the db for the User object
    
    if (user.password and user.email): #if the user already has an email and password
        if user.password == password: #check if the password is the same
            session['user'] = user.user_id #adds user to the session
            user_id_string = str(user.user_id) 
            flash("You are now logged in.")
            return redirect(f"/users/{user_id_string}")
        else:
            flash("Incorrect login information. Please try again.")
            return redirect("/login")

    return render_template("login.html", email=email, password=password, user=user)

@app.route("/logout")
def logout_user():
    """Allow user to logout."""

    session['user'] = None #clears the user's data from the session
    flash("You are now logged out.")

    return redirect("/")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
