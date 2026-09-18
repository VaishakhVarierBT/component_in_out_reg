const socket = io();


let records = [];

let components = [];

let employees = [];


// ============================================================
// SIDEBAR NAVIGATION
// ============================================================

function showSection(sectionId, clickedButton) {

    const sections =
        document.querySelectorAll(".page-section");


    sections.forEach(function(section) {

        section.style.display = "none";

    });


    const selectedSection =
        document.getElementById(sectionId);


    if (selectedSection) {

        selectedSection.style.display = "block";

    }


    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach(function(item) {

        item.classList.remove("active");

    });


    if (clickedButton) {

        clickedButton.classList.add("active");

    }

}


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
            `${component.component_name} [Available: ${component.available_quantity}]`;


        if (component.available_quantity <= 0) {

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


    // --------------------------------------------------------
    // OTHER OPTION
    // --------------------------------------------------------

    const otherOption =
        document.createElement("option");


    otherOption.value = "other";

    otherOption.textContent = "Other";


    select.appendChild(otherOption);

}


// ============================================================
// OTHER EMPLOYEE
// ============================================================

document
    .getElementById("employeeSelect")
    .addEventListener(
        "change",
        function() {

            const otherFields =
                document.getElementById(
                    "otherEmployeeFields"
                );


            const nameInput =
                document.getElementById(
                    "otherEmployeeName"
                );


            const designationInput =
                document.getElementById(
                    "otherDesignation"
                );


            if (this.value === "other") {

                otherFields.style.display =
                    "block";

                nameInput.required = true;

                designationInput.required = true;

            }

            else {

                otherFields.style.display =
                    "none";

                nameInput.required = false;

                designationInput.required = false;

                nameInput.value = "";

                designationInput.value = "";

            }

        }
    );


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


            const quantity =
                document.getElementById(
                    "quantitySelect"
                ).value;


            const employee =
                document.getElementById(
                    "employeeSelect"
                ).value;


            const otherEmployeeName =
                document.getElementById(
                    "otherEmployeeName"
                ).value.trim();


            const otherDesignation =
                document.getElementById(
                    "otherDesignation"
                ).value.trim();


            if (!component || !employee) {

                alert(
                    "Please select a component and employee."
                );

                return;

            }


            if (!quantity || Number(quantity) <= 0) {

                alert(
                    "Please enter a valid quantity."
                );

                return;

            }


            if (
                employee === "other"
                &&
                (
                    !otherEmployeeName
                    ||
                    !otherDesignation
                )
            ) {

                alert(
                    "Please enter the employee name and designation."
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

                                quantity:
                                    Number(quantity),

                                employee_id:
                                    employee,

                                other_employee_name:
                                    otherEmployeeName,

                                other_designation:
                                    otherDesignation

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


            document
                .getElementById(
                    "otherEmployeeFields"
                )
                .style.display = "none";


            document
                .getElementById(
                    "otherEmployeeName"
                )
                .required = false;


            document
                .getElementById(
                    "otherDesignation"
                )
                .required = false;

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


            const componentName =
                document.getElementById(
                    "newComponentName"
                ).value.trim();


            const quantity =
                document.getElementById(
                    "newComponentQuantity"
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

                                component_name:
                                    componentName,

                                quantity:
                                    Number(quantity)

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

    const record =
        records.find(
            r => r.id === id
        );


    if (!record) {

        return;

    }


    const remaining =
        Number(record.quantity_out)
        -
        Number(record.quantity_returned);


    const quantity =
        prompt(
            `How many units are being returned?\n\nRemaining OUT: ${remaining}`,
            remaining
        );


    if (quantity === null) {

        return;

    }


    const returnQuantity =
        Number(quantity);


    if (
        !Number.isInteger(returnQuantity)
        ||
        returnQuantity <= 0
        ||
        returnQuantity > remaining
    ) {

        alert(
            `Please enter a quantity between 1 and ${remaining}.`
        );

        return;

    }


    const confirmation =
        confirm(
            `Return ${returnQuantity} unit(s)?`
        );


    if (!confirmation) {

        return;

    }


    const response =
        await fetch(
            `/api/records/${id}/return`,
            {

                method: "PUT",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body:
                    JSON.stringify({

                        quantity_returned:
                            returnQuantity

                    })

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
                &&
                record.status !== "PARTIALLY RETURNED"
            ) {

                return false;

            }


            return (

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


        const remaining =
            Number(record.quantity_out)
            -
            Number(record.quantity_returned);


        row.innerHTML = `

            <td>
                ${escapeHtml(
                    record.component_name
                )}
            </td>

            <td>
                ${record.quantity_out}
            </td>

            <td>
                ${record.quantity_returned}
            </td>

            <td>
                ${remaining}
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

                    Return

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

                ||

                record.status
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
            ||
            record.status === "PARTIALLY RETURNED"

                ? "status-out"

                : "status-returned";


        row.innerHTML = `

            <td>
                ${escapeHtml(
                    record.component_name
                )}
            </td>

            <td>
                ${record.quantity_out}
            </td>

            <td>
                ${record.quantity_returned}
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
        components.reduce(
            (sum, component) =>
                sum +
                Number(component.total_quantity),
            0
        );


    const available =
        components.reduce(
            (sum, component) =>
                sum +
                Number(component.available_quantity),
            0
        );


    const out =
        total - available;


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


    div.textContent =
        value;


    return div.innerHTML;

}


// ============================================================
// START
// ============================================================

loadData();