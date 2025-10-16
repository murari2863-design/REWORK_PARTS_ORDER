from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret-key-for-flash'

# CSV file paths
REWORK_CSV = 'rework_requests.csv'

# Ensure CSV file exists with header
if not os.path.exists(REWORK_CSV):
    with open(REWORK_CSV, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'van_id', 'part_name', 'requested_by', 'state', 'paint_stock', 'logistics_status', 'paint_approval', 'created_at', 'updated_at'])

def read_rework_requests():
    with open(REWORK_CSV, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_rework_requests(rows):
    with open(REWORK_CSV, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def generate_new_id():
    requests = read_rework_requests()
    if not requests:
        return '1'
    max_id = max(int(r['id']) for r in requests)
    return str(max_id + 1)

@app.route('/')
def home():
    return redirect(url_for('list_requests'))

# Lead creates a rework request
@app.route('/create', methods=['GET', 'POST'])
def create_request():
    if request.method == 'POST':
        van_id = request.form['van_id']
        part_name = request.form['part_name']
        requested_by = request.form['requested_by']
        new_id = generate_new_id()
        now = datetime.now().isoformat(timespec='seconds')
        new_request = {
            'id': new_id,
            'van_id': van_id,
            'part_name': part_name,
            'requested_by': requested_by,
            'state': 'New',
            'paint_stock': 'Unknown',
            'logistics_status': 'Pending',
            'paint_approval': 'Pending',
            'created_at': now,
            'updated_at': now,
        }
        rows = read_rework_requests()
        rows.append(new_request)
        write_rework_requests(rows)
        flash(f'Rework request {new_id} created!', 'success')
        return redirect(url_for('list_requests'))
    return render_template('create_request.html')

# View all requests (for Logistics, Paint, Lead)
@app.route('/requests')
def list_requests():
    requests = read_rework_requests()
    return render_template('list_requests.html', requests=requests)

# Paint marks availability and approval
@app.route('/paint/<request_id>', methods=['GET', 'POST'])
def paint_update(request_id):
    requests = read_rework_requests()
    req = next((r for r in requests if r['id'] == request_id), None)
    if not req:
        flash('Request not found.', 'error')
        return redirect(url_for('list_requests'))
    if request.method == 'POST':
        paint_stock = request.form.get('paint_stock', 'No')
        paint_approval = request.form.get('paint_approval', 'Pending')
        req['paint_stock'] = paint_stock
        if paint_stock == 'Yes':
            req['state'] = 'PaintStockAllocated'
        else:
            if paint_approval == 'Approved':
                req['state'] = 'InPaint'
            else:
                req['state'] = 'OnHold'
        req['paint_approval'] = paint_approval
        req['updated_at'] = datetime.now().isoformat(timespec='seconds')
        write_rework_requests(requests)
        flash(f'Request {request_id} updated by Paint.', 'success')
        return redirect(url_for('list_requests'))
    return render_template('paint_update.html', req=req)

# Logistics updates pickup/delivery
@app.route('/logistics/<request_id>', methods=['GET', 'POST'])
def logistics_update(request_id):
    requests = read_rework_requests()
    req = next((r for r in requests if r['id'] == request_id), None)
    if not req:
        flash('Request not found.', 'error')
        return redirect(url_for('list_requests'))
    if request.method == 'POST':
        status = request.form.get('logistics_status', req['logistics_status'])
        if status == 'Delivered':
            req['state'] = 'Delivered'
        req['logistics_status'] = status
        req['updated_at'] = datetime.now().isoformat(timespec='seconds')
        write_rework_requests(requests)
        flash(f'Request {request_id} updated by Logistics.', 'success')
        return redirect(url_for('list_requests'))
    return render_template('logistics_update.html', req=req)

if __name__ == '__main__':
    app.run(debug=True)
