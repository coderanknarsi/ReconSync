from flask import Flask, render_template, request, redirect, url_for, flash

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
    },
}

CUSTOMER_DATA = {
    "john doe": {
        "vin": "ABC123",
        "year": 2020,
        "make": "Toyota",
        "model": "Camry",
        "customer": "John Doe",
    },
}

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
        }

    return render_template("repair_order.html", vehicle=vehicle, ticket_number=ticket_number)


if __name__ == "__main__":
    app.run(debug=True)
