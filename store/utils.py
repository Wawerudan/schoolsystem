import requests
from django.conf import settings
from .models import Student, Result, ExamSummary

def format_phone(number):
    """Convert 07XXXXXXXX to +2547XXXXXXXX"""
    number = str(number).strip()
    if number.startswith("0"):
        return "+254" + number[1:]
    if number.startswith("+254"):
        return number
    if number.startswith("254"):
        return "+" + number
    return number


def send_at_sms(to, message):
    """
    Send SMS via Africa's Talking API.
    Automatically switches between sandbox (local) and live (deployment).
    Catches SSL and JSON errors.
    """
    # Sandbox for local testing
    if getattr(settings, "LOCAL_ENV", False):
        print("MOCK SMS:", to, message)
        return {"status": "sent", "mock": True}

    url = "https://api.africastalking.com/version1/messaging"  # live API
    headers = {
        "apiKey": settings.AFRICASTALKING_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "username": settings.AFRICASTALKING_USERNAME,
        "to": to,
        "message": message,
        "from": "AFRICASTKNG"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        # Safely parse JSON
        try:
            data = response.json()
        except ValueError:
            return {"status": "failed", "error": f"Invalid response: {response.text}"}

        sms_data = data.get("SMSMessageData", {})
        recipients = sms_data.get("Recipients", [])

        if recipients and recipients[0].get("status") == "Success":
            return {"status": "sent"}

        return {"status": "failed", "error": sms_data.get("Message", "Unknown error")}

    except requests.exceptions.RequestException as e:
        return {"status": "failed", "error": str(e)}


def send_results_to_all_students(exam):
    """
    Send SMS results for all students in a given exam.
    Returns a summary including sent, failed, and error details.
    """
    students = Student.objects.filter(result__exam=exam).distinct()
    sent_count = 0
    failed_count = 0
    failed_details = []  # Store tuples: (student, phone, error)

    for student in students:
        results = Result.objects.filter(student=student, exam=exam)
        summary = ExamSummary.objects.filter(student=student, exam=exam).first()
        parent_number = format_phone(student.parent_no)

        if not results.exists():
            failed_count += 1
            failed_details.append((student, parent_number, "No results found"))
            continue

        # Build message
        message = f"Dear Parent,\nHere are {student.First_name} {student.surname}'s results:\n"
        for r in results:
            grade_text = f" ({r.grade})" if r.grade else ""
            message += f"{r.subject}: {r.marks}{grade_text}\n"

        if summary:
            if getattr(summary, "total_marks", None) is not None:
                message += f"\nTotal Marks: {summary.total_marks}\n"
            if summary.mean_grade:
                message += f"Mean Grade: {summary.mean_grade}\n"
            if getattr(summary, "position", None) is not None:
                message += f"Overall Position: {summary.position}\n"

        message += "\nRegards, St Waweru Academy."

        # Send SMS
        response = send_at_sms(parent_number, message)

        if response.get("status") == "sent":
            sent_count += 1
        else:
            failed_count += 1
            error_msg = response.get("error", "Unknown error")
            failed_details.append((student, parent_number, error_msg))

    return {
        "sent": sent_count,
        "failed": failed_count,
        "failed_details": failed_details
    }
