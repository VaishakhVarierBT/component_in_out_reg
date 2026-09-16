const socket = io();


let records = [];

let components = [];

let employees = [];


// ============================================================
// LOAD EVERYTHING
// ============================================================

async function loadData() {

    await loadComponents();

    await loadEmployees();

    await loadRecords();

    updateStatistics();

}


// ============================================================
// COMPONENTS
// ============================================================

async function loadComponents() {

    const response =
        await fetch("/api/components");

    components =
        await response.json();


    renderComponentDropdown();

    updateStatistics();

}


function renderComponentDropdown() {

    const select =
        document.getElementById(
            "componentSelect"
        );


    select.innerHTML = `

        <option value="">
            Select component
        </option>

    `;


    components.forEach(component => {

        const option =
            document.createElement("option");


        option.value =
            component.id;


        option.textContent =
            `${component.component_id} - ${component.component_name} [${component.status}]`;


        if (component.status === "OUT") {

            option.disabled = true;

        }


        select.appendChild(option);

    });

}


// ============================================================
// EMPLOYEES
// ============================================================

async function loadEmployees() {

    const response =
        await fetch("/api/employees");

    employees =
        await response.json();


    renderEmployeeDropdown();

}


function renderEmployeeDropdown() {

    const select =
        document.getElementById(
            "employeeSelect"
        );


    select.innerHTML = `

        <option value="">
            Select employee
        </option>

    `;


    employees.forEach(employee => {

        const option =
            document.createElement("option");


        option.value =
            employee.id;


        option.textContent =
            `${employee.employee_name} - ${employee.designation}`;


        select.appendChild(option);

    });

}


// ============================================================
// RECORDS
// ============================================================

async function loadRecords() {

    const response =
        await fetch("/api/records");

    records =
        await response.json();


    renderTables();

    updateStatistics();

}


// ============================================================
// TAKE COMPONENT
// ============================================================

document
    .getElementById("outForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const component =
                document.getElementById(
                    "componentSelect"
                ).value;


            const employee =
                document.getElementById(
                    "employeeSelect"
                ).value;


            if (!component || !employee) {

                alert(
                    "Please select a component and employee."
                );

                return;

            }


            const response =
                await fetch(
                    "/api/records",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                component_database_id:
                                    component,

                                employee_id:
                                    employee

                            })

                    }
                );


            const result =
                await response.json();


            if (!result.success) {

                alert(result.message);

                return;

            }


            document
                .getElementById("outForm")
                .reset();

        }
    );


// ============================================================
// ADD COMPONENT
// ============================================================

document
    .getElementById("componentForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const componentId =
                document.getElementById(
                    "newComponentId"
                ).value;


            const componentName =
                document.getElementById(
                    "newComponentName"
                ).value;


            const response =
                await fetch(
                    "/api/components",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                component_id:
                                    componentId,

                                component_name:
                                    componentName

                            })

                    }
                );


            const result =
                await response.json();


            if (!result.success) {

                alert(result.message);

                return;

            }


            document
                .getElementById("componentForm")
                .reset();


            await loadComponents();

        }
    );


// ============================================================
// ADD EMPLOYEE
// ============================================================

document
    .getElementById("employeeForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const name =
                document.getElementById(
                    "newEmployeeName"
                ).value;


            const designation =
                document.getElementById(
                    "newDesignation"
                ).value;


            const response =
                await fetch(
                    "/api/employees",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                employee_name:
                                    name,

                                designation:
                                    designation

                            })

                    }
                );


            const result =
                await response.json();


            if (!result.success) {

                alert(result.message);

                return;

            }


            document
                .getElementById("employeeForm")
                .reset();


            await loadEmployees();

        }
    );


// ============================================================
// RETURN COMPONENT
// ============================================================

async function returnComponent(id) {

    const confirmation =
        confirm(
            "Mark this component as returned?"
        );


    if (!confirmation) {

        return;

    }


    const response =
        await fetch(
            `/api/records/${id}/return`,
            {

                method: "PUT"

            }
        );


    const result =
        await response.json();


    if (!result.success) {

        alert(result.message);

    }

}


// ============================================================
// CURRENTLY OUT TABLE
// ============================================================

function renderOutTable() {

    const table =
        document.getElementById(
            "outTable"
        );


    const search =
        document.getElementById(
            "searchOut"
        ).value.toLowerCase();


    const outRecords =
        records.filter(record => {

            if (
                record.status !== "OUT"
            ) {

                return false;

            }


            return (

                record.component_id
                    .toLowerCase()
                    .includes(search)

                ||

                record.component_name
                    .toLowerCase()
                    .includes(search)

                ||

                record.employee_name
                    .toLowerCase()
                    .includes(search)

                ||

                record.designation
                    .toLowerCase()
                    .includes(search)

            );

        });


    document.getElementById(
        "outCount"
    ).textContent =
        outRecords.length;


    table.innerHTML = "";


    outRecords.forEach(record => {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                ${escapeHtml(
                    record.component_id
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.component_name
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.employee_name
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.designation
                )}
            </td>

            <td>
                ${record.out_time}
            </td>

            <td>
                ${escapeHtml(
                    record.recorded_by
                )}
            </td>

            <td>

                <button
                    class="return-btn"
                    onclick="returnComponent(${record.id})"
                >
                    Mark Returned
                </button>

            </td>

        `;


        table.appendChild(row);

    });

}


// ============================================================
// HISTORY TABLE
// ============================================================

function renderHistory() {

    const table =
        document.getElementById(
            "historyTable"
        );


    const search =
        document.getElementById(
            "searchHistory"
        ).value.toLowerCase();


    const filteredRecords =
        records.filter(record => {

            return (

                record.component_id
                    .toLowerCase()
                    .includes(search)

                ||

                record.component_name
                    .toLowerCase()
                    .includes(search)

                ||

                record.employee_name
                    .toLowerCase()
                    .includes(search)

                ||

                record.designation
                    .toLowerCase()
                    .includes(search)

                ||

                record.recorded_by
                    .toLowerCase()
                    .includes(search)

            );

        });


    table.innerHTML = "";


    filteredRecords.forEach(record => {

        const row =
            document.createElement("tr");


        const statusClass =
            record.status === "OUT"
                ? "status-out"
                : "status-returned";


        row.innerHTML = `

            <td>
                ${escapeHtml(
                    record.component_id
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.component_name
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.employee_name
                )}
            </td>

            <td>
                ${escapeHtml(
                    record.designation
                )}
            </td>

            <td>
                ${record.out_time}
            </td>

            <td>
                ${record.returned_time || "-"}
            </td>

            <td>
                ${escapeHtml(
                    record.recorded_by
                )}
            </td>

            <td class="${statusClass}">
                ${record.status}
            </td>

        `;


        table.appendChild(row);

    });

}


// ============================================================
// RENDER EVERYTHING
// ============================================================

function renderTables() {

    renderOutTable();

    renderHistory();

}


// ============================================================
// STATISTICS
// ============================================================

function updateStatistics() {

    const total =
        components.length;


    const out =
        components.filter(
            component =>
                component.status === "OUT"
        ).length;


    const available =
        total - out;


    document.getElementById(
        "totalComponents"
    ).textContent = total;


    document.getElementById(
        "currentlyOut"
    ).textContent = out;


    document.getElementById(
        "availableComponents"
    ).textContent = available;

}


// ============================================================
// LIVE SOCKET UPDATES
// ============================================================

socket.on(
    "record_added",
    function(record) {

        records.unshift(record);

        loadComponents();

        renderTables();

        updateStatistics();

    }
);


socket.on(
    "record_returned",
    function(record) {

        const index =
            records.findIndex(
                r => r.id === record.id
            );


        if (index !== -1) {

            records[index] = record;

        }


        loadComponents();

        renderTables();

        updateStatistics();

    }
);


socket.on(
    "components_changed",
    function() {

        loadComponents();

    }
);


socket.on(
    "employees_changed",
    function() {

        loadEmployees();

    }
);


// ============================================================
// SEARCH
// ============================================================

document
    .getElementById("searchOut")
    .addEventListener(
        "input",
        renderOutTable
    );


document
    .getElementById("searchHistory")
    .addEventListener(
        "input",
        renderHistory
    );


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent = value;

    return div.innerHTML;

}


// ============================================================
// START
// ============================================================

loadData();