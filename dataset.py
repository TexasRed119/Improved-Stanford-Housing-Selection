'''
- Only Considering dorms that are Upperclassman or 4-class since freshman are placed into freshmans dorms by random selection
and the only time we fill out OAE forms in the current system is sophomore year onwards
- Also not considering theme house since they have a different application process and do not fit into the OAE process

Crothers Hall - Crothers Memorial
Florence Moore - Faisan,  Loro, Paloma, Gavilan, Cardenal,  
Gerhard Casper Quad - Ng, Kimball
Governor's Corner – Adams, Potter, Suites
Lagunita Court - Adelfa, Meier, Norcliffe, Naranja
Roble Hall - Roble
Stern Hall - Sally Ride, Twain
Toyon Hall - Toyon
Wilbur Hall - Arroyo, Junipero, Trancos
EVGR - EVGR-A
Mirrielees - Mirrielees
'''
dorm_names = [
    "crothers_memorial", "faisan", "loro", "paloma", "gavilan", "cardenal", 
    "ng", "kimball", "adams", "potter", "suites", "adelfa", "meier", "norcliffe", "naranja", 
    "roble", "sally_ride", "twain", "toyon", "arroyo", "junipero", "trancos", "evgr_a", "mirrielees"
]

'''
- Room configurations on campus according to R&DE
'''
room_configurations = [
    "1-room single", "1-room double", "1-room triple", "1-room quad", 
    "2-room double", "2-room triple", "2-room quad", 
    "3-room double", "3-room triple", "3-room quad"
]

'''
- Specifications/facilities present in rooms that may fit an OAE requirement
'''
facilities = [
    "ground_floor", "carpet_flooring", "wooden_flooring", "sink", "elevator_access", "braille_signage", "personal_kitchen", "None"
] 

import random
import json

def distribute_rooms(num_dorms, total_rooms):
    rooms_per_dorm = [1] * num_dorms
    for _ in range(total_rooms - num_dorms):
        rooms_per_dorm[random.randint(0, num_dorms-1)] += 1
    print(sum(rooms_per_dorm))
    return rooms_per_dorm

def generate_and_update_dataset(num_dorms, total_rooms, file_path):
    try:
        with open(file_path, 'r') as file:
            original_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        original_data = {}

    selected_dorms = random.sample(dorm_names, num_dorms)
    rooms_distribution = distribute_rooms(num_dorms, total_rooms)
    new_data = {}
    
    for dorm, num_rooms in zip(selected_dorms, rooms_distribution):
        dorm_data = {}
        remaining_rooms = num_rooms
        
        while remaining_rooms > 0:
            selected_room_types = random.sample(room_configurations, random.randint(1, min(4, len(room_configurations))))
            for room_type in selected_room_types:
                if remaining_rooms <= 0:
                    break
                room_type_list = dorm_data.get(room_type, [])
                used_empty_facilities = False
                
                num_configurations = 1 if remaining_rooms == 1 else random.randint(1, min(remaining_rooms, 3))
                
                for _ in range(num_configurations):
                    if remaining_rooms <= 0:
                        break
                    num_facility_groups = random.randint(0, len(facilities) - 1)
                    if num_facility_groups == 0 and not used_empty_facilities:
                        selected_facilities = []
                        used_empty_facilities = True
                    elif num_facility_groups == 0 and used_empty_facilities:
                        continue
                    else:
                        selected_facilities = random.sample(facilities, num_facility_groups)
                    
                    room_count = remaining_rooms if _ == num_configurations - 1 else random.randint(1, remaining_rooms // num_configurations)
                    if "None" in selected_facilities:
                        selected_facilities.remove("None")
                    facilities_data = {
                        "facilities": selected_facilities,
                        "num_rooms": room_count
                    }
                    room_type_list.append(facilities_data)
                    remaining_rooms -= room_count
                dorm_data[room_type] = room_type_list
        
        new_data[dorm] = dorm_data

    with open(file_path, 'w') as file:
        json.dump(original_data, file, indent=4)

generate_and_update_dataset(4, 100, 'original.json')


with open('original.json', 'r') as file:
    data = json.load(file)
# Calculate the sum of all num_rooms across all dorms and room configurations.
total_rooms = sum(
    sum(room_info["num_rooms"] for room_info in room_list)
    for dorm_rooms in data.values()
    for room_list in dorm_rooms.values()
)
print(total_rooms)