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
