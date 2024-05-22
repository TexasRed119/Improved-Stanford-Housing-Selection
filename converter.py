import json

# Load JSON data from a file
with open('neighborhood_datasets/wisteria.json', 'r') as file:
    data = json.load(file)

# Define room configuration mappings
room_configurations = {
    "Single Spaces": "1-room single",
    "Studio Double Spaces": "1-room double",
    "1-room Single": "1-room single",
    "1-room Double": "1-room double",
    "1-room Triple": "1-room triple",
    "1-room Quad": "1-room quad",
    "2BR Double Spaces": "2-room double",
    "2BR Triple Spaces": "2-room triple",
    "3BR Triple Spaces": "3-room triple",
    "1-room Double Spaces": "1-room double",
    "1-room Triple Spaces": "1-room triple",
    "1-room Quad Spaces": "1-room quad",
    "2-room Double Spaces": "2-room double",
    "2-room Triple Spaces": "2-room triple",
    "3-room Double Spaces": "3-room double",
    "3-room Triple Spaces": "3-room triple",
    "3-room Quad Spaces": "3-room quad",
    "3-room Quint Spaces": "3-room quint",
    "3-person Suite Spaces": "1-room single",
    "4-person Suite Spaces": "1-room single",
    "6-person Suite Spaces": "1-room single",
    "8-person Suite Spaces": "1-room single"
}

# Function to convert JSON format
def convert_json_format(data):
    new_data = {}
    
    for dorm, details in data.items():
        new_data[dorm.lower()] = {}
        
        spaces = {**details.get("Spaces in Apartment Style Units", {}), **details.get("Spaces in Residence Halls and Row Houses", {})}
        
        for space_type, space_details in spaces.items():
            # Map the space type to the new configuration name
            new_space_type = room_configurations.get(space_type, space_type).lower()
            
            if new_space_type not in new_data[dorm.lower()]:
                new_data[dorm.lower()][new_space_type] = []
            
            for space in space_details:
                new_data[dorm.lower()][new_space_type].append({
                    "facilities": space["Amenities"],
                    "num_rooms": space["Count"]
                })
    
    return new_data

# Convert the JSON data
converted_data = convert_json_format(data["Wisteria"])

# Save the converted JSON data to a new file
with open('neighborhood_datasets/converted_wisteria.json', 'w') as outfile:
    json.dump(converted_data, outfile, indent=4)

print("Data has been successfully converted and saved to 'neighborhood_datasets/converted_gingko.json'")
