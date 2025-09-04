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
