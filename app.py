
#CheckPoint 1(Booking not being appended)


from flask import Flask, render_template, request, \
    redirect, url_for, session, send_file, flash
import pandas as pd
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
import io
import os
import math
from functools import wraps
from datetime import datetime, timedelta



#NEWWWWWWWWWWWWWWWWWW CODEEEEEE STARTTTTTTT(CALENDER FUNCTIONALITY)
import csv

BOOKINGS_FILE = 'bookings.csv'
data = pd.read_csv(BOOKINGS_FILE)

def load_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return pd.DataFrame(columns=[
            'audit_number', 'audit_title', 'PSID', 'FullName', 'Role', 'Phase', 'BookedFrom', 'BookedTo', 'Timestamp'
        ])
    return pd.read_csv(BOOKINGS_FILE, parse_dates=['BookedFrom', 'BookedTo'])

def check_date_clash(psid, start_date, end_date):
    bookings = load_bookings()
    emp_bookings = bookings[bookings['PSID'] == psid]
    for _, row in emp_bookings.iterrows():
        booked_start = pd.to_datetime(row['BookedFrom'])
        booked_end = pd.to_datetime(row['BookedTo'])
        if not (end_date < booked_start or start_date > booked_end):
            return False, row['audit_number'], booked_start, booked_end
    return True, None, None, None

def save_booking(row):
    file_exists = os.path.exists(BOOKINGS_FILE)
    with open(BOOKINGS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def get_booked_ranges(psid):
    bookings = load_bookings()
    emp_bookings = bookings[bookings['PSID'] == psid]
    return [(row['BookedFrom'], row['BookedTo']) for _, row in emp_bookings.iterrows()]

def is_range_available(psid, start_date, end_date):
    booked_ranges = get_booked_ranges(psid)
    for booked_start, booked_end in booked_ranges:
        if not (end_date < pd.to_datetime(booked_start) or start_date > pd.to_datetime(booked_end)):
            return False, None, booked_start, booked_end
    return True, None, None, None

def percent_free(psid, availability_from, availability_to):
    total_days = (availability_to - availability_from).days + 1
    booked_ranges = get_booked_ranges(psid)
    booked_days = 0
    for booked_start, booked_end in booked_ranges:
        overlap_start = max(availability_from, pd.to_datetime(booked_start))
        overlap_end = min(availability_to, pd.to_datetime(booked_end))
        if overlap_start <= overlap_end:
            booked_days += (overlap_end - overlap_start).days + 1
    free_days = total_days - booked_days
    return round((free_days / total_days) * 100, 2) if total_days > 0 else 0
# ...existing code...
#NEW CODE ENDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a secure key

# Load the CSV data
data = pd.read_csv('output.csv')
#print(data.columns.tolist())
# Get the list of unique audits with their details


audits_df = data[['audit_number', 'audit_title', 'audit_offering', 'audit_offering_sub_type', 'audit_origin', 'critical_audit_tagging_tag', 'audit_plan_year', 'audit_year_quarter', 'country_coverage', 'region_coverage', 'audit_principal_risk_types', 'audit_risk_radar_themes', 
                  'audit_group', 'primary_mca_business_function', 'secondary_mca_business_function', 'primary_sub_function_impacted', 'secondary_sub_function_impacted', 'primary_gia_audit_owner', 'secondary_gia_audit_owner', 'primary_gia_audit_owner_team', 'secondary_gia_audit_owner_team', 'guest_auditors', 
                  'planned_audit_notification_date', 'planned_planning_start_date', 'planned_planning_end_date', 'planned_fieldwork_start_date', 'planned_fieldwork_end_date', 'planned_reporting_start_date', 'planned_report_issuance_date', 'AuditDays', 'SchedulingPhase', 'PSID', 'FullName', 'JobTitle', 
                  'CountryName', 'LocationCity', 'AuditTeamName', 'RecommendedRole', 'Utilisation', 'AvailabilityFrom', 'AvailabilityTo', 'AvailableDateRanges', 'UnavailableDateRanges_DueTo_Leaves', 'UnavailableDateRanges_DueTo_BookedAudit', 'Already_Booked_AuditNumberAndRole', 
                  'AuditPhaseAvailability', 'PriorityScore', 'SuggestionLabel', 'WeightedSimilarityScore', 'NormalizedTeamSimilarityScore', 'NormalizedSkillSimilarityScore', 'TeamMatched', 'TopSkillsMatched', 'report_output_date']].drop_duplicates()

audits = audits_df.to_dict('records')

# Initialize utilization for employees, converting BankID to int
utilization = {int(emp_id): 0 for emp_id in data['PSID'].unique()}

# User credentials (for demonstration purposes)
users = {
    'admin': generate_password_hash('admin123'),
    # Add more users as needed
}
def calculate_business_days(start_date, end_date):
    date_range = np.arange(start_date, end_date + timedelta(days=1), dtype='datetime64[D]')
    business_days = np.is_busday(date_range)
    return np.sum(business_days)

@app.template_filter('datetime')
def datetime_filter(value, format='%Y-%m-%d'):
    return datetime.strptime(value, format)

app.jinja_env.filters['datetime'] = datetime_filter

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error = "Username and password are required."
        else:
            user_password_hash = users.get(username)
            if user_password_hash and check_password_hash(user_password_hash, password):
                session['username'] = username
                next_page = request.args.get('next')
                return redirect(next_page or url_for('select_audit'))
            else:
                error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('select_audit'))

@app.route('/select_audit')
@login_required
def select_audit():
    audit_number = request.args.get('audit_number')
    if audit_number:
        return redirect(url_for('view_resources', audit_number=str(audit_number)))
    else:
        if audits:
            first_audit_number = audits[0]['audit_number']
            return redirect(url_for('view_resources', audit_number=str(first_audit_number)))
        else:
            flash('No audits available.', 'warning')
            return redirect(url_for('index'))


''''''

#inlcude me
@app.route('/view_resources/<audit_number>', methods=['GET', 'POST'])
@login_required
def view_resources(audit_number):
    # 1) Prepare all data FIRST (so POST can use it)
    project_data = data[data['audit_number'] == str(audit_number)]
    if project_data.empty:
        flash("No data found for the selected audit.", "warning")
        return redirect(url_for('select_audit'))

    audit_title = project_data['audit_title'].iloc[0]

    # Deduplicate audits for sidebar
    audits_deduped = list({a['audit_number']: a for a in audits}.values())

    # Build filtered_employees consistently (with booked ranges & percent free)
    employees = project_data.to_dict('records')
    selected_emp_ids = {
        s['PSID'] for s in session.get('selections', [])
        if s['audit_number'] == str(audit_number)
    }

    filtered_employees = []
    for emp in employees:
        emp_id = int(emp['PSID'])
        emp_util = utilization.get(emp_id, 0)
        emp['Utilization'] = emp_util
        emp['Utilization Percent'] = f"{(emp_util / 250) * 100:.2f}%"

        # Parse availability safely (strings like 'YYYY-mm-dd HH:MM:SS+ZZ:ZZ')
        start = pd.to_datetime(emp['AvailabilityFrom']).date()
        end = pd.to_datetime(emp['AvailabilityTo']).date()

        # Business days using pandas (reliable with date objects)
        emp['available_days'] = len(pd.bdate_range(start, end))

        # Precompute calendar info used by template
        ranges = get_booked_ranges(emp_id)
        emp['BookedRanges'] = [(pd.to_datetime(s).date(), pd.to_datetime(e).date()) for s, e in ranges]
        try:
            emp['PercentFree'] = percent_free(emp_id, pd.to_datetime(emp['AvailabilityFrom']),
                                             pd.to_datetime(emp['AvailabilityTo']))
        except Exception:
            emp['PercentFree'] = 100.0

        if emp_util < 210:
            emp['selected'] = emp_id in selected_emp_ids
            filtered_employees.append(emp)

    filtered_employees.sort(key=lambda x: x.get('WeightedSimilarityScore', 0), reverse=True)

    # 2) Handle POST now that everything exists
    if request.method == 'POST':
        selected_employees = request.form.getlist('selected_employees')

        # If nothing selected, give feedback
        if not selected_employees:
            flash("Please select at least one employee.", "warning")
            return redirect(url_for('view_resources', audit_number=str(audit_number)))

        roles = {emp_id: request.form.get(f'role_{emp_id}') for emp_id in selected_employees}
        phases = {emp_id: request.form.get(f'phase_{emp_id}') for emp_id in selected_employees}

        # Use ONE session key consistently
        if 'selections' not in session:
            session['selections'] = []

        any_saved = False
        for emp_id in selected_employees:
            emp_id_int = int(emp_id)
            role = roles.get(emp_id) or ""
            phase = phases.get(emp_id) or ""
            booked_from = request.form.get(f'booked_from_{emp_id}')
            booked_to = request.form.get(f'booked_to_{emp_id}')

            # Only try to book if dates are present
            if booked_from and booked_to:
                ok, clash_audit, _, _ = is_range_available(emp_id_int,
                                                           pd.to_datetime(booked_from),
                                                           pd.to_datetime(booked_to))
                if not ok:
                    flash(f"Employee {emp_id} has a date clash. Please pick different dates.", "danger")
                    continue

                # Persist booking to CSV
                saved = add_booking(
                    audit_number=str(audit_number),
                    psid=emp_id_int,
                    full_name=next((e['FullName'] for e in filtered_employees if int(e['PSID']) == emp_id_int), ""),
                    role=role,
                    phase=phase,
                    booked_from=pd.to_datetime(booked_from),
                    booked_to=pd.to_datetime(booked_to)
                )
                any_saved = any_saved or saved

            # Update session selections (used to grey out rows)
            session['selections'].append({
                'audit_number': str(audit_number),
                'audit_title': str(audit_title),
                'PSID': emp_id_int,
                'RecommendedRole': str(role),
                'SelectedPhase': str(phase),
            })

        session.modified = True
        if any_saved:
            flash("Booking added successfully!", "success")
        return redirect(url_for('view_resources', audit_number=str(audit_number)))

    # 3) Pagination (unchanged behavior)
    page = request.args.get('page', 1, type=int)
    per_page = 6
    total_pages = (len(filtered_employees) + per_page - 1) // per_page
    start = (page - 1) * per_page
    paginated_employees = filtered_employees[start:start + per_page]

    return render_template(
        'view_resources.html',
        audits=audits_deduped,
        audit_number=audit_number,
        audit_title=audit_title,
        employees=paginated_employees,
        page=page,
        total_pages=total_pages
    )


'''
@app.route('/view_resources/<audit_number>', methods=['GET', 'POST'])
@login_required
def view_resources(audit_number):

      if request.method == 'POST':
        selected_employees = request.form.getlist('selected_employees')
        roles = {emp_id: request.form.get(f'role_{emp_id}') for emp_id in selected_employees}
        phases = {emp_id: request.form.get(f'phase_{emp_id}') for emp_id in selected_employees}

      if 'selections' not in session:
            session['selections'] = []

    #4 added lines of code below
    unique_audits = {}

    for audit in audits:
        unique_audits[audit['audit_number']] = audit
        audits_deduped = list(unique_audits.values())


    # prev code below
    page = request.args.get('page', 1, type=int)
    per_page = 6

    project_data = data[data['audit_number'] == str(audit_number)]
    if project_data.empty:
        return "No data found for the selected audit."

    audit_title = project_data['audit_title'].iloc[0]
    employees = project_data.to_dict('records')

    selected_emp_ids = set(
        selection['PSID']
        for selection in session.get('selections', [])
        if selection['audit_number'] == str(audit_number)
    )

    filtered_employees = []
    for emp in employees:
        emp_id = int(emp['PSID'])
        emp_utilization = utilization.get(emp_id, 0)
        emp['Utilization'] = emp_utilization
        emp['Utilization Percent'] = f"{(emp_utilization / 250) * 100:.2f}%"
        
        availability_from_date = datetime.strptime(emp['AvailabilityFrom'], '%Y-%m-%d %H:%M:%S%z')
        availability_to_date = datetime.strptime(emp['AvailabilityTo'], '%Y-%m-%d %H:%M:%S%z')
        emp['available_days'] = calculate_business_days(availability_from_date, availability_to_date)

        if emp_utilization < 210:
            emp['selected'] = emp_id in selected_emp_ids
            filtered_employees.append(emp)

    filtered_employees.sort(key=lambda x: x.get('WeightedSimilarityScore', 0), reverse=True)

    total_employees = len(filtered_employees)
    total_pages = math.ceil(total_employees / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_employees = filtered_employees[start:end]

    if request.method == 'POST':
        selected_employees = request.form.getlist('selected_employees')
        roles = {emp_id: request.form.get(f'role_{emp_id}') for emp_id in selected_employees}
        phases = {emp_id: request.form.get(f'phase_{emp_id}') for emp_id in selected_employees}


        if 'selections' not in session:
            session['selections'] = []

        for emp_id in selected_employees:
            emp_id_int = int(emp_id)
            role = roles[emp_id]
            phase = phases[emp_id]
            available_days_str = request.form.get(f'available_days_{emp_id}')

            if available_days_str:
                try:
                    available_days = int(available_days_str)
                    utilization[emp_id_int] += available_days
                except ValueError as e:
                    print(f"Error parsing available days for employee ID {emp_id}: {e}")
            else:
                print(f"Available days are missing for employee ID {emp_id}")

            emp_data = next((emp for emp in filtered_employees if int(emp['PSID']) == emp_id_int), None)
            if emp_data:
                session['selections'].append({
                    'audit_number': str(audit_number),
                    'audit_title': str(audit_title),
                    'PSID': emp_id_int,
                    'RecommendedRole': str(role),
                    'SelectedPhase': str(phase),
                    'Utilization': int(utilization[emp_id_int])
                })

        session.modified = True
        return redirect(url_for('view_resources', audit_number=str(audit_number), page=page))

    return render_template(
        'view_resources.html',
        #audits=audits,
        #audit_number=str(audit_number),

        #new 2 lines of code below
        audits=audits_deduped,
        audit_number=audit_number,

        #old code below
        audit_title=audit_title,
        employees=paginated_employees,
        page=page,
        total_pages=total_pages
    )

'''
@app.route('/download_all')
@login_required
def download_all():
    # Load bookings.csv
    try:
        bookings = load_bookings()
    except FileNotFoundError:
        flash("Bookings file not found.", 'danger')
        return redirect(url_for('select_audit'))

    if bookings.empty:
        flash("No bookings found.", 'warning')
        return redirect(url_for('select_audit'))

    # Create an in-memory CSV file
    output = io.StringIO()
    bookings.to_csv(output, index=False)
    output.seek(0)

    # Send the CSV file as a download
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='all_bookings.csv'
    )

'''





@app.route('/view_resources/<audit_number>', methods=['GET', 'POST'])
@login_required
def view_resources(audit_number):
    filtered_employees = []

    if request.method == 'POST':
        # Get selected employees and their roles/phases
        selected_employees = request.form.getlist('selected_employees')
        roles = {emp_id: request.form.get(f'role_{emp_id}') for emp_id in selected_employees}
        phases = {emp_id: request.form.get(f'phase_{emp_id}') for emp_id in selected_employees}

        # Initialize session selections if not already present
        if 'selections' not in session:
            session['selections'] = []

        for emp_id in selected_employees:
            emp_id_int = int(emp_id)
            role = roles[emp_id]
            phase = phases[emp_id]
            booked_from = request.form.get(f'booked_from_{emp_id}')
            booked_to = request.form.get(f'booked_to_{emp_id}')

            # Check if booking dates are provided
            if booked_from and booked_to:
                booked_from_date = pd.to_datetime(booked_from)
                booked_to_date = pd.to_datetime(booked_to)

                # Call add_booking to save the booking
                is_successful = add_booking(
                    audit_number=audit_number,
                    psid=emp_id_int,
                    full_name=request.form.get(f'full_name_{emp_id}'),
                    role=role,
                    phase=phase,
                    booked_from=booked_from_date,
                    booked_to=booked_to_date
                )

                # If booking failed due to date clash, skip adding to session
                if not is_successful:
                    continue

            # Add employee data to session selections
            emp_data = next((emp for emp in filtered_employees if int(emp['PSID']) == emp_id_int), None)
            if emp_data:
                session['selections'].append({
                    'audit_number': str(audit_number),
                    'audit_title': str(audit_title),
                    'PSID': emp_id_int,
                    'RecommendedRole': str(role),
                    'SelectedPhase': str(phase),
                    'Utilization': int(utilization[emp_id_int])
                })

        # Mark session as modified and redirect back to the same page
        session.modified = True
        return redirect(url_for('view_resources', audit_number=str(audit_number)))

    # Deduplicate audits
    unique_audits = {}
    for audit in audits:
        unique_audits[audit['audit_number']] = audit
    audits_deduped = list(unique_audits.values())

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 6

    # Filter data for the selected audit
    project_data = data[data['audit_number'] == str(audit_number)]
    if project_data.empty:
        return "No data found for the selected audit."

    audit_title = project_data['audit_title'].iloc[0]
    employees = project_data.to_dict('records')

    # Get selected employee IDs from session
    selected_emp_ids = set(
        selection['PSID']
        for selection in session.get('selections', [])
        if selection['audit_number'] == str(audit_number)
    )

    # Filter employees based on utilization and availability
    filtered_employees = []
    for emp in employees:
        emp_id = int(emp['PSID'])
        emp_utilization = utilization.get(emp_id, 0)
        emp['Utilization'] = emp_utilization
        emp['Utilization Percent'] = f"{(emp_utilization / 250) * 100:.2f}%"

        availability_from_date = datetime.strptime(emp['AvailabilityFrom'], '%Y-%m-%d %H:%M:%S%z')
        availability_to_date = datetime.strptime(emp['AvailabilityTo'], '%Y-%m-%d %H:%M:%S%z')
        emp['available_days'] = calculate_business_days(availability_from_date, availability_to_date)

        if emp_utilization < 210:
            emp['selected'] = emp_id in selected_emp_ids
            filtered_employees.append(emp)

    # Sort employees by WeightedSimilarityScore
    filtered_employees.sort(key=lambda x: x.get('WeightedSimilarityScore', 0), reverse=True)

    # Paginate employees
    total_employees = len(filtered_employees)
    total_pages = math.ceil(total_employees / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_employees = filtered_employees[start:end]

    # Render the template with the required data
    return render_template(
        'view_resources.html',
        audits=audits_deduped,
        audit_number=audit_number,
        audit_title=audit_title,
        employees=paginated_employees,
        page=page,
        total_pages=total_pages
    )
'''

'''
@app.route('/view_resources/<audit_number>', methods=['GET', 'POST'])
@login_required
def view_resources(audit_number):
    if request.method == 'POST':
        selected_employees = request.form.getlist('selected_employees')
        roles = {emp_id: request.form.get(f'role_{emp_id}') for emp_id in selected_employees}
        phases = {emp_id: request.form.get(f'phase_{emp_id}') for emp_id in selected_employees}

        if 'selections' not in session:
            session['selections'] = []

        for emp_id in selected_employees:
            emp_id_int = int(emp_id)
            role = roles[emp_id]
            phase = phases[emp_id]
            booked_from = request.form.get(f'booked_from_{emp_id}')
            booked_to = request.form.get(f'booked_to_{emp_id}')

            # Check if booking dates are provided
            if booked_from and booked_to:
                booked_from_date = pd.to_datetime(booked_from)
                booked_to_date = pd.to_datetime(booked_to)

                # Call add_booking to save the booking
                add_booking(
                    audit_number=audit_number,
                    psid=emp_id_int,
                    full_name=request.form.get(f'full_name_{emp_id}'),
                    role=role,
                    phase=phase,
                    booked_from=booked_from_date,
                    booked_to=booked_to_date
                )

            emp_data = next((emp for emp in filtered_employees if int(emp['PSID']) == emp_id_int), None)
            if emp_data:
                session['selections'].append({
                    'audit_number': str(audit_number),
                    'audit_title': str(audit_title),
                    'PSID': emp_id_int,
                    'RecommendedRole': str(role),
                    'SelectedPhase': str(phase),
                    'Utilization': int(utilization[emp_id_int])
                })

        session.modified = True
        return redirect(url_for('view_resources', audit_number=str(audit_number)))

    # Deduplicate audits
    unique_audits = {}
    for audit in audits:
        unique_audits[audit['audit_number']] = audit
    audits_deduped = list(unique_audits.values())

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 6

    project_data = data[data['audit_number'] == str(audit_number)]
    if project_data.empty:
        return "No data found for the selected audit."

    audit_title = project_data['audit_title'].iloc[0]
    employees = project_data.to_dict('records')

    selected_emp_ids = set(
        selection['PSID']
        for selection in session.get('selections', [])
        if selection['audit_number'] == str(audit_number)
    )

    filtered_employees = []
    for emp in employees:
        emp_id = int(emp['PSID'])
        emp_utilization = utilization.get(emp_id, 0)
        emp['Utilization'] = emp_utilization
        emp['Utilization Percent'] = f"{(emp_utilization / 250) * 100:.2f}%"

        availability_from_date = datetime.strptime(emp['AvailabilityFrom'], '%Y-%m-%d %H:%M:%S%z')
        availability_to_date = datetime.strptime(emp['AvailabilityTo'], '%Y-%m-%d %H:%M:%S%z')
        emp['available_days'] = calculate_business_days(availability_from_date, availability_to_date)

        if emp_utilization < 210:
            emp['selected'] = emp_id in selected_emp_ids
            filtered_employees.append(emp)

    filtered_employees.sort(key=lambda x: x.get('WeightedSimilarityScore', 0), reverse=True)

    total_employees = len(filtered_employees)
    total_pages = math.ceil(total_employees / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_employees = filtered_employees[start:end]

    return render_template(
        'view_resources.html',
        audits=audits_deduped,
        audit_number=audit_number,
        audit_title=audit_title,
        employees=paginated_employees,
        page=page,
        total_pages=total_pages
    )
'''

   


from werkzeug.exceptions import BadRequestKeyError

@app.route('/delete_booking', methods=['POST'])
def delete_booking():

    try:
        audit_number = request.form['audit_number']
        psid = int(request.form['psid'])

    except BadRequestKeyError as e:
        flash(f"Missing form data: {e}", 'danger')
        return redirect(url_for('view_resources', audit_number=request.form.get('audit_number', '')))

    # Remove from session
    if 'selections' in session:
        session['selections'] = [
            emp for emp in session['selections']
            if not (emp['audit_number'] == str(audit_number) and int(emp['PSID']) == psid)
        ]

    # Remove from bookings.csv
    existing_bookings = load_bookings()
    updated_bookings = existing_bookings[
        ~((existing_bookings['audit_number'] == audit_number) & (existing_bookings['PSID'] == (psid)))
    ]
    updated_bookings.to_csv(BOOKINGS_FILE, index=False)

    flash("Booking deleted successfully!", 'success')
    return redirect(url_for('view_resources', audit_number=audit_number))

def get_booked_periods(psid):
    bookings = load_bookings()
    emp_bookings = bookings[bookings['PSID'] == psid]
    return [(row['BookedFrom'], row['BookedTo']) for _, row in emp_bookings.iterrows()]

@app.route('/download/<audit_number>')
@login_required
def download_schedule(audit_number):
    # Load bookings.csv
    bookings = load_bookings()

    # Filter bookings for the selected audit
    audit_bookings = bookings[bookings['audit_number'] == audit_number]

    if audit_bookings.empty:
        flash(f"No bookings found for audit {audit_number}.", 'warning')
        return redirect(url_for('view_resources', audit_number=audit_number))

    # Create an in-memory CSV file
    output = io.StringIO()
    audit_bookings.to_csv(output, index=False)
    output.seek(0)

    # Send the CSV file as a download
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{audit_number}_bookings.csv'
    )


'''
def add_booking(audit_number, psid, full_name, role, phase, booked_from, booked_to):
    # Check for date clashes
    is_available, clash_audit, clash_start, clash_end = check_date_clash(psid, booked_from, booked_to)
    if not is_available:
        flash(f"Date clash detected with audit {clash_audit}: {clash_start} to {clash_end}. Please change the dates.", 'danger')
        return False

    # Add to session
    if 'scheduled_emp' not in session:
        session['scheduled_emp'] = []

    session['scheduled_emp'].append({
        'audit_number': audit_number,
        'psid': psid,
        'full_name': full_name,
        'role': role,
        'phase': phase,
        'booked_from': booked_from,
        'booked_to': booked_to,
        'timestamp': datetime.now().isoformat()
    })

    # Add to bookings.csv
    save_booking({
        'audit_number': audit_number,
        'audit_title': '',  # Add audit title if available
        'PSID': psid,
        'FullName': full_name,
        'Role': role,
        'Phase': phase,
        'BookedFrom': booked_from,
        'BookedTo': booked_to,
        'Timestamp': datetime.now().isoformat()
    })

    flash("Booking added successfully!", 'success')
    return True'''


BOOKING_FIELDS = [
    'audit_number', 'audit_title', 'PSID', 'FullName', 'Role', 'Phase',
    'BookedFrom', 'BookedTo', 'Timestamp'
]

def save_booking(row):
    file_exists = os.path.exists(BOOKINGS_FILE)
    with open(BOOKINGS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=BOOKING_FIELDS)
        if not file_exists:
            writer.writeheader()
        # Ensure all fields exist
        safe = {k: row.get(k, "") for k in BOOKING_FIELDS}
        writer.writerow(safe)

def add_booking(audit_number, psid, full_name, role, phase, booked_from, booked_to):
    # Clash check (reuse your existing)
    is_ok, clash_audit, clash_start, clash_end = check_date_clash(psid, booked_from, booked_to)
    if not is_ok:
        flash(f"Date clash with audit {clash_audit}: {clash_start.date()} to {clash_end.date()}", "danger")
        return False

    # Write to CSV only; session state handled in the route
    save_booking({
        'audit_number': str(audit_number),
        'audit_title': '',   # or pass audit_title if you want
        'PSID': int(psid),
        'FullName': full_name or "",
        'Role': role or "",
        'Phase': phase or "",
        'BookedFrom': pd.to_datetime(booked_from).date(),
        'BookedTo': pd.to_datetime(booked_to).date(),
        'Timestamp': datetime.now().isoformat()
    })
    return True



def check_date_clash(psid, start_date, end_date):
    bookings = load_bookings()
    emp_bookings = bookings[bookings['PSID'] == psid]
    for _, row in emp_bookings.iterrows():
        booked_start = pd.to_datetime(row['BookedFrom'])
        booked_end = pd.to_datetime(row['BookedTo'])
        if not (end_date < booked_start or start_date > booked_end):
            return False, row['audit_number'], booked_start, booked_end
    return True, None, None, None

#flash(f"Date clash detected with audit {clash_audit}: {clash_start} to {clash_end}. Please change the dates.", 'danger')

@app.route('/clear/<audit_number>')
@login_required
def clear_selections(audit_number):
    if 'selections' in session:
        try:
            #selections_df = pd.DataFrame(session['selections'])

            # Filter out selections for the current audit
            session['selections'] = [
                selection for selection in session['selections']
                if selection['audit_number'] != str(audit_number)
            ]

            # Convert session selections to DataFrame

            session.modified = True

            # Reset utilization for employees in the current audit
            project_data = data[data['audit_number'] == audit_number]
            emp_ids_in_audit = project_data['PSID'].astype(int).unique()

            for emp_id in emp_ids_in_audit:
                emp_id_int = int(emp_id)
                current_utilization = utilization.get(emp_id_int, 0)

                # Get available days from the selections DataFrame
                #available_days_str = project_data[project_data['PSID'] == emp_id]['Utilization'].values[0]
                #if available_days_str:
                try:
                    #available_days = int(available_days_str)
                    utilization[emp_id_int] = max(0, current_utilization - current_utilization)
                except ValueError as e:
                    print(f"Error parsing available days for employee ID {emp_id_int}: {e}")
                    flash(f"Invalid available days for employee ID {emp_id_int}.", 'danger')
                #else:
                #    print(f"Available days are missing for employee ID {emp_id_int}")
                #    flash(f"Available days are missing for employee ID {emp_id_int}.", 'warning')

        except Exception as e:
            print(f"Error resetting utilization for audit {audit_number}: {e}")
            flash(f"An error occurred while clearing selections for audit {audit_number}.", 'danger')

    return redirect(url_for('view_resources', audit_number=str(audit_number)))

if __name__ == '__main__':
    app.run(debug=True)
