from db import get_connection
from datetime import datetime, timedelta
from datetime import date


def is_holiday(date):
    if date.weekday() == 6:  # Sunday
        return True
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM holidays WHERE date = ?", (date.strftime("%Y-%m-%d"),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_unpaid_installments_with_fine(student_id, conn):
    cursor = conn.cursor()
    today = date.today()
    results = []

    cursor.execute("""
        SELECT id, due_date, amount_due FROM fee_schedule
        WHERE student_id = ? AND is_paid = 0
        ORDER BY due_date
    """, (student_id,))
    rows = cursor.fetchall()

    for sched_id, due_date_str, amount in rows:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        overdue_days = (today - due_date).days
        fine = 100 * overdue_days if overdue_days > 0 else 0
        total_due = amount + fine
        results.append({
            "Installment ID": sched_id,
            "Due Date": due_date_str,
            "Amount": amount,
            "Fine": fine,
            "Total Due": total_due
        })

    return results


# 🎓 Course Completion Status
def get_course_completion_status(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?", (student_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'", (student_id,))
    present = cursor.fetchone()[0]

    conn.close()

    if total == 0:
        return "Not Evaluated"

    attendance_percent = (present / total) * 100
    return "Completed" if attendance_percent >= 70 else "Attendance Short"


# 🔴🟢🟣 Update Status Based on Attendance
def update_student_status(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Check if attendance exists
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?", (student_id,))
    total = cursor.fetchone()[0]
    if total == 0:
        conn.close()
        return  # 🚫 No attendance yet – don't change status

    # ✅ Check last 10 records
    cursor.execute("""
        SELECT status FROM attendance
        WHERE student_id=? ORDER BY date DESC LIMIT 10
    """, (student_id,))
    last_10 = [row[0] for row in cursor.fetchall()]

    if len(last_10) == 10 and all(status == "Absent" for status in last_10):
        cursor.execute("UPDATE students SET status='deactivated' WHERE id=?", (student_id,))
    else:
        # Check if Leave >= 20 days
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Leave'", (student_id,))
        leave_days = cursor.fetchone()[0]
        if leave_days >= 20:
            cursor.execute("UPDATE students SET status='paused' WHERE id=?", (student_id,))
        else:
            cursor.execute("UPDATE students SET status='active' WHERE id=?", (student_id,))

    conn.commit()
    conn.close()


# 💸 Fine Calculator + Auto Deactivate
def calculate_fine(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # 👤 Get due day + admission date
    cursor.execute("SELECT due_day, admission_date FROM students WHERE id=?", (student_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return 0

    due_day, admission_date = result
    today = datetime.today().date()
    admission_date_obj = datetime.strptime(admission_date, "%Y-%m-%d").date()

    # 🔍 Get last payment
    cursor.execute("SELECT MAX(payment_date) FROM fees WHERE student_id=?", (student_id,))
    last_payment = cursor.fetchone()[0]

    # 🚫 Skip fine if no payment and student is new (<30 days)
    if last_payment is None:
        days_since_admission = (today - admission_date_obj).days
        if days_since_admission < 30:
            conn.close()
            return 0

    # 🗓️ Determine next due date
    if last_payment:
        last_paid = datetime.strptime(last_payment, "%Y-%m-%d").date()
        try:
            next_due = last_paid.replace(day=due_day)
        except ValueError:
            next_due = last_paid.replace(day=28)

        if last_paid.day > due_day:
            next_due = (last_paid.replace(day=1) + timedelta(days=32)).replace(day=due_day)
    else:
        base_date = admission_date_obj
        try:
            next_due = base_date.replace(day=due_day)
        except ValueError:
            next_due = base_date.replace(day=28)

        if next_due < base_date:
            next_due = (base_date.replace(day=1) + timedelta(days=32)).replace(day=due_day)

    # 🔐 If not due yet, no fine
    if today < next_due:
        conn.close()
        return 0

    # ✅ Check for approved exceptions
    due_month = next_due.strftime("%Y-%m")
    cursor.execute("SELECT approved FROM fee_exceptions WHERE student_id=? AND due_month=?", (student_id, due_month))
    exception = cursor.fetchone()
    if exception and exception[0] == 1:
        conn.close()
        return 0

    # 💸 Fine + 🔴 Deactivation if too late
    delay = (today - next_due).days
    fine = delay * 100

    if delay > 10:
        cursor.execute("UPDATE students SET status='deactivated' WHERE id=?", (student_id,))
        conn.commit()

    conn.close()
    return fine



def apply_auto_fines():
    today = datetime.today()
    conn = get_connection()
    cursor = conn.cursor()

    # Get active students and their due day
    cursor.execute("SELECT id, due_day FROM students WHERE status = 'active'")
    students = cursor.fetchall()

    for student_id, due_day in students:
        due_date = datetime(today.year, today.month, due_day)

        if today > due_date:
            days_late = (today - due_date).days

            # Check if student already paid this month's fee
            cursor.execute("""
                SELECT COUNT(*) FROM fees
                WHERE student_id = ? AND strftime('%Y-%m', payment_date) = ?
            """, (student_id, today.strftime("%Y-%m")))
            fee_paid = cursor.fetchone()[0]

            # Check for exception
            cursor.execute("""
                SELECT COUNT(*) FROM fee_exceptions
                WHERE student_id = ? AND due_month = ? AND approved = 1
            """, (student_id, today.strftime("%Y-%m")))
            exception = cursor.fetchone()[0]

            if fee_paid == 0 and exception == 0:
                fine_amount = 100 * days_late

                # Check if fine already added for today
                cursor.execute("""
                    SELECT COUNT(*) FROM fines
                    WHERE student_id = ? AND date = ?
                """, (student_id, today.strftime("%Y-%m-%d")))
                already_fined = cursor.fetchone()[0]

                if already_fined == 0:
                    cursor.execute("""
                        INSERT INTO fines (student_id, date, amount, reason)
                        VALUES (?, ?, ?, ?)
                    """, (student_id, today.strftime("%Y-%m-%d"), fine_amount, f"{days_late} days late"))

                # If >10 days late, deactivate
                if days_late > 10:
                    cursor.execute("""
                        UPDATE students SET status = 'deactivated' WHERE id = ?
                    """, (student_id,))

    cursor.execute("""
    SELECT s.id, s.admission_date, s.final_fee, c.duration_months
        FROM students s
        JOIN courses c ON s.course_id = c.id
        WHERE s.status = 'active'
    """)
    records = cursor.fetchall()
    
    for student_id, admission_date, final_fee, duration_months in records:
        if not admission_date or not duration_months:
            continue
    
        try:
            start = datetime.strptime(admission_date, "%Y-%m-%d")
            end_date = start + timedelta(days=duration_months * 30)
        except:
            continue
    
        if datetime.today() > end_date:
            cursor.execute("SELECT SUM(amount_paid) FROM fees WHERE student_id = ?", (student_id,))
            total_paid = cursor.fetchone()[0] or 0
    
            if total_paid < final_fee:
                cursor.execute("UPDATE students SET status = 'deactivated' WHERE id = ?", (student_id,))

    conn.commit()
    conn.close()


def check_and_update_leave_status():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all active students
    cursor.execute("SELECT id FROM students WHERE status = 'active'")
    students = cursor.fetchall()

    for (student_id,) in students:
        # Get last 30 days of attendance
        today = datetime.today()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT date, status FROM attendance
            WHERE student_id = ? AND date >= ?
            ORDER BY date
        """, (student_id, start_date))
        records = cursor.fetchall()

        # Track longest continuous 'leave'
        longest_streak = 0
        current_streak = 0

        for _, status in records:
            if status == 'leave':
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 0

        if longest_streak >= 20:
            cursor.execute("UPDATE students SET status = 'paused' WHERE id = ?", (student_id,))

    conn.commit()
    conn.close()

