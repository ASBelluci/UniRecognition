from flask import Flask, Response
from utils.Reconhecimento import ReconhecimentoFacial
import psycopg2
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from utils.Helpers import apology, login_required

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

aluno_data_file = 'salas\\BCC\\2A.json'
classifier_file = 'src\\frontalFaceHaarcascade.xml'
recognizer_file = 'src\\classificadores\\classificadorLBPH_V1.yml'

reconhecimento = ReconhecimentoFacial(aluno_data_file, classifier_file, recognizer_file)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
con = psycopg2.connect(
	host='localhost', 
	database='postgres', 
	port='5432',
	user='postgres', 
	password='unimar'
)

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route('/rec')
def rec():
    return Response(gen(reconhecimento),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/reconhecer", methods=["GET"])
@login_required
def reconhecer():
    cursor = con.cursor()
    sql = """SELECT * FROM aluno WHERE id_aula = (SELECT id_aula FROM aula WHERE id_aula = %s) ORDER BY nome;"""
    cursor.execute(sql, (1,))
    data = cursor.fetchall()

    return render_template('reconhecer.html', data=data)

@app.route("/registrar", methods=["GET"])
@login_required
def registrar():
    cursor = con.cursor()
    sql = """SELECT nome, id_aula FROM aula ORDER BY nome;"""
    cursor.execute(sql, (1,))
    data = cursor.fetchall()
    print(sql)

    return render_template('registrar.html', data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        cursor = con.cursor()
        sql = """SELECT * FROM usuario WHERE login = %s;"""
        cursor.execute(sql, (request.form.get("username"),))
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session['alert'] = 'Login sucessful!'
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)

def gen(camera):
    while True:
        frame = camera.run()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
