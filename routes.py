import csv, io
from flask import render_template, request
from app import app
from utils import generate_paths, distance_cache


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a CSV file was uploaded
        uploaded_file = request.files.get('csv_upload')
        input_csv_data = None
        points = {}

        if uploaded_file and uploaded_file.filename:
            # Read CSV from uploaded file; expects columns: Point, X, Y, [Callsign]
            input_csv_data = uploaded_file.stream.read().decode('utf-8')
            f = io.StringIO(input_csv_data)
            reader = csv.DictReader(f)
            for row in reader:
                callsign = row.get('Callsign', '')
                points[row['Point']] = {
                    "x": int(row['X']),
                    "y": int(row['Y']),
                    "callsign": callsign
                }
        else:
            # Process manually entered data; expects arrays for point, x, y, and callsign.
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

        try:
            min_distance = float(request.form['min_distance'])
            max_distance = float(request.form['max_distance'])
        except ValueError:
            return "Invalid numeric input", 400

        distance_cache.clear()  # reset cached distances

        results = generate_paths(points, min_distance, max_distance)

        # Build results CSV (normal output)
        results_output = io.StringIO()
        writer = csv.writer(results_output)
        writer.writerow(['Start Point', 'Path', 'Total Distance', 'Pickup Point'])
        results_list = []
        for path, total in results:
            writer.writerow([path[0], path, round(total), path[-1]])
            results_list.append([path[0], path, round(total), path[-1]])
        results_csv_data = results_output.getvalue()

        # Build a second output with callsign info for the output path.
        callsign_results_list = []
        for path, total in results:
            call_path = []
            for p in path:
                # For non-numbered start points, omit the callsign.
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
