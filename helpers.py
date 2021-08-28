def getSlots():
    return(
        {
            'Monday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Monday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
            'Tuesday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Tuesday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
            'Wednesday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Wednesday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
            'Thursday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Thursday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
            'Friday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Friday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
            'Saturday 09:00 - 12:00': {'count': 0, 'faculty': [], 'semester': []},
            'Saturday 12:45 - 15:45': {'count': 0, 'faculty': [], 'semester': []},
        }
    )


def fillSlots(courses, coursesData, slots):
    for course in courses:
        thisCourseSlot = coursesData[course]['slot']
        if(thisCourseSlot):
            s = thisCourseSlot
            slots[s]['count'] = slots[s]['count'] + 1


def findUnassignedCourse(courses, coursesData):
    for course in courses:
        thisCourseSlot = coursesData[course]['slot']
        if(thisCourseSlot == ''):
            return course


def populatePreAsigned(courses, coursesData, preAssigned):
    for course in courses:
        thisCourseSlot = coursesData[course]['slot']
        if(thisCourseSlot != ''):
            preAssigned.append(course)


def validate(slot, course, count, courseLimit, coursesData, slots):
    if count <= courseLimit:
        if coursesData[course]['faculty'] not in slots[slot]['faculty']:
            if coursesData[course]['semester'] not in slots[slot]['semester']:
                return True
            return False
        return False
    return False
