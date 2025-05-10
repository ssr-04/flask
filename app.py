import os
from flask import Flask, send_file, jsonify, make_response
from flask_cors import CORS

from firebase import get_health_data_from_firebase
from analysis import do_analysis
from pdf import generate_report

app = Flask(__name__)
CORS(app)
@app.route('/report/<int:idx>', methods=['GET'])
def process_request(idx):
    data = get_health_data_from_firebase(idx)
    print(data)
    name = data['name']
    heart_bpm = data['heartBPM']
    spo2 = data['Spo2']
    beat_timings = data['BeatTimings']

    result = do_analysis(name, beat_timings, spo2, heart_bpm)
    
    try:
        report_pdf_path = generate_report(result,name,idx)

        if not os.path.exists(report_pdf_path):
            return make_response(jsonify({"error": "Report file not found after generation."}), 500)

        response = send_file(
            report_pdf_path,
            as_attachment=True,
            download_name=report_pdf_path,
            mimetype='application/pdf'
        )
        

        return response

    except ValueError as ve:
        app.logger.warning(f"Value error for idx {idx}: {str(ve)}")
        if "No data found" in str(ve) or "Incomplete data" in str(ve):
            return make_response(jsonify({"error": str(ve)}), 404) 
        return make_response(jsonify({"error": str(ve)}), 400) 
    except FileNotFoundError: 
        app.logger.error(f"Report generation failed to create file for idx {idx}")
        return make_response(jsonify({"error": "Report generation failed."}), 500)
    except Exception as e:
        app.logger.error(f"An unexpected error occurred for idx {idx}: {str(e)}")
        return make_response(jsonify({"error": "An internal server error occurred."}), 500)

if __name__ == '__main__':
    if not os.path.exists("reports"):
        os.makedirs("reports")
    app.run(host="0.0.0.0",debug=True,port="5432")