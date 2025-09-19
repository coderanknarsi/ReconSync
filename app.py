from flask import Flask, render_template, request, redirect, url_for, flash
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# Fake data for demonstration purposes
VEHICLE_DATA = {
    "123": {
        "vin": "123",
        "year": 2018,
        "make": "Ford",
        "model": "F-150",
        "customer": "Jane Smith",
        "phone": "(555) 123-4567",
        "email": "jane.smith@email.com",
    },
}

CUSTOMER_DATA = {
    "john doe": {
        "vin": "ABC123",
        "year": 2020,
        "make": "Toyota",
        "model": "Camry",
        "customer": "John Doe",
        "phone": "(555) 987-6543",
        "email": "john.doe@email.com",
    },
}

# Store repair orders in memory (in production, use a database)
REPAIR_ORDERS = {}

_ticket_counter = 0


def get_next_ticket_number() -> int:
    global _ticket_counter
    _ticket_counter += 1
    return _ticket_counter


@app.route("/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if not query:
            flash("Please enter a VIN or Customer Name to search.")
            return redirect(url_for("search"))

        vehicle = None

        # VIN lookup
        if query in VEHICLE_DATA:
            vehicle = VEHICLE_DATA[query]
        else:
            # Customer lookup (case-insensitive)
            vehicle = CUSTOMER_DATA.get(query.lower())

        if not vehicle:
            flash("No matching vehicle or customer found. Showing demo vehicle.")
            vehicle = {
                "vin": "DEMO123",
                "year": 2022,
                "make": "Demo",
                "model": "Vehicle",
                "customer": "Demo Customer",
                "phone": "(555) 000-0000",
                "email": "demo@example.com",
            }

        ticket_number = get_next_ticket_number()
        return redirect(url_for("new_repair_order", ticket=ticket_number, vin=vehicle["vin"]))

    return render_template("search.html")


@app.route("/repair-order")
def new_repair_order():
    vin = request.args.get("vin")
    ticket_number = request.args.get("ticket")
    vehicle = VEHICLE_DATA.get(vin)

    if not vehicle:
        # Attempt to find vehicle in customer data
        vehicle = next((data for data in CUSTOMER_DATA.values() if data["vin"] == vin), None)

    if not vehicle:
        vehicle = {
            "vin": vin or "Unknown",
            "year": "-",
            "make": "-",
            "model": "-",
            "customer": "Unknown",
            "phone": "-",
            "email": "-",
        }

    return render_template("repair_order.html", vehicle=vehicle, ticket_number=ticket_number)


@app.route("/save-repair-order", methods=["POST"])
def save_repair_order():
    try:
        data = request.get_json()
        ticket_number = data.get("ticket_number")
        
        # Create repair order record
        repair_order = {
            "ticket_number": ticket_number,
            "vin": data.get("vin"),
            "customer": data.get("customer"),
            "work_description": data.get("work_description"),
            "payer_type": data.get("payer_type"),
            "line_items": data.get("line_items", []),
            "subtotal": data.get("subtotal", 0),
            "tax": data.get("tax", 0),
            "total": data.get("total", 0),
            "created_at": datetime.now().isoformat(),
            "status": "Open"
        }
        
        REPAIR_ORDERS[ticket_number] = repair_order
        
        return {"success": True, "message": "Repair order saved successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}, 400
if __name__ == "__main__":
    app.run(debug=True)

@app.route("/repair-orders")
def list_repair_orders():
    return render_template("repair_orders_list.html", repair_orders=REPAIR_ORDERS)