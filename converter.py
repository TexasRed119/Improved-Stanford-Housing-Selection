#converts the data to the original.json format to make it easy for us to work with 

import json

# Load JSON data from a file
with open('neighborhood_datasets/gingko.json', 'r') as file:
    data = json.load(file)

# Function to convert JSON format
def convert_json_format(data):
    new_data = {}
    
    for dorm, details in data.items():
        new_data[dorm.lower()] = {}
        
        spaces = {**details.get("Spaces in Apartment Style Units", {}), **details.get("Spaces in Residence Halls and Row Houses", {})}
        
        for space_type, space_details in spaces.items():
            new_space_type = space_type.replace(" ", "-").replace("BR", "room").replace("Double", "double").replace("Triple", "triple").replace("Quad", "quad")
            
            if new_space_type not in new_data[dorm.lower()]:
                new_data[dorm.lower()][new_space_type] = []
            
            for space in space_details:
                new_data[dorm.lower()][new_space_type].append({
                    "facilities": space["Amenities"],
                    "num_rooms": space["Count"]
                })
    
    return new_data

# Convert the JSON data
converted_data = convert_json_format(data["Ginkgo"])

# Print the converted JSON data
print(json.dumps(converted_data, indent=4))
