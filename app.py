from flask import Flask, render_template, request, redirect, url_for
import csv, os
from datetime import datetime

app = Flask(__name__)

REQUESTS_FILE = "rework_requests.csv"


# === Initialize CSV if missing ===
def init_csv():
    if not os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "RequestID", "PartName", "RequestedBy", "Status",
                "CurrentOwner", "CreatedAt", "UpdatedAt"
            ])


def read_requests():
    if not os.path.exists(REQUESTS_FILE):
        return []
    with open(REQUESTS_FILE, newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_requests(rows):
    with open(REQUESTS_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def generate_id():
    rows = read_requests()
    return len(rows) + 1


@app.route("/")
def home():
    rows = read_requests()
    return render_template("index.html", requests=rows)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        init_csv()
        part_name = request.form["part_name"]
        requested_by = request.form["requested_by"]
        req_id = generate_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(REQUESTS_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([req_id, part_name, requested_by, "New", "Logistics", now, now])
        return redirect(url_for("home"))
    return render_template("create.html")


@app.route("/update/<req_id>", methods=["GET", "POST"])
def update(req_id):
    rows = read_requests()
    selected = None
    for r in rows:
        if r["RequestID"] == req_id:
            selected = r
            break

    if request.method == "POST":
        new_status = request.form["status"]
        new_owner = request.form["owner"]

        # Handle Paint shop “part in stock” condition
        if new_status == "BuildDone" and new_owner == "Paint":
            part_in_stock = request.form.get("part_in_stock") == "yes"
            if part_in_stock:
                new_status = "ReadyForPickup"
                new_owner = "Logistics"

        for row in rows:
            if row["RequestID"] == req_id:
                row["Status"] = new_status
                row["CurrentOwner"] = new_owner
                row["UpdatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_requests(rows)
        return redirect(url_for("home"))

    return render_template("update.html", request_data=selected)


if __name__ == "__main__":
    init_csv()
    app.run(debug=True)
