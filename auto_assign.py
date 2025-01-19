###
### PROTOTYPE
### Activity Assignment Algorithm (AAA) v1.1.0
### Derek Zhang (https://github.com/fillorkill)
### Last updated: 2024/12/12
###

import csv
import networkx as nx
import argparse

PREFERENCE_WEIGHTS = {'1st': 0, '2nd': 1, '3rd': 2}
DAYS = frozenset(['mon', 'tue', 'wed', 'thu']) 

STUDENT_WEIGHTS = {
    'high': 1,      # Will be assigned first
    'medium': 100,  # Will be assigned second
    'low': 1000    # Will be assigned last
}

def load_student_preferences(csv_file):
    preferences = {} 
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_id = row['student_id']
                if student_id not in preferences:
                    preferences[student_id] = {
                        'weight': row.get('priority', 'medium'),  # Default to medium if not specified
                        'days': {}
                    }
                
                day = row['day'].strip().lower()
                preferences[student_id]['days'][day] = {
                    '1st_preference': row['1st_preference'].strip(),
                    '2nd_preference': row['2nd_preference'].strip(),
                    '3rd_preference': row['3rd_preference'].strip(),
                }
        print(f"Loaded {len(preferences)} student preferences.")
    except Exception as e:
        print(f"Error loading CSV file: {e}")
    return preferences

# assign 15 as the maximum capacity per activity per day as a test, can be assigned individually in a real scenario 
def build_flow_network(preferences, days, max_capacity_per_activity=15):
    G = nx.DiGraph()
    
    G.add_node('source')
    G.add_node('sink')

    activities_by_day = {day: set() for day in days}
    for student_prefs in preferences.values():
        for day, prefs in student_prefs['days'].items():
            activities_by_day[day].update([
                prefs['1st_preference'],
                prefs['2nd_preference'],
                prefs['3rd_preference']
            ])

    # Modified to give strict priority based on student weights
    for student_id, student_data in preferences.items():
        student_weight = STUDENT_WEIGHTS[student_data['weight']]
        for day, prefs in student_data['days'].items():
            student_day_node = f"{student_id}_{day}"
            G.add_edge('source', student_day_node, capacity=1, weight=0)
            
            for pref_type, activity in prefs.items():
                # Base weight from preference order
                base_weight = PREFERENCE_WEIGHTS[pref_type.split('_')[0]]
                # Multiply by student priority weight to ensure strict ordering
                edge_weight = base_weight + student_weight
                G.add_edge(
                    student_day_node,
                    f"{day}_{activity}",
                    capacity=1,
                    weight=edge_weight
                )

    for day, activities in activities_by_day.items():
        for activity in activities:
            G.add_edge(f"{day}_{activity}", 'sink', capacity=max_capacity_per_activity, weight=0)

    print(f"Flow network created with {len(G.nodes)} nodes and {len(G.edges)} edges.")
    print(f"Source node connections: {len(G['source'])}")
    print(f"Sink node connections: {len(G.in_edges('sink'))}")
    return G

def assign_priority_group(priority_students, label, activity_capacity):
    group_assignments = {}
    
    # Try each preference level in order
    for pref_level in ['1st', '2nd', '3rd']:
        print(f"  Trying {pref_level} preferences for {label} priority...")
        
        # Create network for current preference level
        G_pref = create_priority_network(priority_students, activity_capacity, pref_level)
        
        try:
            # Find maximum flow
            flow_dict = nx.maximum_flow(G_pref, 'source', 'sink')[1]
            
            # Process assignments from flow
            for node, flows in flow_dict.items():
                if node != 'source' and '_' in node:
                    student_id, day = node.split('_')
                    if student_id.startswith('S'):  # Only process student nodes
                        for target, flow in flows.items():
                            if flow > 0 and target != 'sink':
                                _, activity = target.split('_', 1)
                                if student_id not in group_assignments:
                                    group_assignments[student_id] = {}
                                if day not in group_assignments[student_id]:
                                    group_assignments[student_id][day] = activity
                                    activity_capacity[day][activity] -= 1
            
        except Exception as e:
            print(f"  Error in {pref_level} preference assignment: {e}")
            continue
            
    return group_assignments

def create_priority_network(priority_students, remaining_capacity, pref_level='1st'):
    G = nx.DiGraph()
    G.add_node('source')
    G.add_node('sink')
    
    # Add student nodes and their preferences
    for student_id, student_data in priority_students.items():
        for day, prefs in student_data['days'].items():
            student_day_node = f"{student_id}_{day}"
            G.add_edge('source', student_day_node, capacity=1, weight=0)
            
            # Add edges for the current preference level
            activity = prefs[f'{pref_level}_preference']
            if remaining_capacity[day][activity] > 0:
                G.add_edge(
                    student_day_node, 
                    f"{day}_{activity}", 
                    capacity=1, 
                    weight=0
                )

            # Add sink edges
            G.add_edge(
                f"{day}_{activity}", 
                'sink', 
                capacity=remaining_capacity[day][activity], 
                weight=0
            )
        
    return G

def assign_students_to_activities(G, preferences):
    try:
        # Split students by priority
        high_priority = {sid: data for sid, data in preferences.items() if data['weight'] == 'high'}
        medium_priority = {sid: data for sid, data in preferences.items() if data['weight'] == 'medium'}
        low_priority = {sid: data for sid, data in preferences.items() if data['weight'] == 'low'}
        
        assignments = {}
        activity_capacity = {day: {} for day in DAYS}

        # Initialize activity capacities
        for day in DAYS:
            for _, student_data in preferences.items():
                for activity in student_data['days'][day].values():
                    if activity not in activity_capacity[day]:
                        activity_capacity[day][activity] = 15  # max capacity

        # Process each priority level
        for priority_group, label in [
            (high_priority, "high"),
            (medium_priority, "medium"),
            (low_priority, "low")
        ]:
            print(f"\nProcessing {label} priority students...")
            new_assignments = assign_priority_group(priority_group, label, activity_capacity)
            print(f"Assigned {len(new_assignments)} {label} priority students")
            assignments.update(new_assignments)

        if not assignments:
            print("Warning: No assignments were made")
            return None, None

        # Calculate preference satisfaction
        preference_satisfaction = {'1st': 0, '2nd': 0, '3rd': 0, 'other': 0}
        for student_id, daily_assignments in assignments.items():
            for day, assigned_activity in daily_assignments.items():
                student_prefs = preferences[student_id]['days'][day]
                if assigned_activity == student_prefs['1st_preference']:
                    preference_satisfaction['1st'] += 1
                elif assigned_activity == student_prefs['2nd_preference']:
                    preference_satisfaction['2nd'] += 1
                elif assigned_activity == student_prefs['3rd_preference']:
                    preference_satisfaction['3rd'] += 1
                else:
                    preference_satisfaction['other'] += 1

        return assignments, preference_satisfaction

    except Exception as e:
        print(f"Error during flow calculation: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def print_results(assignments, preferences):
    if assignments is None:
        print("No results to print due to earlier errors.")
        return
    
    # First print high priority students' assignments
    print("\nHigh Priority Student Assignments:")
    print("=" * 80)
    print(f"{'Student':^10} | {'Day':^5} | {'Assigned':^20} | {'Was':^10} | {'Preferences':<30}")
    print("-" * 80)
    
    for student_id, daily_activities in sorted(assignments.items()):
        student_priority = preferences[student_id]['weight']
        if student_priority != 'high':
            continue
            
        for day, assigned_activity in sorted(daily_activities.items()):
            student_prefs = preferences[student_id]['days'][day]
            pref_status = "other"
            if assigned_activity == student_prefs['1st_preference']:
                pref_status = "1st"
            elif assigned_activity == student_prefs['2nd_preference']:
                pref_status = "2nd"
            elif assigned_activity == student_prefs['3rd_preference']:
                pref_status = "3rd"
                
            prefs_str = f"1:{student_prefs['1st_preference']}, 2:{student_prefs['2nd_preference']}, 3:{student_prefs['3rd_preference']}"
            print(f"{student_id:^10} | {day:^5} | {assigned_activity:^20} | {pref_status:^10} | {prefs_str:<30}")

    # Then print the summary statistics
    activity_count = {day: {} for day in DAYS}
    preference_satisfaction = {'1st': 0, '2nd': 0, '3rd': 0, 'other': 0}
    priority_satisfaction = {priority: {'1st': 0, '2nd': 0, '3rd': 0, 'other': 0} 
                           for priority in STUDENT_WEIGHTS.keys()}
    total_assignments = 0
    
    for student, daily_activities in assignments.items():
        student_priority = preferences[student]['weight']
        for day, assigned_activity in daily_activities.items():
            total_assignments += 1

            student_prefs = preferences[student]['days'][day]
            if assigned_activity == student_prefs['1st_preference']:
                preference_satisfaction['1st'] += 1
                priority_satisfaction[student_priority]['1st'] += 1
            elif assigned_activity == student_prefs['2nd_preference']:
                preference_satisfaction['2nd'] += 1
                priority_satisfaction[student_priority]['2nd'] += 1
            elif assigned_activity == student_prefs['3rd_preference']:
                preference_satisfaction['3rd'] += 1
                priority_satisfaction[student_priority]['3rd'] += 1
            else:
                preference_satisfaction['other'] += 1
                priority_satisfaction[student_priority]['other'] += 1

            if assigned_activity not in activity_count[day]:
                activity_count[day][assigned_activity] = 0
            activity_count[day][assigned_activity] += 1

    # Print Activity Participation Counts in a table format
    print("\nActivity Participation Counts:")
    print("=" * 80)
    print(f"{'Day':^10} | {'Activity':^30} | {'Count':^10}")
    print("-" * 80)
    for day in DAYS:
        for activity, count in sorted(activity_count[day].items()):
            print(f"{day.capitalize():^10} | {activity:<30} | {count:^10}")

    print("\nOverall Preference Satisfaction:")
    for pref, count in preference_satisfaction.items():
        percentage = (count / total_assignments) * 100
        print(f"{pref} preference: {count} assignments ({percentage:.2f}%)")
    print(f"Total assignments: {total_assignments}")

    print("\nPreference Satisfaction by Priority:")
    for priority in STUDENT_WEIGHTS.keys():
        print(f"\n{priority.capitalize()} Priority Students:")
        priority_total = sum(priority_satisfaction[priority].values())
        if priority_total > 0:
            for pref, count in priority_satisfaction[priority].items():
                percentage = (count / priority_total) * 100
                print(f"  {pref} preference: {count} assignments ({percentage:.2f}%)")

    # Print unassigned students and their preferences
    unassigned_students = set(preferences.keys()) - set(assignments.keys())
    if unassigned_students:
        print("\nUnassigned Students:")
        for student_id in unassigned_students:
            print(f"\nStudent {student_id} was not assigned:")
            print(f"Priority: {preferences[student_id]['weight']}")
            print("Their preferences were:")
            for day, prefs in preferences[student_id]['days'].items():
                print(f"{day}: 1st={prefs['1st_preference']}, 2nd={prefs['2nd_preference']}, 3rd={prefs['3rd_preference']}")

def run(csv_file):
    preferences = load_student_preferences(csv_file)
    if not preferences:
        print("No preferences loaded. Exiting.")
        return

    # Debug print to verify priorities
    priority_counts = {'high': 0, 'medium': 0, 'low': 0}
    for student_data in preferences.values():
        priority_counts[student_data['weight']] += 1
    print("\nStudent priority distribution:")
    for priority, count in priority_counts.items():
        print(f"{priority}: {count} students")

    G = build_flow_network(preferences, DAYS)
    assignments, preference_satisfaction = assign_students_to_activities(G, preferences)
    
    if assignments:
        print("\nAssignments completed successfully.")
        print_results(assignments, preferences)
        
        # Debug print for assignment counts
        assigned_count = len(assignments)
        print(f"\nTotal students assigned: {assigned_count}")
        print(f"Total students in system: {len(preferences)}")
    else:
        print("Error: No assignments were made.")

def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description='Activity Assignment Algorithm')
    parser.add_argument('csv_file', nargs='?', default='student_preferences.csv',
                       help='Path to the CSV file containing student preferences')
    
    args = parser.parse_args()
    
    start_time = time.time()
    run(args.csv_file)
    end_time = time.time()
    print(f"\nTime taken: {end_time - start_time} seconds")

if __name__ == '__main__':
    main()