import csv
import io
import pandas as pd
from flask import render_template, request
from app import app
from utils import generate_paths, distance_cache

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_csv_data = None
        points = {}

        # Process file upload if provided
        uploaded_file = request.files.get('csv_upload')
        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename.lower()
            if filename.endswith('.xlsx'):
                # Reset pointer and read using pandas
                uploaded_file.seek(0)
                try:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                except Exception as e:
                    print("Error reading Excel file:", e)
                    raise e
                # Save the input data as CSV for download
                input_csv_data = df.to_csv(index=False)
                for _, row in df.iterrows():
                    # Ensure callsign exists even if blank
                    callsign = row.get('Callsign', "")
                    # Convert Point to string in case it's numeric
                    point_id = str(row['Point'])
                    points[point_id] = {
                        "x": int(row['X']),
                        "y": int(row['Y']),
                        "callsign": callsign if pd.notna(callsign) else ""
                    }
            else:
                # Process as CSV file (using utf-8-sig to handle BOM)
                try:
                    file_data = uploaded_file.stream.read().decode('utf-8-sig')
                except Exception as e:
                    print("Error decoding CSV file:", e)
                    raise e
                input_csv_data = file_data
                f = io.StringIO(file_data)
                reader = csv.DictReader(f)
                for row in reader:
                    callsign = row.get('Callsign', "")
                    points[row['Point']] = {
                        "x": int(row['X']),
                        "y": int(row['Y']),
                        "callsign": callsign
                    }
        else:
            # Process manual entry from form fields
            point_ids = request.form.getlist('point[]')
            x_coords = request.form.getlist('x[]')
            y_coords = request.form.getlist('y[]')
            callsigns = request.form.getlist('callsign[]')
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Point', 'X', 'Y', 'Callsign'])
            for pid, x, y, cs in zip(point_ids, x_coords, y_coords, callsigns):
                if pid and x and y:
                    points[pid] = {"x": int(x), "y": int(y), "callsign": cs}
                    writer.writerow([pid, x, y, cs])
            input_csv_data = output.getvalue()

        # Parse parameters from the form
        try:
            min_distance = float(request.form.get('min_distance', 700))
            max_distance = float(request.form.get('max_distance', 5000))
            num_numbered_points = int(request.form.get('num_numbered_points', 3))
        except ValueError:
            return "Invalid numeric input", 400

        # Reset the distance cache before generating paths
        distance_cache.clear()

        # Generate valid paths using the user-specified number of numbered points
        results = generate_paths(points, min_distance, max_distance, num_numbered_points)

        # Build the results CSV
        results_output = io.StringIO()
        writer = csv.writer(results_output)
        writer.writerow(['Start Point', 'Path', 'Total Distance', 'Pickup Point'])
        results_list = []
        for path, total in results:
            writer.writerow([path[0], path, round(total), path[-1]])
            results_list.append([path[0], path, round(total), path[-1]])
        results_csv_data = results_output.getvalue()

        # Build a second CSV and table for callsign paths
        callsign_results_list = []
        for path, total in results:
            call_path = []
            for p in path:
                # For non-numbered start points, omit the callsign
                if p in ['N', 'S', 'E', 'W']:
                    call_path.append(p)
                else:
                    cs = points[p].get("callsign", "")
                    call_path.append(f"{p} ({cs})" if cs else p)
            callsign_results_list.append(call_path)
        callsign_output = io.StringIO()
        writer = csv.writer(callsign_output)
        writer.writerow(["Callsign Path"])
        for call_path in callsign_results_list:
            writer.writerow(call_path)
        callsign_csv_data = callsign_output.getvalue()

        message = f"Found {len(results)} valid path(s)."
        return render_template('result.html',
                               results=results_list,
                               results_csv=results_csv_data,
                               input_csv=input_csv_data,
                               callsign_results=callsign_results_list,
                               callsign_csv=callsign_csv_data,
                               message=message)
    return render_template('form.html')
