# Activity Assignment Algorithm (AAA)

## Overview
The Activity Assignment Algorithm (AAA) is a Python-based solution for automatically assigning students to activities based on their preferences and priorities. It uses network flow algorithms to optimize assignments while respecting capacity constraints and student preferences. While it's designed for student activity assignment, it can be adapted to other use cases, such as room allocation, etc.

## Features
- Priority-based assignment (high, medium, low priority students)
- Support for multiple days and activities
- Preference-based matching (1st, 2nd, and 3rd choices)
- Capacity limits for activities
- Detailed assignment statistics and reporting

## Requirements
- Python 3.x
- NetworkX library
- CSV input file

## Installation
1. Clone this repository
2. Install required dependencies:
```bash
pip3 install networkx
```

## Usage
To run the AAA, use the following command:
```bash
python3 auto_assign.py <path_to_csv_file>
```

## Input File Format
The program expects a CSV file with the following columns:
- `student_id`: Unique identifier for each student
- `priority`: Student priority level (high/medium/low)
- `day`: Day of the week (mon/tue/wed/thu)
- `1st_preference`: First choice activity
- `2nd_preference`: Second choice activity
- `3rd_preference`: Third choice activity

Example:
```
student_id,day,1st_preference,2nd_preference,3rd_preference,priority
S001,mon,CreativeWriting,UIDesign,BoardGames,high
S001,tue,Theater,BoardGames,DramaClub,high
S001,wed,Meditation,DramaClub,mediumDPrinting,high
```
student_preferences.csv contains the sample csv file.

## Output
The program provides:
- Detailed assignments for high-priority students
- Activity participation counts by day
- Overall preference satisfaction statistics
- Priority-based satisfaction breakdown
- List of unassigned students (if any)
- Execution time

### Performance
- The execution time is typically under 1 second for a small dataset such as 1000 students, 4 days, 3 preferences, making it suitable for real-time applications.
- For larger datasets, the execution time may increase, but the algorithm is designed to be efficient.
