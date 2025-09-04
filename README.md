# Stan-Chat-Projs
I am making a employee smart assignment project:
Different audit teams can select employee(book them for a time period)
That will show in booking csv and session 
And that time period(date will be registered)

now currectly error:
When I am submitting sumbit button it is not saving anything(not booking emp nor showhing booking in session and booking)
Ask questions to understand about the project and apart from this error try to find diff errors also

APP.py:

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
            return False, booked_start, booked_end
    return True, None, None

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

            if booked_from and booked_to:
                booked_from_date = pd.to_datetime(booked_from)
                booked_to_date = pd.to_datetime(booked_to)

                is_successful = add_booking(
                    audit_number=audit_number,
                    psid=emp_id_int,
                    full_name=request.form.get(f'full_name_{emp_id}'),
                    role=role,
                    phase=phase,
                    booked_from=booked_from_date,
                    booked_to=booked_to_date
                )

                if not is_successful:
                    continue

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

    flash("Booking added successfully!", 'success')
    return True



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
        psid = request.form['psid']
    except BadRequestKeyError as e:
        flash(f"Missing form data: {e}", 'danger')
        return redirect(url_for('view_resources', audit_number=request.form.get('audit_number', '')))

    # Remove from session
    if 'scheduled_emp' in session:
        session['scheduled_emp'] = [
            emp for emp in session['scheduled_emp']
            if not (emp['audit_number'] == audit_number and emp['psid'] == psid)
        ]


    # Remove from bookings.csv
    existing_bookings = load_bookings()
    updated_bookings = existing_bookings[
        ~((existing_bookings['audit_number'] == audit_number) & (existing_bookings['PSID'] == int(psid)))
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


view_resource.html






{% extends 'base.html' %}

{% block main_content %}

<h2 class="mb-3">Audit {{ audit_number }} - {{ audit_title }}</h2>
    <!-- Audit Details Section -->
    <div class="audit-details">
        <table class="table table-bordered table-fixed">
            <thead class="thead-dark">
                <tr>
                    <th>Scheduling Phase</th>
                    <th>Audit Plan Year</th>
                    <th>Audit Principal Risk Types</th>
                    <th>Audit Risk Radar Themes</th>
                    <th>Primary GIA Audit Owner Team</th>
                    <th>Planned Audit Notification Date</th>
                    <th>Planned Planning Start Date</th>
                    <th>Planned Planning End Date</th>
                    <th>Planned Fieldwork Start Date</th>
                    <th>Planned Fieldwork End Date</th>
                    <th>Planned Reporting Start Date</th>
                    <th>Planned Report Issuance Date</th>
                </tr>
            </thead>
            <tbody>
                {% for audit in audits %}
                    {% if audit['audit_number'] == audit_number %}
                <tr>
                        <!--
                    <td>{{ audit['SchedulingPhase'] }}</td>
                    <td>{{ audit['Audit Plan Year'] }}</td>
                    <td>{{ audit['Audit Principal Risk Types'] }}</td>
                    <td>{{ audit['Audit Risk Radar Themes'] }}</td>
                    <td>{{ audit['Primary GIA Audit Owner Team'] }}</td>
                    <td>{{ audit['Planned Audit Notification Date'] }}</td>
                    <td>{{ audit['Planned Planning Start Date'] }}</td>
                    <td>{{ audit['Planned Planning End Date'] }}</td>
                    <td>{{ audit['Planned Fieldwork Start Date'] }}</td>
                    <td>{{ audit['Planned Fieldwork End Date'] }}</td>
                    <td>{{ audit['Planned Reporting Start Date'] }}</td>
                    <td>{{ audit['Planned Report Issuance Date'] }}</td>    -->


                    <td>{{ audit['SchedulingPhase'] }}</td>
                    <td>{{ audit['audit_plan_year'] }}</td>
                    <td>{{ audit['audit_principal_risk_types'] }}</td>
                    <td>{{ audit['audit_risk_radar_themes'] }}</td>
                    <td>{{ audit['primary_gia_audit_owner_team'] }}</td>
                    <td>{{ audit['planned_audit_notification_date'] }}</td>
                    <td>{{ audit['planned_planning_start_date'] }}</td>
                    <td>{{ audit['planned_planning_end_date'] }}</td>
                    <td>{{ audit['planned_fieldwork_start_date'] }}</td>
                    <td>{{ audit['planned_fieldwork_end_date'] }}</td>
                    <td>{{ audit['planned_reporting_start_date'] }}</td>
                    <td>{{ audit['planned_report_issuance_date'] }}</td>

                </tr>
                    {% endif %}
                {% endfor %}
            </tbody>
        </table>
    </div>
<div class="content-wrapper">
    <form method="post">
        <table class="table table-bordered table-fixed">
            <thead class="thead-dark">
                <tr>
                    <th>Select</th>
                    <th>PSID</th>
                    <th>Full Name</th>
                    <th>Job Title</th>
                    <th>Team Name</th>
                    <th>City</th>
                    <th>Country</th>
                    <th>Availability</th>
                    <th>Similarity Score</th>
                    <th>Select Days</th>
                    <th>Select Phase</th>
                    <th>Select Role</th>
                    <th>Utilization %</th>
                    <th>Percent Free</th>
                    <th>Book From</th>
                    <th>Book To</th>
                    <th>Booked Periods</th>
                    <th>Delete</th>
                </tr>
            </thead>
            <tbody>
                {% for emp in employees %}
                <tr {% if emp.selected %}class="greyed-out"{% endif %}>
                    <td>
                        <input type="checkbox" name="selected_employees" value="{{ emp['PSID'] }}" {% if emp.selected %}disabled{% endif %} class="large-checkbox">
                    </td>
                    
                    <td>{{ emp['PSID'] }}</td>
                    <td>{{ emp['FullName'] }}</td>
                    <td>{{ emp['JobTitle'] }}</td>
                    <td>{{ emp['AuditTeamName'] }}</td>
                    <td>{{ emp['LocationCity'] }}</td>
                    <td>{{ emp['CountryName'] }}</td>
                    <td>{{ emp['AvailabilityFrom'] }} TO {{ emp['AvailabilityTo'] }} - 
                        {{ emp['available_days'] }} days -
                        {{ emp['Audit Phase Availability'] }}
                    </td>
                    <td>{{ (emp['WeightedSimilarityScore'] * 100) | round(2) }}%</td>
                    <td>
                        <input type="text" name="available_days_{{ emp['PSID'] }}"
                               {% if emp.selected %}readonly{% endif %} style="width: 75px;">
                    </td>
                    <td>
                        <input type="text" name="phase_{{ emp['PSID'] }}"
                               {% if emp.selected %}readonly{% endif %} style="width: 75px;">
                    </td>
                    <td>
                        <select name="role_{{ emp['PSID'] }}" class="form-control" {% if emp.selected %}disabled{% endif %}>
                            <option value="" >Select Role</option>
                            <option value="Team Manager">Team Manager</option>
                            <option value="Team Leader">Team Leader</option>
                            <option value="Team Member">Team Member</option>
                        </select>
                    </td>
                    <td>
                        {{ emp['Utilization Percent'] }}
                    </td>
                    <td>
                        {{ emp['PercentFree'] }}%
                    </td>
                    <td>
                        <input type="text" name="booked_from_{{ emp['PSID'] }}" class="datepicker" placeholder="Start date"
                               {% if emp.selected %}readonly{% endif %} style="width: 110px;">
                    </td>
                    <td>
                        <input type="text" name="booked_to_{{ emp['PSID'] }}" class="datepicker" placeholder="End date"
                               {% if emp.selected %}readonly{% endif %} style="width: 110px;">
                    </td>
                    <td>
                        {% for br in emp['BookedRanges'] %}
                            <span class="booked">{{ br[0] }} to {{ br[1] }}</span><br>
                        {% endfor %}
                    </td>
                    <td>
                        {% if emp.selected %}

                        <form method="post" action="{{ url_for('delete_booking') }}" style="display:inline;" onsubmit="return confirm('Are you sure you want to remove this employee from the audit?');">
                            <input type="hidden" name="audit_number" value="{{ audit_number }}">
                            <input type="hidden" name="psid" value="{{ emp['PSID'] }}">
                            <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                        </form>

                        {% endif %}
                    </td>

                </tr>
                {% endfor %}
            </tbody>
        </table>
        <!-- Combined Buttons and Pagination Controls -->
        <div class="d-flex align-items-center justify-content-between">
            <!-- Left Side: Submit Button -->
            <div>
                <button type="submit" name="submit" class="btn btn-success">Submit</button>
            </div>

            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
             <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
            <script>
            flatpickr(".datepicker", {
               mode: "single",
         dateFormat: "Y-m-d"
            });
            </script>
            <!-- Center: Pagination Controls -->
            <nav aria-label="Page navigation">
                <ul class="pagination mb-0">
                    <!-- Previous Page Link -->
                    {% if page > 1 %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('view_resources', audit_number=audit_number, page=page-1) }}" aria-label="Previous">
                            <span aria-hidden="true">&laquo;</span>
                        </a>
                    </li>
                    {% else %}
                    <li class="page-item disabled">
                        <a class="page-link" href="#" aria-label="Previous">
                            <span aria-hidden="true">&laquo;</span>
                        </a>
                    </li>
                    {% endif %}

                    <!-- Page Number Links -->
                    {% for p in range(1, total_pages + 1) %}
                    <li class="page-item {% if p == page %}active{% endif %}">
                        <a class="page-link" href="{{ url_for('view_resources', audit_number=audit_number, page=p) }}">{{ p }}</a>
                    </li>
                    {% endfor %}

                    <!-- Next Page Link -->
                    {% if page < total_pages %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('view_resources', audit_number=audit_number, page=page+1) }}" aria-label="Next">
                            <span aria-hidden="true">&raquo;</span>
                        </a>
                    </li>
                    {% else %}
                    <li class="page-item disabled">
                        <a class="page-link" href="#" aria-label="Next">
                            <span aria-hidden="true">&raquo;</span>
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            <!-- Right Side: Download and Clear Buttons -->
            <div>
                {% if session.get('selections') %}
                <a href="{{ url_for('download_schedule',audit_number=audit_number) }}" class="btn btn-info">Download Selections</a>
                <a href="{{ url_for('clear_selections', audit_number=audit_number) }}" class="btn btn-secondary">Clear Selections</a>
                <a href="{{ url_for('download_all') }}" class="btn btn-info">Download All Bookings</a>
                {% endif %}
            </div>
        </div>
    </form>
</div>
{% endblock %}


base.html:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Smart Scheduling Assistant</title>
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <!-- Banner -->
    <div class="banner">
        <div class="container-fluid">
            <div class="d-flex align-items-center justify-content-center">
                <!-- Left Side: Logo -->
                <div class="logo-container mr-auto">
                    <img src="{{ url_for('static', filename='ai_image.svg') }}" alt="Standard Chartered Logo" class="logo" style="width:auto; height:auto; margin-left: 20px;">
                    <img src="{{ url_for('static', filename='analytics.svg') }}" alt="Standard Chartered Logo" class="logo" style="width:auto; height:auto; margin-left: 20px;">
                </div>
                <!-- Center: Title with Calendar Icon -->
                <div class="title-container text-center">
                    <h1 class="banner-title">
                        <i class="fas fa-calendar-alt"></i> Smart Scheduling Assistant Tool
                    </h1>
                </div>
                <!-- Right Side: Logout Button -->
                <div class="logout-container ml-auto">
                    {% if session.get('username') %}
                    <span class="text-white mr-2">Welcome, {{ session['username'] }}</span>
                    <a href="{{ url_for('logout') }}" class="btn btn-outline-light">Logout</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container-fluid">
        <div class="row no-gutters">
            {% if 'login' not in request.path %}
            <!-- Sidebar -->
            <nav id="sidebar" class="col-md-2 d-none d-md-block sidebar">
                <div class="sidebar-sticky">
                    <h5 class="mt-4">Select Audit</h5>
                    <input type="text" id="searchInput" class="form-control mb-2" placeholder="Search Audit">
                    <button id="searchButton" class="btn btn-primary mb-2">Search</button>
                    <select id="auditSelect" class="form-control">
                        {% for audit in audits %}
                        
                        <option value="{{ audit['audit_number'] }}" {% if audit['audit_number'] == audit_number %}selected{% endif %}>
                            {{ audit['audit_number'] }} - {{ audit['audit_title'] }}
                        </option>
                        
                        {% endfor %}
                    </select>
                </div>
            </nav>
            {% endif %}
            <!-- Main Content Area -->
            <main role="main" class="{% if 'login' not in request.path %}with-sidebar{% else %}without-sidebar{% endif %}">
                {% block main_content %}
                {% endblock %}
            </main>
        </div>
    </div>

    <!--<script>
        // Store original audits for search reset
    var originalOptions = [];
    document.addEventListener('DOMContentLoaded', function() {
    var select = document.getElementById('auditSelect');
    for (var i = 0; i < select.options.length; i++) {
        originalOptions.push({
            value: select.options[i].value,
            text: select.options[i].text,
            selected: select.options[i].selected
           });
         }
     });

        document.getElementById('searchButton').addEventListener('click', function() {
            var input = document.getElementById('searchInput').value.toLowerCase();
            var select = document.getElementById('auditSelect');
            
            //new line of code below:
            select.innerHTML = ''; // Clear all options
            
            // old line of code below:
            //  var options = select.getElementsByTagName('option');

            /*for (var i = 0; i < options.length; i++) {
                var optionText = options[i].text.toLowerCase();
                if (optionText.includes(input)) {
                    options[i].style.display = '';
                } else {
                    options[i].style.display = 'none';
                }
            }
        });*/

        originalOptions.forEach(function(opt) {
        if (opt.text.toLowerCase().includes(input)) {
            var option = document.createElement('option');
            option.value = opt.value;
            option.text = opt.text;
            if (opt.selected) option.selected = true;
            select.appendChild(option);
        }
     });
    });
    </script>-->


<!--<script>
    // Store the original dropdown options for resetting after search
    var originalOptions = [];
    document.addEventListener('DOMContentLoaded', function() {
        var select = document.getElementById('auditSelect');
        // Save all initial options
        for (var i = 0; i < select.options.length; i++) {
            originalOptions.push({
                value: select.options[i].value,
                text: select.options[i].text,
                selected: select.options[i].selected
            });
        }

        // Search button click event
        document.getElementById('searchButton').addEventListener('click', function() {
            var input = document.getElementById('searchInput').value.toLowerCase();
            var select = document.getElementById('auditSelect');
            select.innerHTML = ''; // Clear all options before filtering

            var found = false; // Track if any results are found
            // Add only matching options
            originalOptions.forEach(function(opt) {
                if (opt.text.toLowerCase().includes(input)) {
                    var option = document.createElement('option');
                    option.value = opt.value;
                    option.text = opt.text;
                    if (opt.selected) option.selected = true;
                    select.appendChild(option);
                    found = true;
                }
            });

            // If no results, show a disabled "No results found" option
            if (!found) {
                var option = document.createElement('option');
                option.text = 'No results found';
                option.disabled = true;
                select.appendChild(option);
            }
        });

        // Reset dropdown when search box is cleared
        document.getElementById('searchInput').addEventListener('input', function() {
            if (this.value === '') {
                var select = document.getElementById('auditSelect');
                select.innerHTML = ''; // Clear all options
                // Restore all original options
                originalOptions.forEach(function(opt) {
                    var option = document.createElement('option');
                    option.value = opt.value;
                    option.text = opt.text;
                    if (opt.selected) option.selected = true;
                    select.appendChild(option);
                });
            }
        });
    });
</script>-->
    
    
<script>
    document.addEventListener('DOMContentLoaded', function() {
        var select = document.getElementById('auditSelect');
        var searchInput = document.getElementById('searchInput');
        var searchButton = document.getElementById('searchButton');
        var audits = [];
        var noResultMsg = document.createElement('div');
        noResultMsg.id = 'noResultMsg';
        noResultMsg.className = 'text-danger mt-2';
        noResultMsg.style.display = 'none';
        noResultMsg.innerText = 'No audit found';
        select.parentNode.appendChild(noResultMsg);

        // Store original audits for reset
        for (var i = 0; i < select.options.length; i++) {
            audits.push({
                value: select.options[i].value,
                text: select.options[i].text,
                selected: select.options[i].selected
            });
        }

        // Restore dropdown options
        function restoreOptions() {
            select.innerHTML = '';
            audits.forEach(function(opt) {
                var option = document.createElement('option');
                option.value = opt.value;
                option.text = opt.text;
                if (opt.selected) option.selected = true;
                select.appendChild(option);
            });
            noResultMsg.style.display = 'none';
        }

        // Dropdown change event (redirect)
        select.onchange = function() {
            var selectedAudit = this.value;
            window.location.href = "{{ url_for('view_resources', audit_number='') }}" + selectedAudit;
        };

        // Search button click event
        searchButton.addEventListener('click', function() {
            var input = searchInput.value.trim().toLowerCase();
            if (!input) {
                restoreOptions();
                return;
            }
            var found = false;
            for (var i = 0; i < audits.length; i++) {
                if (audits[i].text.toLowerCase().includes(input)) {
                    select.value = audits[i].value;
                    found = true;
                    // Trigger change event to redirect
                    select.dispatchEvent(new Event('change'));
                    noResultMsg.style.display = 'none';
                    break;
                }
            }
            if (!found) {
                noResultMsg.style.display = 'block';
            }
        });

        // Reset message and dropdown when typing
        searchInput.addEventListener('input', function() {
            if (this.value === '') {
                restoreOptions();
            }
            noResultMsg.style.display = 'none';
        });
    });
</script>

    <!-- jQuery and dependencies -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Custom JavaScript -->
    {% if 'login' not in request.path %}
    <script>
        // Handle audit selection change
        document.getElementById('auditSelect').addEventListener('change', function() {
            var selectedAudit = this.value;
            window.location.href = "{{ url_for('view_resources', audit_number='') }}" + selectedAudit;
        });
    </script>
    {% endif %}
</body>
</html>

CSV file:
booking.csv
audit_number,audit_title,PSID,FullName,Role,Phase,BookedFrom,BookedTo,Timestamp
2025-US-AU3003043,"Business Continuity Management, US",1563311,"Ha,Sung Bok",,,2025-09-08,2025-09-20,2025-09-01T16:29:49.874797
2025-US-AU3002921,Q3 Exam - FI - Latin America & Brazil,1601725,"Chua,Pei Wen",,,2025-09-01,2025-09-09,2025-09-01T16:44:15.131891
