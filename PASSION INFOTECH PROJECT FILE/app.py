from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.secret_key = 'secret123'  # For flash messaging if needed

# In-memory storage
campaigns = []
approved_campaigns = []

def company_exists_online(company_name):
    try:
        search_url = f"https://www.zaubacorp.com/companysearchresults/{company_name.replace(' ', '%20')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return company_name.lower() in soup.text.lower()
    except Exception:
        return False

def is_legitimate(campaign):
    # Rule 1: Check amount
    try:
        amount = int(campaign['amount'])
    except ValueError:
        return False, "Amount must be a valid number"

    if amount > 100000:
        return False, "Requested amount too high"

    # Rule 2: Address check
    if not campaign['address'].strip():
        return False, "Invalid address"

    # Rule 3: Company check
    if not company_exists_online(campaign['company'].strip()):
        return False, "Company not found on ZaubaCorp"

    return True, "Legitimate"

@app.route('/')
def index():
    return render_template('index.html', campaigns=campaigns)

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        'title': request.form.get('title', '').strip(),
        'description': request.form.get('description', '').strip(),
        'amount': request.form.get('amount', '').strip(),
        'address': request.form.get('address', '').strip(),
        'company': request.form.get('company', '').strip(),
    }

    # Check for empty fields
    if not all(data.values()):
        data['status'] = 'Rejected'
        data['reason'] = 'Please fill in all fields'
    else:
        # Optional: Keep reason from legitimacy check but allow admin decision
        _, reason = is_legitimate(data)
        data['status'] = 'Pending'
        data['reason'] = reason

    campaigns.append(data)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    return render_template('admin.html', campaigns=campaigns)

@app.route('/approve/<int:id>', methods=['POST'])
def approve(id):
    if 0 <= id < len(campaigns):
        reason = request.form.get('reason', 'Approved by admin')
        campaigns[id]['status'] = 'Approved'
        campaigns[id]['reason'] = reason
        approved_campaigns.append(campaigns[id])
    return redirect(url_for('admin'))

@app.route('/reject/<int:id>', methods=['POST'])
def reject(id):
    if 0 <= id < len(campaigns):
        reason = request.form.get('reason', 'Rejected by admin')
        campaigns[id]['status'] = 'Rejected'
        campaigns[id]['reason'] = reason
    return redirect(url_for('admin'))

@app.route('/bulk-approve', methods=['POST'])
def bulk_approve():
    selected = request.form.getlist('selected[]')
    reason = request.form.get('reason', 'Approved in bulk')

    for idx in selected:
        try:
            i = int(idx)
            if 0 <= i < len(campaigns) and campaigns[i]['status'] == 'Pending':
                campaigns[i]['status'] = 'Approved'
                campaigns[i]['reason'] = reason
                approved_campaigns.append(campaigns[i])
        except:
            continue

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
