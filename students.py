import random
import json
import numpy as np
import pandas as pd
from modified_srsd import modified_srsd
from modified_srsd_multipleOAE import multipleOAE_modified_srsd


with open('original.json', 'r') as file:
    rooms_data = json.load(file)

#below taken from dataset.py
accomodations = [
    "ground_floor", "carpet_flooring", "wooden_flooring", "sink", "elevator_access", "braille_signage", "personal_kitchen", "None"
]

dorm_names = [
    "crothers_memorial", "faisan", "loro", "paloma", "gavilan", "cardenal",
    "ng", "kimball", "adams", "potter", "suites", "adelfa", "meier", "norcliffe", "naranja",
    "roble", "sally_ride", "twain", "toyon", "arroyo", "junipero", "trancos", "evgr_a", "mirrielees"
]

room_configurations = [
    "1-room single", "1-room double", "1-room triple", "1-room quad",
    "2-room double", "2-room triple", "2-room quad",
    "3-room double", "3-room triple", "3-room quad"
]


'''
generates synthetic data (pandas dataframe) of rankings and accomodations for certain (num_students) amount of students.
Currently done without housing groups (we will likely change this).
columns of dataframe include:
- an assigned student id
- OAE accomation type
- a 'year' variable corresponding to the students upcoming year in school. Freshman will be exluded for now, since most are randomly assigned in different process
- a ranking number for each house/dormitory

TODO: housing groups
TODO: neighborhoods (and housing groups is conditioned on this)
TODO: We currently have not included room configurations in our ranking system (e.g. someone ranking a single in Crothers higher than a double in Toyon), but we will
TODO: how to watch for room configurations and housing groups (how does this work?)
'''
def generate_students(rooms_data, num_students, dorm_names, room_configurations, accomodations):
    students = []
    column_names = ["student_id", "year", "OAE", "Assignment", "Rankings"]
    column_names.extend(dorm_names)

    for i in range(num_students):
        current_student = [None for u in range(len(column_names))]

        # student id
        current_student[0] = i

        # student upcoming year at stanford
        year = random.randint(2, 4)
        current_student[1] = year

        # OAE accommodations
        num_oae = random.choices([0, 1, 2], weights=[0.6, 0.25, 0.15])[0]
        oae_accommodations = random.sample(accomodations[:-1], num_oae)
        current_student[2] = ",".join(oae_accommodations) if num_oae > 0 else "None"

        # dorm rankings
        suitable_dorms = []
        for dorm in dorm_names:
            if dorm in rooms_data:
                if current_student[2] == "None":  # student has no OAE
                    suitable_dorms.append(dorm)
                else:  # student has OAE accommodations
                    for room in room_configurations:
                        if room in rooms_data[dorm]:
                            for k in range(len(rooms_data[dorm][room])):
                                if all(oae in rooms_data[dorm][room][k]["facilities"] for oae in oae_accommodations):
                                    suitable_dorms.append(dorm)
                                    break
                        if dorm in suitable_dorms:
                            break

        # Generate rankings for suitable dorms
        rankings = {}
        for dorm in suitable_dorms:
            rankings[dorm] = random.randint(1, len(suitable_dorms))

        # Sort the rankings based on the values
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])

        # Create a list of ranked dorms
        ranked_dorms = [dorm for dorm, _ in sorted_rankings]

        # Assign the ranked dorms to the current student
        current_student[4] = ranked_dorms

        # Populate the individual dorm ranking columns
        for dorm in dorm_names:
            if dorm in ranked_dorms:
                dorm_index = column_names.index(dorm)
                current_student[dorm_index] = ranked_dorms.index(dorm) + 1
            else:
                dorm_index = column_names.index(dorm)
                current_student[dorm_index] = None

        students.append(current_student)

    return pd.DataFrame(data=students, columns=column_names)


'''
serial dictatorship modeling current housing mechanism employed by stanford
'''
def current_assignment_mech(df_students, rooms_data, year_priority):
    # Shuffle dataframe of students
    df_students = df_students.sample(frac=1).reset_index(drop=True)

    # Sort students based on the specified year priority
    df_students['year_priority'] = df_students['year'].map(lambda x: year_priority.index(x))
    df_students.sort_values(by=['year_priority', 'student_id'], inplace=True)

    # Initialize variables to store the housing assignments
    assignments = {}

    # Assign OAE students first for control/current system
    # OAE assumption system for current assignment: 50% get first assignment, 50% get second
    for _, student in df_students[df_students['OAE'] != "None"].iterrows():
        student_id = student['student_id']
        oae_accommodations = student['OAE'].split(',')
        ranked_dorms = student['Rankings']
        r = random.randint(1, 4)
        # Assign to top choice 50% of time (assumption for now)
        if r > 2:
            ranked_dorms = ranked_dorms[1:]  # Remove the first choice

        assigned = False
        for dorm in ranked_dorms:
            if dorm in rooms_data:
                for room_type in rooms_data[dorm]:
                    for j in range(len(rooms_data[dorm][room_type])):
                        if all(oae in rooms_data[dorm][room_type][j]['facilities'] for oae in oae_accommodations):
                            if rooms_data[dorm][room_type][j]['num_rooms'] > 0:
                                assignments[student_id] = (dorm, room_type)
                                rooms_data[dorm][room_type][j]['num_rooms'] -= 1
                                assigned = True
                                break
                    if assigned:
                        break
            if assigned:
                break
        if not assigned:
            # If no suitable room found, assign to any available room
            for dorm in rooms_data:
                for room_type in rooms_data[dorm]:
                    for j in range(len(rooms_data[dorm][room_type])):
                        if rooms_data[dorm][room_type][j]['num_rooms'] > 0:
                            assignments[student_id] = (dorm, room_type)
                            rooms_data[dorm][room_type][j]['num_rooms'] -= 1
                            assigned = True
                            break
                    if assigned:
                        break
                if assigned:
                    break

    # Now traverse and assign through each year, based on the year priority
    for _, student in df_students[df_students['OAE'] == "None"].iterrows():
        student_id = student['student_id']
        ranked_dorms = student['Rankings']
        assigned = False
        for dorm in ranked_dorms:
            if dorm in rooms_data:
                for room_type in rooms_data[dorm]:
                    for j in range(len(rooms_data[dorm][room_type])):
                        if rooms_data[dorm][room_type][j]['num_rooms'] > 0:
                            assignments[student_id] = (dorm, room_type)
                            rooms_data[dorm][room_type][j]['num_rooms'] -= 1
                            assigned = True
                            break
                    if assigned:
                        break
            if assigned:
                break
        if not assigned:
            # If no suitable room found, assign to any available room
            for dorm in rooms_data:
                for room_type in rooms_data[dorm]:
                    for j in range(len(rooms_data[dorm][room_type])):
                        if rooms_data[dorm][room_type][j]['num_rooms'] > 0:
                            assignments[student_id] = (dorm, room_type)
                            rooms_data[dorm][room_type][j]['num_rooms'] -= 1
                            assigned = True
                            break
                    if assigned:
                        break
                if assigned:
                    break

    return assignments

df_students = generate_students(rooms_data, 90, dorm_names, room_configurations, accomodations)

# print(df_students)

# Example usage
# oae_threshold = 0.3  # Adjust the threshold as needed
year_priority = [4, 3, 2]  # Specify the year priority order

modified_assignments = multipleOAE_modified_srsd(df_students, rooms_data, year_priority)
current_assignments = current_assignment_mech(df_students, rooms_data, year_priority)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df_students)

print("Current mech:")
for student_id, (dorm, room) in current_assignments.items():
    print(f"Student {student_id}: {dorm} - {room}")

print("Modified mech:")
for student_id, (dorm, room) in modified_assignments.items():
    print(f"Student {student_id}: {dorm} - {room}")


