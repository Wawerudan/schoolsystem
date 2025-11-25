import pandas as pd
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, Avg
from .models import Exam, Result, Student, ExamSummary


def calculate_subject_positions(exam):
    """Calculate subject-wise positions for each student in the exam."""
    subjects = Result.objects.filter(exam=exam).values_list("subject", flat=True).distinct()

    for subject in subjects:
        records = Result.objects.filter(exam=exam, subject=subject).order_by("-marks")
        position = 1
        previous_marks = None
        same_rank_count = 0

        for idx, record in enumerate(records, start=1):
            if record.marks == previous_marks:
                record.subject_position = position
                same_rank_count += 1
            else:
                position = idx
                same_rank_count = 1
                record.subject_position = position

            record.save()
            previous_marks = record.marks


def calculate_overall_positions_by_points(exam):
    """Calculate overall positions based on points in ExamSummary."""
    summaries = ExamSummary.objects.filter(exam=exam)
    totals = []

    for summary in summaries:
        pts = summary.points or 0
        totals.append((summary.student_id, pts))

    # Sort descending
    totals.sort(key=lambda x: x[1], reverse=True)

    position = 0
    previous_total = None

    for idx, (student_id, total_points) in enumerate(totals, start=1):
        if total_points == previous_total:
            # tie → same position
            pass
        else:
            position = idx

        ExamSummary.objects.filter(exam=exam, student_id=student_id).update(
            overall_position=position
        )
        previous_total = total_points


@receiver(post_save, sender=Exam)
def import_results_from_excel(sender, instance, created, **kwargs):
    """Import results from uploaded Excel, calculate points, grades, and positions."""
    if not instance.upload_results:
        return

    file_path = instance.upload_results.path

    try:
        df = pd.read_excel(file_path, dtype={'Admission_No': str})
        df = df.dropna(how="all")  # remove fully empty rows
        df = df.dropna(subset=["Admission_No"])  # remove rows without admission number
        df.columns = df.columns.str.strip()

        if "Admission_No" not in df.columns:
            print("❌ Excel missing Admission_No column")
            return

        df["Admission_No"] = df["Admission_No"].astype(str).str.replace('.0', '', regex=False).str.strip()

        subject_columns = []
        grade_columns = {}

        # Detect subject & grade columns
        for idx, col in enumerate(df.columns):
            if col in ["Name", "Admission_No", "Marks", "points", "mean_grade"]:
                continue

            sample = df[col].dropna().astype(str).head(5).tolist()
            is_marks = all(s.replace('.', '', 1).isdigit() for s in sample if s.strip() != "")
            if not is_marks:
                continue

            grade_col = None
            if idx + 1 < len(df.columns):
                next_col = df.columns[idx + 1]
                next_sample = df[next_col].dropna().astype(str).head(5).tolist()
                looks_like_grade = any(val.strip()[0] in "ABCDE" for val in next_sample if len(val.strip()) > 0)
                if looks_like_grade:
                    grade_col = next_col

            subject_columns.append(col)
            grade_columns[col] = grade_col

        # Process each student
        for _, row in df.iterrows():
            admission_no = row["Admission_No"].strip()
            if not admission_no or admission_no.lower() == "nan":
                continue

            student = Student.objects.filter(admission_no=admission_no).first()
            if not student:
                print(f"⚠ Student {admission_no} not found")
                continue

            total_points = 0  # calculate per student

            for subject in subject_columns:
                marks = row[subject]
                if pd.isna(marks) or not isinstance(marks, (int, float)):
                    continue

                grade = None
                grade_col = grade_columns.get(subject)
                if grade_col:
                    g = row[grade_col]
                    if not pd.isna(g):
                        grade = str(g).strip()

               

                Result.objects.update_or_create(
                    exam=instance,
                    student=student,
                    subject=subject,
                    defaults={
                        "marks": float(marks),
                        "grade": grade,
                        
                    }
                )
            points = row.get("points") or 0
            total_points += points if not pd.isna(points) else 0
            mean_grade = row.get("mean_grade")
            total_marks=row.get("Marks")
            # Save in ExamSummary
            ExamSummary.objects.update_or_create(
                exam=instance,
                student=student,
                defaults={
                    "points": total_points,
                    "total_marks":total_marks,
                    "mean_grade": str(mean_grade).strip() if not pd.isna(mean_grade) else None
                }
            )

        print("✅ Successfully imported marks, grades, and points.")

        # Calculate positions
        calculate_subject_positions(instance)
        calculate_overall_positions_by_points(instance)

        print("✅ Rankings calculated successfully!")

    except Exception as e:
        print(f"❌ Error importing Excel: {e}")
