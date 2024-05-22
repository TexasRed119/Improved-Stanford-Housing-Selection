import random
import json
import numpy as np
import pandas as pd
import copy

with open('neighborhood_datasets/converted_aspen.json', 'r') as file:
    rooms_data = json.load(file)

rooms_data2 = copy.deepcopy(rooms_data)

# List of accommodations and dorm names from the JSON data
accomodations = [
    "ground_floor", "carpet_flooring", "wooden_flooring", "sink", "elevator_access", "braille_signage", "personal_kitchen"
]

# Extract dorm names from JSON data
dorm_names = list(rooms_data.keys())
print(dorm_names)

room_configurations = [
    "1-room single", "1-room double", "1-room triple", "1-room quad",
    "2-room double", "2-room triple", "2-room quad",
    "3-room double", "3-room triple", "3-room quad", "3-room quint"
]

def generate_students(rooms_data, num_students, dorm_names, room_configurations, accomodations):
    students = []
    column_names = ["student_id", "year", "OAE", "Assignment", "Rankings"]
    column_names.extend(dorm_names)

    for i in range(num_students):
        current_student = [None for _ in range(len(column_names))]

        # student id
        current_student[0] = i

        # student upcoming year at Stanford
        year = random.randint(2, 4)
        current_student[1] = year

        # OAE accommodations
        num_oae = random.choices([0, 1, 2], weights=[0.65, 0.25, 0.10])[0]
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


def calculate_popularity(students_df):
    popularity = {dorm: 0 for dorm in dorm_names}
    for dorm in dorm_names:
        # Calculate popularity based on inverse of ranking
        popularity[dorm] = students_df[dorm].apply(lambda x: 1 / x if x is not None else 0).sum()
    return popularity

def assign_oae_thresholds(popularity, total_oae_rooms, higher_threshold_for_popular=True):
    total_popularity = sum(popularity.values())
    oae_thresholds = {}
    for dorm, pop in popularity.items():
        proportion = pop / total_popularity
        if higher_threshold_for_popular:
            oae_thresholds[dorm] = math.ceil(total_oae_rooms * proportion)
        else:
            oae_thresholds[dorm] = math.ceil(total_oae_rooms * (1 - proportion))
    return oae_thresholds


def multipleOAE_modified_srsd(students_df, rooms_data, year_priority, higher_threshold_for_popular=True):
    # Sort students based on the specified year priority (e.g., [4, 3, 2])
    students_df['year_priority'] = students_df['year'].map(lambda x: year_priority.index(x))
    students_df.sort_values(by=['year_priority', 'student_id'], inplace=True)

    # Initialize variables to store the housing assignments
    assignments = {}

    # Calculate the number of rooms available for OAE students based on the number of OAE students
    total_rooms = sum(sum(room["num_rooms"] for room_type in dorm.values() for room in room_type) for dorm in rooms_data.values())
    oae_students = students_df[students_df['OAE'] != 'None']
    oae_threshold = len(oae_students) / len(students_df) 
    # oae_threshold = 0.3
    oae_rooms = math.ceil(total_rooms * oae_threshold) + 1

    popularity = calculate_popularity(students_df)
    oae_thresholds = assign_oae_thresholds(popularity, oae_rooms, higher_threshold_for_popular)

    # Iterate over each student in the sorted order
    for _, student in students_df.iterrows():
        student_id = student['student_id']
        oae_accommodations = student['OAE'].split(',') if student['OAE'] != 'None' else []

        # Check if the student has OAE accommodations and if there are available OAE rooms
        if oae_accommodations and oae_rooms > 0:
            # Find the highest-ranked dorm that meets all the OAE requirements
            for dorm in student[dorm_names].sort_values().index:
                if dorm in rooms_data and oae_thresholds[dorm] > 0:
                    for room_type in rooms_data[dorm]:
                        for room in rooms_data[dorm][room_type]:
                            if all(oae in room["facilities"] for oae in oae_accommodations):
                                # Check if the room has available slots
                                if room["num_rooms"] > 0:
                                    # Assign the student to the room
                                    assignments[student_id] = (dorm, room_type)
                                    room["num_rooms"] -= 1
                                    oae_rooms -= 1
                                    oae_thresholds[dorm] -= 1
                                    break
                        if student_id in assignments:
                            break
                if student_id in assignments:
                    break
        else:
            # Find the highest-ranked dorm with available rooms
            for dorm in student[dorm_names].sort_values().index:
                if dorm in rooms_data:
                    for room_type in rooms_data[dorm]:
                        for room in rooms_data[dorm][room_type]:
                            # Check if the room has available slots
                            if room["num_rooms"] > 0:
                                # Assign the student to the room
                                assignments[student_id] = (dorm, room_type)
                                room["num_rooms"] -= 1
                                break
                        if student_id in assignments:
                            break
                if student_id in assignments:
                    break

    return assignments



def current_assignment_mech(df_students, rooms_data, year_priority):
    df_students = df_students.sample(frac=1).reset_index(drop=True)
    df_students['year_priority'] = df_students['year'].map(lambda x: year_priority.index(x))
    df_students.sort_values(by=['year_priority', 'student_id'], inplace=True)

    assignments = {}

    def assign_rooms(students, random_oae=False):
        for idx, student in students.iterrows():
            student_id = student['student_id']
            ranked_dorms = student['Rankings']
            oae_accommodations = student['OAE'].split(',') if student['OAE'] != "None" else []

            assigned = False

            if random_oae and oae_accommodations:
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
                for dorm in ranked_dorms:
                    if dorm in rooms_data:
                        for room_type, rooms in rooms_data[dorm].items():
                            for room in rooms:
                                if room['num_rooms'] > 0 and (not oae_accommodations or all(oae in room['facilities'] for oae in oae_accommodations)):
                                    assignments[student_id] = (dorm, room_type)
                                    room['num_rooms'] -= 1
                                    assigned = True
                                    break
                            if assigned:
                                break
                    if assigned:
                        break

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

    assign_rooms(df_students[df_students['OAE'] != "None"], random_oae=True)
    assign_rooms(df_students[df_students['OAE'] == "None"])

    return assignments

df_students1 = generate_students(rooms_data, 1200, dorm_names, room_configurations, accomodations)
df_students2 = copy.deepcopy(df_students1)

year_priority = [4, 3, 2]

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df_students1)

# Assume the functions `multipleOAE_modified_srsd` and `modified_srsd` are correctly defined elsewhere
# modified_assignments = multipleOAE_modified_srsd(df_students1, rooms_data, year_priority)
# For demonstration, we will use the current_assignment_mech function instead of the missing `multipleOAE_modified_srsd`
modified_assignments = current_assignment_mech(df_students1, rooms_data, year_priority)
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
        dorm_rank = df_students.loc[df_students['student_id'] == student_id, 'Rankings'].values[0]
        if dorm in dorm_rank:
            student_score = 5 - dorm_rank.index(dorm)
        else:
            student_score = 0
        scores[0] += student_score
        if df_students.loc[df_students['student_id'] == student_id, 'OAE'].values[0] != "None":
            scores[1] += student_score
        else:
            scores[2] += student_score
            
    return scores

current_score = calculate_score(current_assignments, df_students2)
modified_score = calculate_score(modified_assignments, df_students1)

print(f'Current mech score: {current_score} \nModified mech score : {modified_score}')
