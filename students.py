import random
import json
import numpy as np
import pandas as pd

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

  column_names = ["student_id", "year", "OAE", "Assignment"]
  for dorm in dorm_names:
    column_names.append(dorm)

  for i in range(num_students):
    current_student = [None for u in range(len(column_names))]

    #student id
    current_student[0] = i

    #student upcoming year at stanford
    year = random.randint(2,4)
    current_student[1] = year

    #OAE type
    #can add more columns for multiple OAE in future (e.g. "OAE_1", "OAE_2") and repeat process below
    #TODO: multiple OAEs
    r = random.randint(1,10)
    if (r <= 2): #for now set at 20% chance of having OAE, each type of OAE having equal probability of occuring
      q = random.randint(0,6)
      OAE_type = accomodations[q]
      current_student[2] = OAE_type
    else:
      current_student[2] = "None"

    '''
    Different way of things I tried, ignore for now. Left in case we want to use in future implementation

    #below for loop randomly generates OAE accommodation types for current student
    #note: we are currently capping # of OAE accomodations at 1 for now, will likely change and become more possible complex combinations of OAE types
    num_OAE = 0
    for oae in accomodations:
      if (oae is not "None"): #not including "None" since would be perfectly collinear with all other OAE booleans being False"
        column_names.append(oae)
        if (num_OAE == 0):
          r = random.randint(0, 19) # 20 possible outcomes
          if (r == 0): #give 5% chance of having each OAE type, with 7 different types (currently) results in probability of student having an OAE at 35%
            current_student.append(True)
            num_OAE += 1
          else:
            current_student.append(False)
        else:
          current_student.append(False)
    '''

    #dorm rankings, first finding dorms that are suitable (i.e. must have facilties for accomodation of student)
    suitable_dorms = []
    for dorm in dorm_names:
      if dorm in rooms_data:
        if current_student[2] == "None": #student has no OAE
          suitable_dorms.append(dorm)
        else: #student does have an OAE
          for room in room_configurations:
            if room in rooms_data[dorm]:
              for k in range(len(rooms_data[dorm][room])):
                if current_student[2] in rooms_data[dorm][room][k]["facilities"]:  #would need to change index of current_student based on implementation above
                  suitable_dorms.append(dorm)
                  break
              break

    #now do random ranking TODO: more popular housing would be ranked higher (could make system based off of amenities provided, or do subjective ranking system for now)
    #assign each house random ranking
    suitable_dorms_randomized = random.sample(suitable_dorms, len(suitable_dorms))
    #assign column with name suitable_dorms_randomized[i] with rank i+1 (rank will be 1-indexed)
    for j in range(len(suitable_dorms_randomized)):
      dorm = suitable_dorms_randomized[j]
      dorm_index = column_names.index(dorm)
      current_student[dorm_index] = j + 1

    students.append(current_student)

  return pd.DataFrame(data = students, columns = column_names)


'''
serial dictatorship modeling current housing mechanism employed by stanford
'''
def current_assignment_mech(df_students, assignment_data):
  #shuffle dataframe of students (this isn't really neccessary per se since data was random to begin with, but we will do for now anyways, may help when we incorporate houing groups later)
  df_students = df_students.sample(frac = 1).reset_index(drop=True)


  #assign OAE students first for control/current system
  #OAE assumption system for current assignment: 50% get first assignment, 50% get second
  for year in range(4, 1, -1):
    df_year = df_students.loc[df_students["year"] == year].reset_index(drop=True)
    for i in range(len(df_year.index)):
      student = df_year.loc[i,:]
      if student['OAE'] != "None":
        OAE = student['OAE']
        r = random.randint(1,4)
        #assign to top choice 50% of time (assumption for now)
        assigned = False
        k = 1
        #TODO: what if only available choice for OAE is 1st choice? below starting at 2nd choice will cause bug. add clause to if statement? or maybe add something to for loop that loops back to 1 if no others after all options exhausted
        if r > 2:
          k = 2
        #TODO: does below need to be changed to reflect when rank k choice doesn't exist to prevent out-of-bounds error? (this shouldn't occur ever tho, everyone can be assigned based on nature of system)
        while assigned == False:
          top_choice = student[student == k].index[-1]
          #note that the below will look different when we incorporate room configurations in rankings
          for room_type in assignment_data[top_choice]:
            for j in range(len(assignment_data[top_choice][room_type])):
              if OAE in assignment_data[top_choice][room_type][j]['facilities']:
                if assignment_data[top_choice][room_type][j]['num_rooms'] > 0:
                  df_students.loc[df_students['student_id'] == student['student_id'], "Assignment"] = top_choice
                  assignment_data[top_choice][room_type][j]['num_rooms'] = assignment_data[top_choice][room_type][j]['num_rooms'] - 1
                  assigned = True
                  break
          k += 1

  #now traverse and assign through each year, starting with seniors
  for year in range(4, 1, -1):
    df_year = df_students.loc[df_students["year"] == year].reset_index(drop=True)
    for i in range(len(df_year.index)):
      student = df_year.loc[i,:]
      if student['OAE'] == "None": #non-OAE students only, OAE already assigned
        assigned = False
        k = 1
        while assigned == False: #TODO: does this need to be changed to reflect when rank k choice doesn't exist to prevent out-of-bounds error? (this shouldn't occur ever tho, everyone can be assigned based on nature of system)
          top_choice = student[student == k].index[-1]
          #note that the below will look different when we incorporate room configurations in rankings
          for room_type in assignment_data[top_choice]:
            for j in range(len(assignment_data[top_choice][room_type])):
              if assignment_data[top_choice][room_type][j]['num_rooms'] > 0:
                df_students.loc[df_students['student_id'] == student['student_id'], "Assignment"] = top_choice
                assignment_data[top_choice][room_type][j]['num_rooms'] = assignment_data[top_choice][room_type][j]['num_rooms'] - 1
                assigned = True
                break
          k += 1

  return df_students, assignment_data

df_students = generate_students(rooms_data, 90, dorm_names, room_configurations, accomodations)

#make copy of rooms_data
#TODO: could just reload the json each time? or should we make function that creates copy?
with open('original.json', 'r') as file:
    assignment_data = json.load(file)

df_assignments_current, assignment_data = current_assignment_mech(df_students, assignment_data)

print(df_assignments_current)
