import json

with open('neighborhood_datasets/converted_aspen.json', 'r') as file:
    data = json.load(file)

multipliers = {
    "single": 1,
    "double": 2,
    "triple": 3,
    "quad": 4,
    "quint": 5
}

def calculate_total_spaces(data):
    total_spaces = 0
    
    for dorm, room_types in data.items():
        for room_type, rooms in room_types.items():
            room_type_split = room_type.split(' ')
            last_word = room_type_split[-1]
            if last_word in multipliers:
                multiplier = multipliers[last_word]
                for room in rooms:
                    total_spaces += room['num_rooms']
    
    return total_spaces

# Calculate total spaces
total_spaces = calculate_total_spaces(data)
print("Total number of spaces:", total_spaces)


# set the student number to that exact number 


# find the number of rooms of each type we have 