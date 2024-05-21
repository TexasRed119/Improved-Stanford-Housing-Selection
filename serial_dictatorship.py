# This file is basic serial dictatorship 

import json

# Load JSON data from a file
with open('neighborhood_datasets/gingko.json', 'r') as file:
    housing_data = json.load(file)

# Example list of students and their required amenities in priority order
students = [
    {"name": "Student1", "required_amenities": ["ground_floor", "braille_signage"]},
    {"name": "Student2", "required_amenities": ["elevator_access"]},
    {"name": "Student3", "required_amenities": ["sink", "personal_kitchen"]},
]

def find_room(buildings, required_amenities):
    for building, data in buildings.items():
        if "Spaces in Apartment Style Units" in data:
            for unit_type, units in data["Spaces in Apartment Style Units"].items():
                for unit in units:
                    if all(amenity in unit["Amenities"] for amenity in required_amenities) and unit["Count"] > 0:
                        unit["Count"] -= 1
                        return (building, unit_type, unit["Amenities"])
        if "Spaces in Residence Halls and Row Houses" in data:
            for unit_type, units in data["Spaces in Residence Halls and Row Houses"].items():
                for unit in units:
                    if all(amenity in unit["Amenities"] for amenity in required_amenities) and unit["Count"] > 0:
                        unit["Count"] -= 1
                        return (building, unit_type, unit["Amenities"])
    return None

# Perform the serial dictatorship assignment
def serial_dictatorship_assignments(housing_data, students):
    assignments = {}
    for student in students:
        result = find_room(housing_data["Ginkgo"], student["required_amenities"])
        if result:
            assignments[student["name"]] = {
                "Building": result[0],
                "Unit Type": result[1],
                "Amenities": result[2]
            }
        else:
            assignments[student["name"]] = "No suitable room available"
    return assignments

# Run the assignment
assignments = serial_dictatorship_assignments(housing_data, students)

# Print the results
print(json.dumps(assignments, indent=2))
