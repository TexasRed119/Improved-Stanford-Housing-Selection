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

TODO: We currently have not included room configurations in our ranking system (e.g. someone ranking a single in Crothers higher than a double in Toyon), but we will
'''
def generate_students(rooms_data, num_students, dorm_names, room_configurations, accomodations):
  students = []
  
  column_names = ["student_id", "year", "OAE"]
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
    r = random.randint(0,9)
    if (r <= 2): #for now set at 30% chance of having OAE, each type of OAE having equal probability of occuring
      q = random.randint(0,6)
      OAE_type = accomodations[q]
      current_student[2] = OAE_type
    else:
      current_student[2] = "None"
    
    '''
    Different way of things using boolean variables for each OAE ignore for now. 
    Left in case we want to use in future implementation or have no ceiling on number of OAE that one student can have

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

    #now do random ranking (can make this more nuanced later)
    #give suitable houses random order
    suitable_dorms_randomized = random.sample(suitable_dorms, len(suitable_dorms))
    #assign column with name suitable_dorms_randomized[i] with rank i+1 (rank will be 1-indexed)
    for j in range(len(suitable_dorms_randomized)):
      dorm = suitable_dorms_randomized[j]
      dorm_index = column_names.index(dorm)
      current_student[dorm_index] = j + 1

    students.append(current_student)
  
  return pd.DataFrame(data = students, columns = column_names)

df_students = generate_students(rooms_data, 90, dorm_names, room_configurations, accomodations)

print(df_students)
