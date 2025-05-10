import matplotlib # Import matplotlib first
matplotlib.use('Agg') # <--- !! IMPORTANT: Set backend before importing pyplot !!
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import welch
from scipy.stats import variation
from nolds import sampen
import datetime
import google.generativeai as genai
import os

def do_analysis(name, beat_timings, spo2_values, bpm_values):
  # name = "Sankar"
  # date = datetime.datetime.now().strftime("%Y-%m-%d")
  # beat_timings = [148, 1034, 1841, 2707, 3653, 4629, 5585, 6531, 7428, 8224, 9041, 9917, 10893, 11879, 12835, 13721, 14637, 15573, 16489, 17575, 18640, 19656, 20552, 21488, 22414, 23320, 24436, 25412, 26398, 27284, 28180, 29077, 30063, 31069, 31965, 32831, 33728, 34614, 35600, 36616, 37572, 38478, 39384, 40340, 41316, 42332, 43288, 44194, 45120, 46106, 47112, 48118, 49004, 49920, 50827, 51833, 52759, 53685, 54591, 55418, 56234, 57150, 58126, 59122, 60098, 61034, 61941, 62937, 63952, 64938, 65825, 66711, 67637, 68613, 69509, 70385, 71262, 72098, 73015, 74090]
  # spo2_values = [96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 96, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97]
  # bpm_values = [57, 57, 57, 65, 65, 65, 69, 69, 69, 69, 72, 72, 72, 72, 72, 72, 74, 74, 74, 74, 71, 71, 71, 70, 70, 70, 70, 68, 68, 68]

  rr_intervals = []
  for i in range(len(beat_timings) - 1):
    rr_intervals.append(beat_timings[i+1] - beat_timings[i])
  rr_intervals = np.array(rr_intervals)

  result = []

  # --- Time-Domain Metrics ---
  sdnn = np.std(rr_intervals, ddof=1)
  rmssd = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))
  pnn50 = np.sum(np.abs(np.diff(rr_intervals)) > 50) / len(rr_intervals) * 100

  result.append("\n--- Time-Domain Metrics ---")
  result.append(f"SDNN: {sdnn:.2f} ms")
  result.append(f"RMSSD: {rmssd:.2f} ms")
  result.append(f"pNN50: {pnn50:.2f} %")

  # --- Frequency-Domain Metrics ---
  freqs, psd = welch(rr_intervals, fs=4, nperseg=64)  # fs=4Hz (if ~250ms sampling)
  lf_band = (freqs >= 0.04) & (freqs <= 0.15)
  hf_band = (freqs >= 0.15) & (freqs <= 0.4)
  lf_power = np.trapz(psd[lf_band], freqs[lf_band])
  hf_power = np.trapz(psd[hf_band], freqs[hf_band])
  lf_hf_ratio = lf_power / hf_power if hf_power > 0 else np.inf

  result.append("\n--- Frequency-Domain Metrics ---")
  result.append(f"LF Power: {lf_power:.6f} s²")
  result.append(f"HF Power: {hf_power:.6f} s²")
  result.append(f"LF/HF Ratio: {lf_hf_ratio:.2f}")

  # --- Nonlinear Metrics ---
  sd1 = np.sqrt(0.5) * np.std(np.diff(rr_intervals), ddof=1)
  sd2 = np.sqrt(2 * sdnn**2 - 0.5 * sd1**2)
  sampen_value = sampen(rr_intervals)

  result.append("\n--- Nonlinear Metrics ---")
  result.append(f"SD1: {sd1:.2f} ms")
  result.append(f"SD2: {sd2:.2f} ms")
  result.append(f"Sample Entropy: {sampen_value:.4f}")

  # --- Per-Window Analysis ---
  window_size = 10
  n_windows = len(rr_intervals) // window_size
  window_results = []

  for i in range(n_windows):
      window_rr = rr_intervals[i*window_size:(i+1)*window_size]
      mean_rr = np.mean(window_rr)
      window_sdnn = np.std(window_rr, ddof=1)
      window_rmssd = np.sqrt(np.mean(np.diff(window_rr) ** 2))
      window_results.append({
          'Window': i+1,
          'Mean RR (ms)': mean_rr,
          'SDNN (ms)': window_sdnn,
          'RMSSD (ms)': window_rmssd
      })

  window_df = pd.DataFrame(window_results)
  result.append("\n--- Per-Window HRV Metrics ---")
  for window_result in window_results:
      result.append(str(window_result))

  # --- SpO₂ Analysis ---
  spo2_mean = np.mean(spo2_values)
  spo2_std = np.std(spo2_values)
  spo2_cv = variation(spo2_values) * 100
  spo2_min = np.min(spo2_values)
  spo2_max = np.max(spo2_values)

  result.append("\n--- SpO₂ Summary ---")
  result.append(f"Mean SpO₂: {spo2_mean:.2f} %")
  result.append(f"Std Dev SpO₂: {spo2_std:.2f} %")
  result.append(f"Coefficient of Variation: {spo2_cv:.2f} %")
  result.append(f"Min SpO₂: {spo2_min:.2f} %")
  result.append(f"Max SpO₂: {spo2_max:.2f} %")

  # --- Visualization ---

  # RR Interval Time Series
  plt.figure(figsize=(10, 4))
  plt.plot(rr_intervals, marker='o')
  plt.title('RR Intervals Over Time')
  plt.xlabel('Beat Number')
  plt.ylabel('RR Interval (ms)')
  plt.grid(True)
  plt.savefig('./rr_intervals.png', dpi=300)
  plt.close()

  # PSD Plot
  plt.figure(figsize=(8, 4))
  plt.semilogy(freqs, psd)
  plt.title('Power Spectral Density (PSD)')
  plt.xlabel('Frequency (Hz)')
  plt.ylabel('PSD (s²/Hz)')
  plt.grid(True)
  plt.savefig('./psd.png', dpi=300)
  plt.close()


  # Poincaré Plot
  plt.figure(figsize=(6, 6))
  plt.scatter(rr_intervals[:-1], rr_intervals[1:], alpha=0.7)
  plt.title('Poincaré Plot')
  plt.xlabel('RR_n (ms)')
  plt.ylabel('RR_n+1 (ms)')
  plt.grid(True)
  plt.savefig('./poincare.png', dpi=300)
  plt.close()


  # SpO₂ and BPM Time Series
  fig, ax1 = plt.subplots(figsize=(10, 4))
  ax1.plot(bpm_values, color='tab:red', label='BPM', marker='o')
  ax1.set_xlabel('Measurement Number')
  ax1.set_ylabel('BPM', color='tab:red')
  ax1.tick_params(axis='y', labelcolor='tab:red')

  ax2 = ax1.twinx()
  ax2.plot(spo2_values, color='tab:blue', label='SpO₂', marker='s')
  ax2.set_ylabel('SpO₂ (%)', color='tab:blue')
  ax2.tick_params(axis='y', labelcolor='tab:blue')

  plt.title('BPM and SpO₂ Over Time')
  fig.tight_layout()
  plt.savefig('./series.png', dpi=300)
  plt.close()
  print("Analysis completed...")
  result_string = "\n".join(result)
  print('generating report...')
  report = generate_report(name, result_string)
  return report

def generate_report(name, result_string):
  date = datetime.datetime.now().strftime("%Y-%m-%d")
  prompt = """
  You are an AI expert in physiological data analysis, specializing in Heart Rate Variability (HRV) and SpO₂ interpretation. Your task is to generate a comprehensive, detailed, and professional medical-style report based on the provided sensor data and computed metrics. The entire output MUST be a single, valid JSON object. Do not include any explanatory text outside of this JSON object.
  The JSON object should adhere to the following structure. The content within the interpretation, paragraph, analysis, content, text, and similar string fields should be the detailed, professional medical-style text as if you were writing a normal report.
  JSON Output Structure:
  {
    "reportTitle": "PHYSIOLOGICAL ASSESSMENT REPORT",
    "patientAndAssessmentDetails": {
      "patientName": "[As per Input]",
      "dateOfDataCollection": "[Not Provided, or 'As per input data timestamp if available']",
      "reasonForAssessment": "Evaluation of Autonomic Nervous System Function and Oxygen Saturation."
    },
    "introduction": {
      "paragraph": "String: Brief statement on the purpose of the report – to analyze HRV and SpO₂ data for insights into autonomic and respiratory health."
    },
    "heartRateVariabilityAnalysis": {
      "introductionParagraph": "String: General introduction to HRV (e.g., 'HRV reflects the variation...').",
      "timeDomainMetrics": {
        "sectionTitle": "A. Time-Domain Metrics",
        "sectionDescription": "String: Brief description (e.g., 'These metrics quantify the amount of variability...').",
        "sdnn": {
          "metricName": "SDNN (Standard Deviation of NN intervals)",
          "value": "String: e.g., '{{SDNN_VALUE}} ms'",
          "interpretation": "String: Detailed interpretation of the specific SDNN value, its physiological significance, relevance to overall HRV, and what it generally implies for health."
        },
        "rmssd": {
          "metricName": "RMSSD (Root Mean Square of Successive Differences)",
          "value": "String: e.g., '{{RMSSD_VALUE}} ms'",
          "interpretation": "String: Detailed interpretation of the specific RMSSD value, its link to parasympathetic activity, and health implications."
        },
        "pnn50": {
          "metricName": "pNN50 (Percentage of successive NN intervals differing by more than 50 ms)",
          "value": "String: e.g., '{{PNN50_VALUE}} %'",
          "interpretation": "String: Detailed interpretation of the specific pNN50 value, its relation to parasympathetic activity, and health implications."
        }
      },
      "frequencyDomainMetrics": {
        "sectionTitle": "B. Frequency-Domain Metrics",
        "sectionDescription": "String: Brief description (e.g., 'These metrics analyze the power distribution...').",
        "lfPower": {
          "metricName": "LF Power (Low Frequency Power)",
          "value": "String: e.g., '{{LF_POWER_VALUE}} s²'",
          "interpretation": "String: Detailed interpretation of LF power, its influences, and what the value suggests."
        },
        "hfPower": {
          "metricName": "HF Power (High Frequency Power)",
          "value": "String: e.g., '{{HF_POWER_VALUE}} s²'",
          "interpretation": "String: Detailed interpretation of HF power, its link to vagal tone, and what the value suggests."
        },
        "lfHfRatio": {
          "metricName": "LF/HF Ratio",
          "value": "String: e.g., '{{LF_HF_RATIO_VALUE}}'",
          "interpretation": "String: Detailed interpretation of the LF/HF ratio regarding sympathovagal balance and what the specific ratio implies."
        }
      },
      "nonlinearMetrics": {
        "sectionTitle": "C. Nonlinear Metrics",
        "sectionDescription": "String: Brief description (e.g., 'These metrics provide insights into the complexity...').",
        "sd1": {
          "metricName": "SD1 (Short-term variability from Poincaré plot)",
          "value": "String: e.g., '{{SD1_VALUE}} ms'",
          "interpretation": "String: Detailed interpretation of SD1, its relation to Poincaré plots, short-term HRV, and parasympathetic activity."
        },
        "sd2": {
          "metricName": "SD2 (Long-term variability from Poincaré plot)",
          "value": "String: e.g., '{{SD2_VALUE}} ms'",
          "interpretation": "String: Detailed interpretation of SD2, its relation to Poincaré plots, long-term HRV, and overall variability."
        },
        "sampleEntropy": {
          "metricName": "Sample Entropy",
          "value": "String: e.g., '{{SAMPLE_ENTROPY_VALUE}}'",
          "interpretation": "String: Detailed interpretation of Sample Entropy regarding signal complexity/regularity and physiological adaptability."
        }
      },
      "perWindowHrvMetrics": {
        "sectionTitle": "D. Per-Window HRV Metrics",
        "sectionDescription": "String: Brief description (e.g., 'This shows HRV dynamics over shorter segments...').",
        "windows": [

        ],
        "overallAnalysis": "String: Analysis of trends, variations, or consistencies across windows for Mean RR, SDNN, and RMSSD, and what it might imply."
      }
    },
    "peripheralOxygenSaturationSummary": {
      "sectionTitle": "IV. PERIPHERAL OXYGEN SATURATION (SpO₂) SUMMARY",
      "sectionDescription": "String: Brief description (e.g., 'SpO₂ measures the percentage of hemoglobin...').",
      "meanSpo2": {
        "metricName": "Mean SpO₂",
        "value": "String: e.g., '{{MEAN_SPO2_VALUE}} %'",
        "interpretation": "String: Interpretation of mean SpO₂, whether it's normal/optimal."
      },
      "stdDevSpo2": {
        "metricName": "Std Dev SpO₂",
        "value": "String: e.g., '{{STD_DEV_SPO2_VALUE}} %'",
        "interpretation": "String: Interpretation regarding stability of SpO₂."
      },
      "coefficientOfVariationSpo2": {
        "metricName": "Coefficient of Variation",
        "value": "String: e.g., '{{COV_SPO2_VALUE}} %'",
        "interpretation": "String: Interpretation regarding relative variability and stability."
      },
      "minSpo2": {
        "metricName": "Min SpO₂",
        "value": "String: e.g., '{{MIN_SPO2_VALUE}} %'",
        "interpretation": "String: Interpretation of minimum SpO₂, noting any desaturations."
      },
      "maxSpo2": {
        "metricName": "Max SpO₂",
        "value": "String: e.g., '{{MAX_SPO2_VALUE}} %'",
        "interpretation": "String: Interpretation of maximum SpO₂."
      },
      "overallInterpretation": "String: Overall interpretation of SpO₂ status, efficiency of respiratory function."
    },
    "integratedImpressionAndSummary": {
      "sectionTitle": "V. INTEGRATED IMPRESSION & SUMMARY",
      "content": [
        // Array of strings, each string being a paragraph of the summary.
        "String: Synthesized findings from HRV and SpO₂.",
        "String: Description of predominant autonomic state.",
        "String: Comments on cardiovascular adaptability and respiratory status.",
        "String: Highlight of noteworthy findings.",
        "String: Conclusion of the report."
      ]
    },
    "recommendationsAndConsiderations": {
      "sectionTitle": "VI. RECOMMENDATIONS & CONSIDERATIONS",
      "points": [
        // Array of string, each representing a recommendation point.
      ]
    }
  }

  Tone and Style for Content within JSON strings:
  Maintain a professional, objective, authoritative, and clinical tone.
  Use clear, precise medical terminology where appropriate, with detailed explanations.
  Base interpretations firmly on the provided data. Avoid speculation.
  Constraints for Content within JSON strings:
  DO NOT invent patient data beyond placeholders.
  BEGIN DATA INPUT:

  """ + f"Name:{name} \nDate:{date} \nData:{result_string}" + """\nEND DATA INPUT.
  Please generate ONLY the JSON object as described, based on the data that will be provided in the 'BEGIN DATA INPUT' section. Ensure the JSON is valid."""
  key = os.getenv("API_KEY")
  genai.configure(api_key=key)
  model = genai.GenerativeModel(model_name = "gemini-2.0-flash")
  response = model.generate_content([prompt])
  return response.text

