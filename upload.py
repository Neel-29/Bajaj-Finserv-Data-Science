# client_bulk_upload_parallel.py

import base64
import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

IMAGE_FOLDER = "D:\CODE\Python\lbmaske"
API_URL = "http://127.0.0.1:8000/get-lab-tests"
OUTPUT_JSON = "lab_reports_results_parallel.json"
MAX_WORKERS = 10

results = {}


def process_image(filename):
    filepath = os.path.join(IMAGE_FOLDER, filename)
    try:
        with open(filepath, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode('utf-8')

        payload = {"image_base64": b64_string}
        response = requests.post(API_URL, json=payload)
        data = response.json()

        if response.status_code == 200 and data.get('is_success'):
            print(f"{filename} processed")
            return (filename, data['data'])
        else:
            print(f"Failed {filename}: {data}")
            return (filename, None)
    except Exception as e:
        print(f"Error with {filename}: {e}")
        return (filename, None)


def main():
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(process_image, f): f for f in image_files}

        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                fname, result = future.result()
                if result is not None:
                    results[fname] = result
            except Exception as e:
                print(f"Unexpected error on {filename}: {e}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\nDone! Results saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
