import random
from datetime import time
from django.core.management.base import BaseCommand
from store.models import ClassLevel, TeacherSubject, TimetableSlot, Room

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Structured daily lesson blocks
TIME_SLOTS = [
    (time(8, 0), time(8, 30)),
    (time(8, 30), time(9, 0)),

    (time(9, 30), time(10, 0)),
    (time(10, 0), time(10, 30)),

    (time(11, 0), time(11, 30)),
    (time(11, 30), time(12, 0)),

    (time(13, 0), time(13, 30)),
    (time(13, 30), time(14, 0)),
    (time(14, 0), time(14, 30)),

    # Evening double/single slot
    (time(16, 0), time(17, 0)),
]

DOUBLE_SUBJECTS = ["Chemistry", "Biology", "Physics"]

class Command(BaseCommand):
    help = "Generate timetable automatically with strict rules"

    def handle(self, *args, **kwargs):
        TimetableSlot.objects.all().delete()

        for class_room in ClassLevel.objects.all():
            print(f"Generating timetable for {class_room}")

            teacher_subjects = list(
                TeacherSubject.objects.filter(class_room=class_room)
            )

            subject_map = {ts.subject.name: ts for ts in teacher_subjects}

            # Pick which days get double lessons (Chem/Bio/Physics)
            double_days = random.sample(DAYS, len(DOUBLE_SUBJECTS))
            double_assign = dict(zip(double_days, DOUBLE_SUBJECTS))

            for day in DAYS:
                used_subjects = set()   # Prevent duplicate subjects in a day

                for index, (start, end) in enumerate(TIME_SLOTS):

                    # evening slot (double or single)
                    if index == len(TIME_SLOTS) - 1:

                        # If this day has a designated double subject
                        if day in double_assign:
                            subject_name = double_assign[day]
                        else:
                            # Pick ANY single subject that is not repeated
                            subject_name = random.choice([
                                s.subject.name for s in teacher_subjects
                                if s.subject.name not in used_subjects
                            ])

                    else:
                        # Normal lesson slot — no repeats allowed
                        available = [
                            s.subject.name for s in teacher_subjects
                            if s.subject.name not in used_subjects
                        ]

                        if not available:
                            # Reset if exhausted — prevents crash
                            used_subjects = set()
                            available = [s.subject.name for s in teacher_subjects]

                        subject_name = random.choice(available)

                    used_subjects.add(subject_name)
                    ts = subject_map[subject_name]

                    # Check teacher & room availability
                    teacher_busy = TimetableSlot.objects.filter(
                        teacher=ts.teacher, day=day, start_time=start
                    ).exists()

                    room_busy = False
                    if ts.room:
                        room_busy = TimetableSlot.objects.filter(
                            room=ts.room, day=day, start_time=start
                        ).exists()

                    if teacher_busy or room_busy:
                        continue  # Skip this slot and try next

                    TimetableSlot.objects.create(
                        class_room=class_room,
                        teacher=ts.teacher,
                        subject=ts.subject,
                        room=ts.room,
                        day=day,
                        start_time=start,
                        end_time=end
                    )

        print("Timetable generated successfully.")
