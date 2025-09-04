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
