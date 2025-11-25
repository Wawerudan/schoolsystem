from django.conf import settings
from .models import Student, Result, ExamSummary
import requests


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
    """Send SMS via Africa's Talking API"""
    url = "https://api.sandbox.africastalking.com/version1/messaging"
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

    # Optional: Mock for local testing
    if getattr(settings, "LOCAL_ENV", False):
        print("MOCK SMS:", to, message)
        return {"status": "sent", "mock": True}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        sms_data = data.get("SMSMessageData", {})
        recipients = sms_data.get("Recipients", [])
        if recipients and recipients[0].get("status") == "Success":
            return {"status": "sent"}
        return {"status": "failed", "error": sms_data.get("Message")}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def send_results_to_all_students(exam):
    """
    Send SMS results for all students in a given exam.
    Returns summary of sent, failed, and error details.
    """
    students = Student.objects.filter(result__exam=exam).distinct()
    sent_count = 0
    failed_count = 0
    failed_details = []  # Store tuples: (student, error)

    for student in students:
        results = Result.objects.filter(student=student, exam=exam)
        summary = ExamSummary.objects.filter(student=student, exam=exam).first()

        if not results.exists():
            failed_count += 1
            failed_details.append((student, "No results found"))
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
        response = send_at_sms(format_phone(student.parent_no), message)
        if response.get("status") == "sent":
            sent_count += 1
        else:
            failed_count += 1
            error_msg = response.get("error", "Unknown error")
            failed_details.append((student, error_msg))

    return {
        "sent": sent_count,
        "failed": failed_count,
        "failed_details": failed_details
    }

