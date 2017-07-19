from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT * FROM own WHERE id = :id", id = session["user_id"])
    for stock in rows:
        stock["name"] = lookup(stock["symbol"])["name"]
        stock["price"] = lookup(stock["symbol"])["price"]
    cash = db.execute("SELECT cash FROM users where id = :id", id = session["user_id"])[0]["cash"]
    return render_template("index.html", rows = rows, cash = cash)
    #rows = db.execute("SELECT * FROM users")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        share = int(request.form.get("share"))
        stock = lookup(symbol)
        if stock == None:
            return render_template("buy.html", error1 = "invalid symbol", output = 0)
        if share < 1:
            return render_template("buy.html", error2 = "invalid share", output = 0)
        price = stock["price"] * share
        if db.execute("SELECT cash FROM users where id = :id", id = session["user_id"])[0]["cash"] < price:
            return apology("Cant Afford")
        username = db.execute("SELECT username FROM users where id = :id", id = session["user_id"])[0]["username"]
        db.execute("UPDATE users SET cash = cash - :price WHERE id = :id", price = price, id = session["user_id"])
        if len(db.execute("SELECT symbol from own where id=:id and symbol = :symbol", id = session["user_id"], symbol = symbol))!=0:
            db.execute("UPDATE own set share = share + :share where id=:id and symbol = :symbol", share = share, 
            id = session["user_id"], symbol = symbol)
        else:
            db.execute("INSERT INTO own (id, symbol, share) VALUES(:id,:symbol,:share)",id = session["user_id"], symbol = symbol, share = share)
        db.execute("INSERT INTO transac (id, username, symbol, share, price) VALUES(:id,:username,:symbol,:share,:price)",
        id = session["user_id"], username = username, symbol = symbol, share = share, price = price)
        display = db.execute("SELECT * FROM transac WHERE id = :id", id = session["user_id"]).pop()
        return render_template("buy.html", row = display, output = 1)
    else:
        return render_template("buy.html", output = 0)
    """Buy shares of stock."""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    display = db.execute("SELECT * FROM transac WHERE id = :id", id = session["user_id"])
    if display == []:
        return render_template("history.html", output = 0)
    display.reverse()
    return render_template("history.html",output = 1, rows = display)
    """Show history of transactions."""


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        stock = lookup(request.form.get("quote"))
        if stock == None:
            return render_template("quote.html", error = "Quote incorrect", stock = stock, output = 0)
        else:
            return render_template("quote.html", error = "", stock = stock, output = 1)
    else:
        return render_template("quote.html", error = "", stock = None, output = 0)
    """Get stock quote."""

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #render_template("register.html")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if username=='' or password == '' or confirm == '':
            return apology("Please do not leave a blank")
        if len(db.execute("SELECT * FROM users WHERE username = :username", username = username)) == 1:
            return apology("User already existed")
        if password != confirm:
            return apology("confirm incorrect")
        hash = pwd_context.encrypt(password)
        if len(db.execute("SELECT * FROM users WHERE hash = :hash", hash = hash)) == 1:
            return apology("password was already used")
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username = username, hash = hash)
        return redirect(url_for("login"))
        
    else:
        return render_template("register.html")
    """Register user."""

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    rows = db.execute("SELECT * FROM own WHERE id = :id", id = session["user_id"])
    for stock in rows:
        stock["name"] = lookup(stock["symbol"])["name"]
        stock["price"] = lookup(stock["symbol"])["price"]
    cash = db.execute("SELECT cash FROM users where id = :id", id = session["user_id"])[0]["cash"]
    if request.method == "POST":
        symbol = request.form.get("symbol")
        share = int(request.form.get("share"))
        if symbol not in [x["symbol"] for x in rows]:
            return render_template("sell.html", rows=rows, error1 = "you didn't own it", cash = cash)
        amount = db.execute("SELECT share from own where id = :id and symbol = :sym", id = session["user_id"], sym = symbol)[0]["share"]
        if share < 1 or share > amount:
            return render_template("sell.html", rows=rows,error2 = "invalid share", cash = cash)
        username = db.execute("SELECT username FROM users where id = :id", id = session["user_id"])[0]["username"]
        price = lookup(symbol)["price"]
        db.execute("INSERT INTO transac (id, username, symbol, share, price) VALUES(:id,:username,:symbol,:share,:price)",
        id = session["user_id"], username = username, symbol = symbol, share = -share, price = price)
        if amount - share > 0:
            db.execute("UPDATE own SET share = share - :s where id = :id and symbol=:x",s=share,id = session["user_id"], x=symbol)
        else:
            db.execute("DELETE from own where id = :id and symbol = :x",id = session["user_id"], x=symbol)
        db.execute("UPDATE users SET cash = cash + :s * :price where id = :id", s=share, price = price, id = session["user_id"])
        rows = db.execute("SELECT * FROM own WHERE id = :id", id = session["user_id"])
        for stock in rows:
            stock["name"] = lookup(stock["symbol"])["name"]
            stock["price"] = lookup(stock["symbol"])["price"]
        cash = db.execute("SELECT cash FROM users where id = :id", id = session["user_id"])[0]["cash"]
        return render_template("sell.html",rows=rows, cash=cash)
    else:
        return render_template("sell.html", rows = rows, cash = cash)
    """Sell shares of stock."""
