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
# TESTING TEAM LOGIN USERS
#
# Add / edit usernames and passwords here.
# Format:
# ("username", "password", "Full Name", "role")
# ============================================================

TESTING_TEAM_USERS = [
    ("vaishakh", "vaishakh123", "Vaishakh Varier", "user"),
    ("sahil", "sahil123", "Sahil Pankar", "user"),
    ("snehal", "snehal123", "Snehal", "user"),
]


# ============================================================
# EMPLOYEE MASTER LIST
#
# Add / edit employee names and designations here.
# Format:
# ("Employee Name", "Designation")
# ============================================================

EMPLOYEE_LIST = [
    ("Nishant S", "General Manager"),
    ("Vaishnavi N", "Product Manager"),
    ("Sahil P", "IoT Engineer"),
    ("Ganesh R", "IoT Engineer"),
    ("Gayatri S", "IoT Engineer"),
    ("Snehal B", "Senior Test Engineer"),
    ("Vaishakh V", "IoT Engineer"),
    ("Ram G", "Embedded SW Engineer"),
    ("Dipak D", "HW Team"),
    ("Preeti", "HW Team"),
    ("Sharad A", "HW Manager"),
    ("Sai Teja", "Developer"),
    ("Prasanna G", "Asst Prod Manager"),
    ("Aniket S", "RnR"),
]


# ============================================================
# DATABASE
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def column_exists(conn, table_name, column_name):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


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

            component_id TEXT UNIQUE,

            component_name TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'AVAILABLE',

            total_quantity INTEGER NOT NULL DEFAULT 1,

            available_quantity INTEGER NOT NULL DEFAULT 1

        )
    """)


    # --------------------------------------------------------
    # MIGRATE OLD COMPONENT TABLE
    # --------------------------------------------------------

    if not column_exists(
        conn,
        "components",
        "total_quantity"
    ):

        conn.execute("""
            ALTER TABLE components
            ADD COLUMN total_quantity INTEGER
            NOT NULL DEFAULT 1
        """)


    if not column_exists(
        conn,
        "components",
        "available_quantity"
    ):

        conn.execute("""
            ALTER TABLE components
            ADD COLUMN available_quantity INTEGER
            NOT NULL DEFAULT 1
        """)


    # --------------------------------------------------------
    # MIGRATE OLD COMPONENT STATUS TO QUANTITY
    # --------------------------------------------------------

    conn.execute("""
        UPDATE components

        SET total_quantity = 1

        WHERE total_quantity IS NULL
        OR total_quantity <= 0
    """)


    conn.execute("""
        UPDATE components

        SET available_quantity =
            CASE
                WHEN status = 'OUT' THEN 0
                ELSE 1
            END

        WHERE available_quantity IS NULL
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

            employee_name TEXT,

            designation TEXT,

            quantity_out INTEGER NOT NULL DEFAULT 1,

            quantity_returned INTEGER NOT NULL DEFAULT 0,

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


    # --------------------------------------------------------
    # MIGRATE OLD TRANSACTIONS
    # --------------------------------------------------------

    if not column_exists(
        conn,
        "transactions",
        "employee_name"
    ):

        conn.execute("""
            ALTER TABLE transactions
            ADD COLUMN employee_name TEXT
        """)


    if not column_exists(
        conn,
        "transactions",
        "designation"
    ):

        conn.execute("""
            ALTER TABLE transactions
            ADD COLUMN designation TEXT
        """)


    if not column_exists(
        conn,
        "transactions",
        "quantity_out"
    ):

        conn.execute("""
            ALTER TABLE transactions
            ADD COLUMN quantity_out INTEGER
            NOT NULL DEFAULT 1
        """)


    if not column_exists(
        conn,
        "transactions",
        "quantity_returned"
    ):

        conn.execute("""
            ALTER TABLE transactions
            ADD COLUMN quantity_returned INTEGER
            NOT NULL DEFAULT 0
        """)


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


    # --------------------------------------------------------
    # CREATE TESTING TEAM USERS
    # --------------------------------------------------------

    for username, password, full_name, role in TESTING_TEAM_USERS:

        existing_user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()


        if existing_user is None:

            password_hash = generate_password_hash(
                password
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
                username,
                password_hash,
                full_name,
                role
            ))


    # --------------------------------------------------------
    # ADD EMPLOYEE MASTER LIST
    # --------------------------------------------------------

    for employee_name, designation in EMPLOYEE_LIST:

        existing_employee = conn.execute("""
            SELECT *
            FROM employees
            WHERE employee_name = ?
            AND designation = ?
        """, (
            employee_name,
            designation
        )).fetchone()


        if existing_employee is None:

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


    # --------------------------------------------------------
    # ENSURE OTHER EMPLOYEE EXISTS
    #
    # This is only an internal placeholder.
    # It will not be shown in the normal employee dropdown.
    # Actual Other person's name/designation is stored
    # separately in the transaction.
    # --------------------------------------------------------

    other_employee = conn.execute("""
        SELECT *
        FROM employees
        WHERE employee_name = ?
        AND designation = ?
    """, (
        "__OTHER__",
        "__OTHER__"
    )).fetchone()


    if other_employee is None:

        conn.execute("""
            INSERT INTO employees
            (
                employee_name,
                designation
            )

            VALUES (?, ?)
        """, (
            "__OTHER__",
            "__OTHER__"
        ))


    # --------------------------------------------------------
    # BACKFILL OLD TRANSACTION EMPLOYEE DETAILS
    # --------------------------------------------------------

    conn.execute("""
        UPDATE transactions

        SET
            employee_name = (
                SELECT employee_name
                FROM employees
                WHERE employees.id = transactions.employee_id
            ),

            designation = (
                SELECT designation
                FROM employees
                WHERE employees.id = transactions.employee_id
            )

        WHERE employee_name IS NULL
        OR designation IS NULL
    """)


    # --------------------------------------------------------
    # UPDATE QUANTITY VALUES FOR OLD RECORDS
    # --------------------------------------------------------

    conn.execute("""
        UPDATE transactions

        SET quantity_out = 1

        WHERE quantity_out IS NULL
        OR quantity_out <= 0
    """)


    conn.execute("""
        UPDATE transactions

        SET quantity_returned = 0

        WHERE quantity_returned IS NULL
    """)


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

    component_name = data.get(
        "component_name",
        ""
    ).strip()

    quantity = data.get(
        "quantity",
        0
    )


    try:

        quantity = int(quantity)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Quantity must be a valid number."
        }), 400


    if not component_name:

        return jsonify({
            "success": False,
            "message": "Component name is required."
        }), 400


    if quantity <= 0:

        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero."
        }), 400


    conn = get_db()


    existing = conn.execute("""
        SELECT *
        FROM components
        WHERE LOWER(component_name) = LOWER(?)
    """, (
        component_name,
    )).fetchone()


    if existing:

        conn.execute("""
            UPDATE components

            SET
                total_quantity =
                    total_quantity + ?,

                available_quantity =
                    available_quantity + ?,

                status = 'AVAILABLE'

            WHERE id = ?
        """, (
            quantity,
            quantity,
            existing["id"]
        ))

    else:

        conn.execute("""
            INSERT INTO components
            (
                component_name,
                status,
                total_quantity,
                available_quantity
            )

            VALUES (?, 'AVAILABLE', ?, ?)
        """, (
            component_name,
            quantity,
            quantity
        ))


    conn.commit()

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
        WHERE employee_name != '__OTHER__'
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

            c.component_name,

            t.employee_name,

            t.designation,

            u.full_name AS recorded_by,

            t.quantity_out,

            t.quantity_returned,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

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


    quantity = data.get(
        "quantity"
    )


    employee_id = data.get(
        "employee_id"
    )


    other_employee_name = data.get(
        "other_employee_name",
        ""
    ).strip()


    other_designation = data.get(
        "other_designation",
        ""
    ).strip()


    if not component_database_id:

        return jsonify({
            "success": False,
            "message": "Component is required."
        }), 400


    try:

        quantity = int(quantity)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Quantity must be a valid number."
        }), 400


    if quantity <= 0:

        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero."
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
    # CHECK AVAILABLE QUANTITY
    # --------------------------------------------------------

    if quantity > component["available_quantity"]:

        conn.close()

        return jsonify({
            "success": False,
            "message":
                f"Only {component['available_quantity']} "
                f"unit(s) of this component are available."
        }), 400


    # --------------------------------------------------------
    # EMPLOYEE
    # --------------------------------------------------------

    if employee_id == "other":

        if not other_employee_name or not other_designation:

            conn.close()

            return jsonify({
                "success": False,
                "message":
                    "Please enter the name and designation."
            }), 400


        other_employee = conn.execute("""
            SELECT id
            FROM employees
            WHERE employee_name = '__OTHER__'
            AND designation = '__OTHER__'
        """).fetchone()


        if other_employee is None:

            conn.execute("""
                INSERT INTO employees
                (
                    employee_name,
                    designation
                )

                VALUES ('__OTHER__', '__OTHER__')
            """)

            conn.commit()


            other_employee = conn.execute("""
                SELECT id
                FROM employees
                WHERE employee_name = '__OTHER__'
                AND designation = '__OTHER__'
            """).fetchone()


        employee_database_id = other_employee["id"]

        employee_name = other_employee_name

        designation = other_designation

    else:

        if not employee_id:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Employee is required."
            }), 400


        employee = conn.execute("""
            SELECT *
            FROM employees
            WHERE id = ?
        """, (
            employee_id,
        )).fetchone()


        if employee is None:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Employee not found."
            }), 404


        employee_database_id = employee["id"]

        employee_name = employee["employee_name"]

        designation = employee["designation"]


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
            employee_name,
            designation,
            quantity_out,
            quantity_returned,
            out_time,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'OUT')
    """, (
        component_database_id,
        employee_database_id,
        current_user.id,
        employee_name,
        designation,
        quantity,
        out_time
    ))


    transaction_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE COMPONENT QUANTITY
    # --------------------------------------------------------

    new_available_quantity = (
        component["available_quantity"] - quantity
    )


    new_status = (
        "OUT"
        if new_available_quantity == 0
        else "AVAILABLE"
    )


    conn.execute("""
        UPDATE components

        SET
            available_quantity = ?,

            status = ?

        WHERE id = ?
    """, (
        new_available_quantity,
        new_status,
        component_database_id
    ))


    conn.commit()


    # --------------------------------------------------------
    # GET COMPLETE RECORD
    # --------------------------------------------------------

    row = conn.execute("""
        SELECT

            t.id,

            c.component_name,

            t.employee_name,

            t.designation,

            u.full_name AS recorded_by,

            t.quantity_out,

            t.quantity_returned,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

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


    socketio.emit(
        "components_changed"
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

    data = request.json or {}


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


    pending_quantity = (
        transaction["quantity_out"]
        - transaction["quantity_returned"]
    )


    if pending_quantity <= 0:

        conn.close()

        return jsonify({
            "success": False,
            "message": "All quantity has already been returned."
        }), 400


    quantity_returned_now = data.get(
        "quantity_returned",
        pending_quantity
    )


    try:

        quantity_returned_now = int(
            quantity_returned_now
        )

    except (TypeError, ValueError):

        conn.close()

        return jsonify({
            "success": False,
            "message": "Return quantity must be a valid number."
        }), 400


    if quantity_returned_now <= 0:

        conn.close()

        return jsonify({
            "success": False,
            "message":
                "Return quantity must be greater than zero."
        }), 400


    if quantity_returned_now > pending_quantity:

        conn.close()

        return jsonify({
            "success": False,
            "message":
                f"Only {pending_quantity} unit(s) "
                f"are currently OUT."
        }), 400


    new_quantity_returned = (
        transaction["quantity_returned"]
        + quantity_returned_now
    )


    fully_returned = (
        new_quantity_returned
        == transaction["quantity_out"]
    )


    returned_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


    new_status = (
        "RETURNED"
        if fully_returned
        else "PARTIALLY RETURNED"
    )


    # --------------------------------------------------------
    # UPDATE TRANSACTION
    # --------------------------------------------------------

    conn.execute("""
        UPDATE transactions

        SET

            quantity_returned = ?,

            returned_time = ?,

            status = ?

        WHERE id = ?

    """, (
        new_quantity_returned,
        returned_time if fully_returned else None,
        new_status,
        record_id
    ))


    # --------------------------------------------------------
    # UPDATE COMPONENT
    # --------------------------------------------------------

    conn.execute("""
        UPDATE components

        SET

            available_quantity =
                available_quantity + ?

        WHERE id = ?

    """, (
        quantity_returned_now,
        transaction["component_id"]
    ))


    # --------------------------------------------------------
    # UPDATE COMPONENT STATUS
    # --------------------------------------------------------

    component = conn.execute("""
        SELECT *
        FROM components
        WHERE id = ?
    """, (
        transaction["component_id"],
    )).fetchone()


    component_status = (
        "OUT"
        if component["available_quantity"] == 0
        else "AVAILABLE"
    )


    conn.execute("""
        UPDATE components

        SET status = ?

        WHERE id = ?

    """, (
        component_status,
        transaction["component_id"]
    ))


    conn.commit()


    # --------------------------------------------------------
    # GET UPDATED RECORD
    # --------------------------------------------------------

    row = conn.execute("""
        SELECT

            t.id,

            c.component_name,

            t.employee_name,

            t.designation,

            u.full_name AS recorded_by,

            t.quantity_out,

            t.quantity_returned,

            t.out_time,

            t.returned_time,

            t.status

        FROM transactions t

        JOIN components c
            ON t.component_id = c.id

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


    socketio.emit(
        "components_changed"
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