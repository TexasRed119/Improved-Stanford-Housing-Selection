import random
import json
import numpy as np
import pandas as pd
from modified_srsd import modified_srsd
from modified_srsd_multipleOAE import multipleOAE_modified_srsd
import copy


with open('/Users/aryanguls/Desktop/Improved-Stanford-Housing-Selection/neighborhood_datasets/converted_aspen.json', 'r') as file:
    rooms_data = json.load(file)

rooms_data2 = copy.deepcopy(rooms_data)
dorm_names = rooms_data2.keys()
print(dorm_names)

#below taken from dataset.py
accomodations = [
    "ground_floor", "carpet_flooring", "wooden_flooring", "sink", "elevator_access", "braille_signage", "personal_kitchen", "None"
]

# dorm_names = [
#     "crothers_memorial", "faisan", "loro", "paloma", "gavilan", "cardenal",
#     "ng", "kimball", "adams", "potter", "suites", "adelfa", "meier", "norcliffe", "naranja",
#     "roble", "sally_ride", "twain", "toyon", "arroyo", "junipero", "trancos", "evgr_a", "mirrielees"
# ]

room_configurations = [
    "1-room single", "1-room double", "1-room triple", "1-room quad",
    "2-room double", "2-room triple", "2-room quad",
    "3-room double", "3-room triple", "3-room quad", "3-room quint"
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
        num_oae = random.choices([0, 1, 2], weights=[0.60, 0.25, 0.15])[0]
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

    # Function to assign students to rooms
    def assign_rooms(students, random_oae=False):
        for idx, student in students.iterrows():
            student_id = student['student_id']
            ranked_dorms = student['Rankings']
            oae_accommodations = student['OAE'].split(',') if student['OAE'] != "None" else []

            assigned = False

            if random_oae and oae_accommodations:
                # Randomly assign OAE students to a dorm that matches their accommodations
                matching_dorms = []
                for dorm, room_types in rooms_data.items():
                    for room_type, rooms in room_types.items():
                        for room in rooms:
                            if room['num_rooms'] > 0 and all(oae in room['facilities'] for oae in oae_accommodations):
                                matching_dorms.append((dorm, room_type, room))

                if matching_dorms:
                    dorm, room_type, room = random.choice(matching_dorms)
                    assignments[student_id] = (dorm, room_type)
                    room['num_rooms'] -= 1
                    assigned = True

            if not assigned:
                # Continue with regular assignment logic
                for dorm in ranked_dorms:
                    if dorm in rooms_data:
                        for room_type, rooms in rooms_data[dorm].items():
                            for room in rooms:
                                if room['num_rooms'] > 0: 
                                # and (not oae_accommodations or all(oae in room['facilities'] for oae in oae_accommodations)):
                                    assignments[student_id] = (dorm, room_type)
                                    room['num_rooms'] -= 1
                                    assigned = True
                                    break
                            if assigned:
                                break
                    if assigned:
                        break

                # Fallback to any available room if no preferred room is found
                if not assigned:
                    for dorm, room_types in rooms_data.items():
                        for room_type, rooms in room_types.items():
                            for room in rooms:
                                if room['num_rooms'] > 0:
                                    assignments[student_id] = (dorm, room_type)
                                    room['num_rooms'] -= 1
                                    assigned = True
                                    break
                            if assigned:
                                break
                        if assigned:
                            break

    # Process OAE students first with random assignment
    assign_rooms(df_students[df_students['OAE'] != "None"], random_oae=True)

    # Process non-OAE students
    assign_rooms(df_students[df_students['OAE'] == "None"])

    return assignments

df_students1 = generate_students(rooms_data, 1000, dorm_names, room_configurations, accomodations)
df_students2 = copy.deepcopy(df_students1)

# print(df_students)

# Example usage
# oae_threshold = 0.3  # Adjust the threshold as needed
year_priority = [4, 3, 2]  # Specify the year priority order

with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df_students1)

modified_assignments = multipleOAE_modified_srsd(df_students1, rooms_data, year_priority)
current_assignments = current_assignment_mech(df_students2, rooms_data2, year_priority)

def print_sorted_assignments(assignments, df_students):
    sorted_assignments = sorted(assignments.items())
    for student_id, (dorm, room_type) in sorted_assignments:
        print(f"Student {student_id}: {dorm} - {room_type}")

print("\nCurrent mech assignments (sorted by student ID):")
print_sorted_assignments(current_assignments, df_students2)

print("\nModified mech assignments (sorted by student ID):")
print_sorted_assignments(modified_assignments, df_students1)



def count_oae_students(assignments, df_students):
    oae_counts = {dorm: 0 for dorm in dorm_names}
    total_counts = {dorm: 0 for dorm in dorm_names}

    for student_id, (dorm, room) in assignments.items():
        total_counts[dorm] += 1
        if df_students.loc[df_students['student_id'] == student_id, 'OAE'].values[0] != "None":
            oae_counts[dorm] += 1

    oae_proportions = {dorm: (oae_counts[dorm] / total_counts[dorm]) if total_counts[dorm] > 0 else 0 for dorm in dorm_names}
    return oae_counts, total_counts, oae_proportions

# Calculate OAE student proportions
current_oae_counts, current_total_counts, current_oae_proportions = count_oae_students(current_assignments, df_students2)
modified_oae_counts, modified_total_counts, modified_oae_proportions = count_oae_students(modified_assignments, df_students1)

print("Current mech OAE proportions:")
for dorm in dorm_names:
    print(f"{dorm}: {current_oae_proportions[dorm]:.2f} ({current_oae_counts[dorm]}/{current_total_counts[dorm]})")

print("\nModified mech OAE proportions:")
for dorm in dorm_names:
    print(f"{dorm}: {modified_oae_proportions[dorm]:.2f} ({modified_oae_counts[dorm]}/{modified_total_counts[dorm]})")

def calculate_score(assignments, df_students): 
    
    scores = [0, 0, 0]

    for student_id, (dorm, room) in assignments.items():
        dorm_rank = list(df_students['Rankings'][student_id])
        print(dorm_rank)
        if dorm_rank == [] or dorm not in dorm_rank:
            student_score = 0
        else:
            student_score = 1 / (1 + dorm_rank.index(dorm))
        scores[0] += student_score
        if df_students.loc[df_students['student_id'] == student_id, 'OAE'].values[0] != "None":
            scores[1] += student_score
        else:
            scores[2] += student_score
        
        # for index in range(len(scores)):
        #     scores[index] = scores[index] / len(assignments)
    
    
    return scores

current_score = calculate_score(current_assignments, df_students2)
modified_score = calculate_score(modified_assignments, df_students1)

print(f'Current mech score: {current_score} \nModified mech score : {modified_score}')