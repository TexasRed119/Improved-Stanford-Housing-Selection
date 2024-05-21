import random
import json
import numpy as np
import pandas as pd
import math

with open('original.json', 'r') as file:
    rooms_data = json.load(file)

# Below taken from dataset.py
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