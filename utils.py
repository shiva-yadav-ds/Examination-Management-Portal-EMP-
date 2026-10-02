from datetime import datetime

# Examiners may still add slots after student booking opens, as long as the
# slot-creation window is active. Closed/Completed exams never accept new slots.
SLOT_CREATE_STATUSES = ("Slot Creation", "Booking Open")


# Checks whether the examination is currently accepting new time slots from examiners.
# Uses current server/application datetime to match timestamps configured by administrators.
def is_slot_creation_open(exam):
    now = datetime.now()

    if not exam.slot_creation_start or not exam.slot_creation_end:
        return False

    return exam.slot_creation_start <= now <= exam.slot_creation_end


# Returns detailed diagnostic status for the slot creation window.
def get_slot_creation_window_info(exam):
    now = datetime.now()
    if not exam.slot_creation_start or not exam.slot_creation_end:
        return {
            "is_open": False,
            "status": "unconfigured",
            "message": f"Slot creation window dates have not been configured for {exam.name}."
        }
    if now < exam.slot_creation_start:
        return {
            "is_open": False,
            "status": "upcoming",
            "message": (
                f"Slot creation window for {exam.name} has not opened yet. "
                f"It opens on {exam.slot_creation_start.strftime('%d %b %Y, %H:%M')}. "
                f"(Current server time: {now.strftime('%d %b %Y, %H:%M')})"
            )
        }
    if now > exam.slot_creation_end:
        return {
            "is_open": False,
            "status": "closed",
            "message": (
                f"Slot creation window for {exam.name} closed on {exam.slot_creation_end.strftime('%d %b %Y, %H:%M')}. "
                f"(Current server time: {now.strftime('%d %b %Y, %H:%M')})"
            )
        }
    return {
        "is_open": True,
        "status": "open",
        "message": f"Slot creation window is currently open until {exam.slot_creation_end.strftime('%d %b %Y, %H:%M')}."
    }


# Checks whether the student booking window is currently active.
# Uses current server/application datetime.
def is_booking_open(exam):
    now = datetime.now()

    if not exam.booking_start or not exam.booking_end:
        return False

    return exam.booking_start <= now <= exam.booking_end


# Returns detailed diagnostic status for the student booking window.
def get_booking_window_info(exam):
    now = datetime.now()
    if not exam.booking_start or not exam.booking_end:
        return {
            "is_open": False,
            "status": "unconfigured",
            "message": f"Booking window dates have not been configured for {exam.name}."
        }
    if now < exam.booking_start:
        return {
            "is_open": False,
            "status": "upcoming",
            "message": (
                f"Student booking window for {exam.name} has not opened yet. "
                f"It opens on {exam.booking_start.strftime('%d %b %Y, %H:%M')}. "
                f"(Current server time: {now.strftime('%d %b %Y, %H:%M')})"
            )
        }
    if now > exam.booking_end:
        return {
            "is_open": False,
            "status": "closed",
            "message": (
                f"Student booking window for {exam.name} closed on {exam.booking_end.strftime('%d %b %Y, %H:%M')}. "
                f"(Current server time: {now.strftime('%d %b %Y, %H:%M')})"
            )
        }
    return {
        "is_open": True,
        "status": "open",
        "message": f"Student booking window is currently open until {exam.booking_end.strftime('%d %b %Y, %H:%M')}."
    }


# True when faculty may still create slots: exam is in an eligible phase AND the
# configured slot-creation window contains the current server time.
def can_examiner_create_slots(exam):
    if exam.status not in SLOT_CREATE_STATUSES:
        return False
    return is_slot_creation_open(exam)


def is_slot_creation_visible_to_examiners(exam):
    now = datetime.now()
    if exam.status not in SLOT_CREATE_STATUSES:
        return False
    if not exam.slot_creation_end:
        return False
    return now <= exam.slot_creation_end


# True when a student may book or cancel: admin has opened booking AND the
# booking window contains the current server time.
def can_student_book(exam):
    if exam.status != "Booking Open":
        return False
    return is_booking_open(exam)


# True when every rubric criterion for the exam has a saved evaluation row.
def is_booking_fully_evaluated(booking):
    rubrics = list(booking.examination.rubrics)
    if not rubrics:
        return False
    scored_ids = {ev.rubric_id for ev in booking.evaluations}
    return all(r.id in scored_ids for r in rubrics)
