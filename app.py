from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for
)

from flask_socketio import SocketIO
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import sqlite3
from datetime import datetime


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "CHANGE_THIS_SECRET_KEY"

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

DATABASE = "register.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            full_name TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'user'

        )
    """)


    # --------------------------------------------------------
    # EMPLOYEES
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_name TEXT NOT NULL,

            designation TEXT NOT NULL

        )
    """)


    # --------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS components (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            component_id TEXT UNIQUE NOT NULL,

            component_name TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'AVAILABLE'

        )
    """)


    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            component_id INTEGER NOT NULL,

            employee_id INTEGER NOT NULL,

            recorded_by INTEGER NOT NULL,

            out_time TEXT NOT NULL,

            returned_time TEXT,

            status TEXT NOT NULL DEFAULT 'OUT',

            FOREIGN KEY(component_id)
                REFERENCES components(id),

            FOREIGN KEY(employee_id)
                REFERENCES employees(id),

            FOREIGN KEY(recorded_by)
                REFERENCES users(id)

        )
    """)


    conn.commit()


    # --------------------------------------------------------
    # CREATE DEFAULT ADMIN
    # --------------------------------------------------------

    admin = conn.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, ("admin",)).fetchone()


    if admin is None:

        password_hash = generate_password_hash(
            "admin123"
        )

        conn.execute("""
            INSERT INTO users
            (
                username,
                password,
                full_name,
                role
            )

            VALUES (?, ?, ?, ?)
        """, (
            "admin",
            password_hash,
            "Administrator",
            "admin"
        ))


    conn.commit()

    conn.close()


# ============================================================
# LOGIN USER CLASS
# ============================================================

class User(UserMixin):

    def __init__(
        self,
        user_id,
        username,
        full_name,
        role
    ):

        self.id = user_id

        self.username = username

        self.full_name = full_name

        self.role = role


@login_manager.user_loader
def load_user(user_id):

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    conn.close()


    if row is None:

        return None


    return User(
        row["id"],
        row["username"],
        row["full_name"],
        row["role"]
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()

        row = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        conn.close()


        if row and check_password_hash(
            row["password"],
            password
        ):

            user = User(
                row["id"],
                row["username"],
                row["full_name"],
                row["role"]
            )

            login_user(user)

            return redirect(
                url_for("index")
            )


        return render_template(
            "login.html",
            error="Invalid username or password"
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# ============================================================
# MAIN PAGE
# ============================================================

@app.route("/")
@login_required
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# GET COMPONENTS
# ============================================================

@app.route(
    "/api/components",
    methods=["GET"]
)
@login_required
def get_components():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM components
        ORDER BY component_name
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# ADD COMPONENT
# ============================================================

@app.route(
    "/api/components",
    methods=["POST"]
)
@login_required
def add_component():

    data = request.json


    component_id = data.get(
        "component_id",
        ""
    ).strip()

    component_name = data.get(
        "component_name",
        ""
    ).strip()


    if not component_id or not component_name:

        return jsonify({
            "success": False,
            "message": "Component ID and name are required."
        }), 400


    conn = get_db()


    try:

        conn.execute("""
            INSERT INTO components
            (
                component_id,
                component_name,
                status
            )

            VALUES (?, ?, 'AVAILABLE')
        """, (
            component_id,
            component_name
        ))

        conn.commit()


    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Component ID already exists."
        }), 400


    conn.close()


    socketio.emit(
        "components_changed"
    )


    return jsonify({
        "success": True
    })


# ============================================================
# GET EMPLOYEES
# ============================================================

@app.route(
    "/api/employees",
    methods=["GET"]
)
@login_required
def get_employees():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM employees
        ORDER BY employee_name
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# ADD EMPLOYEE
# ============================================================

@app.route(
    "/api/employees",
    methods=["POST"]
)
@login_required
def add_employee():

    data = request.json


    employee_name = data.get(
        "employee_name",
        ""
    ).strip()

    designation = data.get(
        "designation",
        ""
    ).strip()


    if not employee_name or not designation:

        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400


    conn = get_db()


    conn.execute("""
        INSERT INTO employees
        (
            employee_name,
            designation
        )

        VALUES (?, ?)
    """, (
        employee_name,
        designation
    ))


    conn.commit()

    conn.close()


    socketio.emit(
        "employees_changed"
    )


    return jsonify({
        "success": True
    })


# ============================================================
# GET TRANSACTIONS
# ============================================================

@app.route(
    "/api/records",
    methods=["GET"]
)
@login_required
def get_records():

    conn = get_db()


    rows = conn.execute("""
        SELECT

            t.id,

            c.component_id,

            c.component_name,

            e.employee_name,

            e.designation,

            u.full_name AS recorded_by,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

        JOIN employees e
            ON t.employee_id = e.id

        JOIN users u
            ON t.recorded_by = u.id

        ORDER BY t.id DESC

    """).fetchall()


    conn.close()


    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# MARK COMPONENT OUT
# ============================================================

@app.route(
    "/api/records",
    methods=["POST"]
)
@login_required
def add_record():

    data = request.json


    component_database_id = data.get(
        "component_database_id"
    )

    employee_id = data.get(
        "employee_id"
    )


    if not component_database_id or not employee_id:

        return jsonify({
            "success": False,
            "message": "Component and employee are required."
        }), 400


    conn = get_db()


    # --------------------------------------------------------
    # CHECK COMPONENT
    # --------------------------------------------------------

    component = conn.execute("""
        SELECT *
        FROM components
        WHERE id = ?
    """, (
        component_database_id,
    )).fetchone()


    if component is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Component not found."
        }), 404


    # --------------------------------------------------------
    # CHECK WHETHER ALREADY OUT
    # --------------------------------------------------------

    if component["status"] == "OUT":

        conn.close()

        return jsonify({
            "success": False,
            "message": "This component is already OUT."
        }), 400


    # --------------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------------

    out_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


    # --------------------------------------------------------
    # CREATE TRANSACTION
    # --------------------------------------------------------

    cursor = conn.execute("""
        INSERT INTO transactions
        (
            component_id,
            employee_id,
            recorded_by,
            out_time,
            status
        )

        VALUES (?, ?, ?, ?, 'OUT')
    """, (
        component_database_id,
        employee_id,
        current_user.id,
        out_time
    ))


    transaction_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE COMPONENT STATUS
    # --------------------------------------------------------

    conn.execute("""
        UPDATE components

        SET status = 'OUT'

        WHERE id = ?
    """, (
        component_database_id,
    ))


    conn.commit()


    # --------------------------------------------------------
    # GET COMPLETE RECORD
    # --------------------------------------------------------

    row = conn.execute("""
        SELECT

            t.id,

            c.component_id,

            c.component_name,

            e.employee_name,

            e.designation,

            u.full_name AS recorded_by,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

        JOIN employees e
            ON t.employee_id = e.id

        JOIN users u
            ON t.recorded_by = u.id

        WHERE t.id = ?

    """, (
        transaction_id,
    )).fetchone()


    conn.close()


    record = dict(row)


    socketio.emit(
        "record_added",
        record
    )


    return jsonify({
        "success": True,
        "record": record
    })


# ============================================================
# RETURN COMPONENT
# ============================================================

@app.route(
    "/api/records/<int:record_id>/return",
    methods=["PUT"]
)
@login_required
def return_component(record_id):

    conn = get_db()


    transaction = conn.execute("""
        SELECT *
        FROM transactions
        WHERE id = ?
    """, (
        record_id,
    )).fetchone()


    if transaction is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Transaction not found."
        }), 404


    if transaction["status"] != "OUT":

        conn.close()

        return jsonify({
            "success": False,
            "message": "Component has already been returned."
        }), 400


    returned_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


    # --------------------------------------------------------
    # UPDATE TRANSACTION
    # --------------------------------------------------------

    conn.execute("""
        UPDATE transactions

        SET

            returned_time = ?,

            status = 'RETURNED'

        WHERE id = ?

    """, (
        returned_time,
        record_id
    ))


    # --------------------------------------------------------
    # UPDATE COMPONENT
    # --------------------------------------------------------

    conn.execute("""
        UPDATE components

        SET status = 'AVAILABLE'

        WHERE id = ?

    """, (
        transaction["component_id"],
    ))


    conn.commit()


    # --------------------------------------------------------
    # GET UPDATED RECORD
    # --------------------------------------------------------

    row = conn.execute("""
        SELECT

            t.id,

            c.component_id,

            c.component_name,

            e.employee_name,

            e.designation,

            u.full_name AS recorded_by,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

        JOIN employees e
            ON t.employee_id = e.id

        JOIN users u
            ON t.recorded_by = u.id

        WHERE t.id = ?

    """, (
        record_id,
    )).fetchone()


    conn.close()


    record = dict(row)


    socketio.emit(
        "record_returned",
        record
    )


    return jsonify({
        "success": True,
        "record": record
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    init_db()


    print()
    print("=" * 50)
    print("COMPONENT IN/OUT REGISTER")
    print("=" * 50)
    print()
    print("Open locally:")
    print("http://127.0.0.1:5000")
    print()
    print("For other computers:")
    print("http://SERVER_IP:5000")
    print()
    print("Default admin:")
    print("Username: admin")
    print("Password: admin123")
    print()
    print("=" * 50)


    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )