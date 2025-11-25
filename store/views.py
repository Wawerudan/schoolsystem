from django.shortcuts import render,get_object_or_404
from .models import Result,Student,Finance,Reporting,Subject,StudentSubject,ExamCard,ClassLevel,TimetableSlot
from collections import defaultdict
import json
from django.utils import timezone
import matplotlib.pyplot as plt
from io import BytesIO
from django.db.models import Avg
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.pdfgen import canvas
import io
import matplotlib.pyplot as plt
from django.http import HttpResponse, FileResponse,JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
import barcode
from barcode.writer import ImageWriter




def student_performance_plot(request):
    subjects = []
    averages = []
    
    data = (
        Result.objects.values('subject')
       .annotate(avg_marks=Avg('marks'))
        .order_by('subject')
    )

    for entry in data:
        subjects.append(entry['subject'])
        averages.append(entry['avg_marks'])

    # Create chart
    plt.figure(figsize=(7, 4))
    plt.bar(subjects, averages,color='red')
    plt.title("Average Marks per Subject")
    plt.xlabel("Subject")
    plt.ylabel("Average Marks")
   
    

    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


def student_chart_view(request):
    students = Student.objects.all()
    data = []

    for student in students:
        results = Result.objects.filter(student=student)
        subjects = [r.subject for r in results]
        marks = [r.marks for r in results]

        data.append({
            "name": f"{student.First_name} {student.surname}",
            "subjects": subjects,
            "marks": marks
        })

    return render(request, "students.html", {
        "students_data": json.dumps(data)
    })
    
    #student portaaaaaaaaaaaaaaaaaaaaaaaaaaal

def login_view(request):
    if request.method == 'POST':
        admission_no = request.POST.get('admission_no')
        password = request.POST.get('password')

        user = authenticate(request, admission_no=admission_no, password=password)
        if user is not None:
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid admission number or password')
    return render(request, 'login.html')



def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def student_dashboard(request):
    student = request.user  
    finance = Finance.objects.filter(student=student)
    registered_subjects = StudentSubject.objects.filter(student=student)
    term = "Term 1 2025"  # you can automate this later
    report = Reporting.objects.filter(student=student, term=term).first()
    return render(request, 'student_portal.html', 
                  {'student': student,
                    "finance": finance,
                    "report":report,
                    "term":term,
                    "registered_subjects":registered_subjects,})

def report_start_of_term(request):
    student = request.user
    term = "Term 1 2025"

    report, created = Reporting.objects.get_or_create(
        student=student,
        term=term,
        defaults={"has_reported": True}
    )

    if created:
        message = "You successfully reported for this term."
    else:
        message = "You have already reported for this term!"

    return render(request, "report.html", {"message": message})

@login_required
def student_chart(request):
    student = request.user  # Logged-in student

    results = Result.objects.filter(student=student)
    subjects = [r.subject for r in results]  # assuming subject has 'name' field
    marks = [r.marks for r in results]

    data = {
        "name": f"{student.First_name} {student.surname or ''}",
        "subjects": subjects,
        "marks": marks
    }

    return render(request, "student_portal.html", {
        "student_data": json.dumps(data)
    })

def results(request):
    student = request.user

    # Get selected term from URL ?term=Term 1
    selected_term = request.GET.get("term")

    # Base query
    student_results = Result.objects.filter(student=student)

    # If user selected a term, filter results by that term
    if selected_term:
        student_results = student_results.filter(exam__term=selected_term)

    # Chart data
    subjects = [r.subject for r in student_results]
    marks = [r.marks for r in student_results]

    chart_data = {
        "labels": subjects,
        "datasets": [
            {
                "label": "Marks",
                "data": marks,
                "borderWidth": 2,
            }
        ]
    }

    return render(request, "students.html", {
        "student": student,
        "student_results": student_results,
        "chart_data": json.dumps(chart_data),
        "selected_term": selected_term,
    })


def add_header_footer(canvas, doc):
    """Draw logo, school name, and signature line."""
    canvas.saveState()

    # --- Header ---
    # Draw the logo (ensure you have logo.png in your static folder)
    logo_path = "static/logo.png"  # adjust path if different
    try:
        canvas.drawImage(logo_path, 40, 730, width=60, height=60)
    except:
        pass  # skip if logo not found

    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(120, 760, "St. Waweru Academy")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(120, 745, "P.O. Box 123, Nairobi, Kenya")
    canvas.drawString(120, 732, "Tel: +254 758 079 624")

    # --- Footer (Signature line) ---
    canvas.setFont("Helvetica", 12)
    canvas.drawString(50, 100, "Principle’s Signature:")
    canvas.line(170, 100, 370, 100)

    canvas.drawString(400, 100, "Date:")
    canvas.line(440, 100, 550, 100)

    canvas.restoreState()


def download_pdf(request):
    student = request.user
    results = Result.objects.filter(student=student)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_results.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    styles = getSampleStyleSheet()
    story = []

   
    story.append(Paragraph(
        f"<b>Student Academic Report</b>", styles["Title"]
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<b>Name:</b> {student.First_name} {student.surname} &nbsp;&nbsp;&nbsp;"
        f"<b>Gender:</b> {student.gender} &nbsp;&nbsp;&nbsp;"
        f"<b>Admission No:</b> {student.admission_no}", styles["Normal"] 
    ))
   
    story.append(Spacer(1, 20))

    
    data = [['Subject', 'Marks','Teachers comments']]
    for r in results:
        data.append([r.subject, str(r.marks)])

    table = Table(data, colWidths=[250, 100, 200])
    table.setStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ])
    story.append(table)
    story.append(Spacer(1, 30))

    # --- Add a Performance Chart (Matplotlib) ---
    subjects = [r.subject for r in results]
    marks = [r.marks for r in results]

    if subjects and marks:
        plt.figure(figsize=(5, 3))
        plt.bar(subjects, marks)
        plt.title("Student Performance")
        plt.xlabel("Subjects")
        plt.ylabel("Marks")
        plt.ylim(0, 100)

        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="PNG")
        plt.close()
        img_buffer.seek(0)

        story.append(Image(img_buffer, width=4*inch, height=2*inch))
        story.append(Spacer(1, 30))

    # --- Build PDF ---
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return response

def register_subjects(request):
    student = request.user
    student_class = student.class_level   # get student class

    # Subjects only for the student's class
    allowed_subjects = Subject.objects.filter(class_level=student_class)

    if request.method == "POST":
        selected_ids = request.POST.getlist("subjects")

        # Remove old registrations
        StudentSubject.objects.filter(student=student).delete()

        for sid in selected_ids:
            subject = Subject.objects.get(id=sid)
            StudentSubject.objects.create(student=student, subject=subject)

        return render(request, "subjects.html", {
            "message": "Subjects registered successfully!",
        })

    # Get already registered subjects
    registered = StudentSubject.objects.filter(student=student).values_list("subject_id", flat=True)

    return render(request, "subjects.html", {
        "allowed_subjects": allowed_subjects,
        "registered": registered,
        "student": student,
    })




def generate_exam_card(request):
    student = request.user
    term = "Term 1 2025"

    
    finance = Finance.objects.filter(student=student).first()

    if not finance:
        return HttpResponse("Finance record missing")

    if finance.balance > 0:
        return HttpResponse("Cannot generate exam card. Fees NOT cleared.")

    subjects = StudentSubject.objects.filter(student=student)

    if not subjects.exists():
        return HttpResponse("You have not registered any subjects.")

    # --- 3. Create or get exam card ---
    exam_card, created = ExamCard.objects.get_or_create(student=student, term=term)

    # --- 4. Generate BARCODE (Code128) ---
    barcode_value = str(exam_card.code)  # typically something like "ST12345-T1"
    CODE128 = barcode.get("code128", barcode_value, writer=ImageWriter())

    barcode_io = io.BytesIO()
    CODE128.write(barcode_io)
    barcode_io.seek(0)

    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>EXAMINATION CARD</b>", styles['Title']))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>Name:</b> {student.First_name} {student.surname}", styles['Normal']))
    story.append(Paragraph(f"<b>Admission:</b> {student.admission_no}", styles['Normal']))
    story.append(Paragraph(f"<b>Term:</b> {term}", styles['Normal']))

    story.append(Spacer(1, 20))



    # --- Subject Table ---
    data = [["Subjects"  ,"signature"]]
    for s in subjects:
        data.append([s.subject.name])

    table = Table(data, colWidths=[250, 200])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))

    story.append(table)
    
    # --- Insert BARCODE into PDF ---
    story.append(Spacer(1, 50))
    story.append(Image(barcode_io, width=200, height=70, hAlign='LEFT'))
    story.append(Spacer(1, 40))
    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename="exam_card.pdf")


from django.shortcuts import render, redirect


def signup_view(request):
    
    if request.method == "POST":
        admission_no = request.POST.get("admission_no")
        password = request.POST.get("password")

        try:
            student = Student.objects.get(admission_no=admission_no)
        except Student.DoesNotExist:
            messages.error(request, "Admission number not found.")
            return redirect("signup")

        # set password securely
        student.set_password(password)
        student.save()

        messages.success(request, "Password created! You can now log in.")
        return redirect("login")

    return render(request, "signup.html")
       


 # Or your portal page


from django.shortcuts import render
from .forms import ExamSelectForm
from .utils import send_results_to_all_students


def send_results_view(request):
    sent = failed = 0
    selected_exam = None
    failed_details = []

    if request.method == "POST":
        form = ExamSelectForm(request.POST)
        if form.is_valid():
            selected_exam = form.cleaned_data["exam"]
            summary = send_results_to_all_students(selected_exam)
            sent = summary["sent"]
            failed = summary["failed"]
            failed_details = summary["failed_details"]

    else:
        form = ExamSelectForm()

    return render(request, "send_results.html", {
        "form": form,
        "sent": sent,
        "failed": failed,
        "failed_details": failed_details,
        "exam": selected_exam,
    })






# views.py






DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def class_timetable(request, class_id):
    # Get all slots for class
    slots = TimetableSlot.objects.filter(class_room_id=class_id).order_by("day", "start_time")

    # extract time slots (top row)
    time_slots = list(
        slots.values("start_time", "end_time").distinct().order_by("start_time")
    )

    # prepare timetable structure
    timetable = {day: [] for day in DAYS}

    for day in DAYS:
        day_slots = []
        for t in time_slots:
            # find a slot matching this day + time
            slot = slots.filter(
                day=day,
                start_time=t["start_time"],
                end_time=t["end_time"]
            ).first()

            day_slots.append(slot)   # slot or None

        timetable[day] = day_slots

    return render(request, "schooltimetable.html",{
        "time_slots": time_slots,
        "timetable": timetable,
        "days": DAYS
    })


    


    
