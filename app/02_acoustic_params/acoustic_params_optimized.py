import time
_SCRIPT_T0 = time.perf_counter()
def boot_timing(label):
    now = time.perf_counter()
    print(f"[BOOT_TIMING] {label}: {now - _SCRIPT_T0:.3f}s", flush=True)

import sys
import os
import csv
import datetime
import argparse

import leq_levels_oct_weighting_C as m
import numpy as np

from utils import load_config,load_yaml,read_calibration_constants,get_valid_audio_files,read_audio,resample_audio,update_processed_files
from logging_config import setup_logging

config = load_config("/opt/noiseport/app/config.yaml")
logging = setup_logging(script_name="acoustic_params")

def get_start_timestamp(audio_file):
    filename = os.path.basename(audio_file)
    name_split = os.path.splitext(filename)[0]

    start_timestamp = datetime.datetime.strptime(
        name_split,
        "%Y%m%d_%H%M%S"
    )

    return start_timestamp


class LeqLevelOct:
    def __init__(
        self,
        fs: int,
        calibration_constant: float,
        window_size: int,
        audio_path: str,
        weighting_yaml_path: str,
        bank_yaml_path: str,
    ):
        self.fs = int(fs)
        self.C = float(calibration_constant)
        self.window_size = int(window_size)
        self.audio_path = audio_path

        w = load_yaml(weighting_yaml_path)

        if int(w["fs"]) != self.fs:
            raise ValueError(f"Weighting YAML fs={w['fs']} does not match fs={self.fs}")

        self.bA = np.asarray(w["A_weighting"]["b"], dtype=float)
        self.aA = np.asarray(w["A_weighting"]["a"], dtype=float)
        self.bC = np.asarray(w["C_weighting"]["b"], dtype=float)
        self.aC = np.asarray(w["C_weighting"]["a"], dtype=float)

        b = load_yaml(bank_yaml_path)
        if int(b["fs"]) != self.fs:
            raise ValueError(f"Bank YAML fs={b['fs']} does not match fs={self.fs}")

        self.sos_bank = np.asarray(b["sos_bank"], dtype=float)
        self.center_freqs = b["freq_center"]

        self.processor = m.AcousticProcessor(
            np.ascontiguousarray(self.bA, dtype=float),
            np.ascontiguousarray(self.aA, dtype=float),
            np.ascontiguousarray(self.bC, dtype=float),
            np.ascontiguousarray(self.aC, dtype=float),
            np.ascontiguousarray(self.sos_bank, dtype=float),
        )

    def process_audio_files(self,x, audio_file, bands):

        """
        Returns:
        all_data: list of per-file rows
        col_names: column names
        """

        start_timestamp = get_start_timestamp(audio_file)
        rows = []

        # ---------------------------------------
        # Select column names
        # ---------------------------------------

        if bands: col_names = ( ["LA", "LC", "LZ", "LAmax", "LAmin"] + [f"{f:.2f}Hz" for f in self.center_freqs] + ["filename", "date"] )           
        else: col_names = ["LA", "LC", "LZ", "LAmax", "LAmin", "filename", "date"]
            
        # ---------------------------------------
        # Skip audio if length shorter than one window
        # ---------------------------------------

        if len(x) < self.window_size:
            logging.warning(f"Skipping {audio_file}: shorter than one window.")
            return [], col_names
        
        # ---------------------------------------
        # Process audio
        # ---------------------------------------

        levels = self.processor.process(
            x,
            self.window_size,
            float(self.C),
            bands,
        )

        # ---------------------------------------
        # Parse results and return
        # ---------------------------------------

        
        for frame_idx, values in enumerate(levels):
            timestamp = start_timestamp + datetime.timedelta(
                seconds=(frame_idx * self.window_size) / self.fs
            )

            numeric_values = [
                round(float(v), 2) if np.isfinite(v) else ""
                for v in values
            ]

            row = numeric_values + [
                audio_file,
                timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            ]

            rows.append(row)

        return [rows], col_names

def main():

    try:

        
        # ---------------------------------------
        # Load config info
        # ---------------------------------------

        audio_path                      = config['paths']['audio']
        output_path                     = config['paths']['acoustic_params']
        processed_files_txt             = config['paths']['processed_files_acoustics']
        calibration_constants_folder    = config['paths']['calibration_constants']
        fs                              = config['acoustic']['fs']
        mode                            = config['acoustic']['bands'] 

        if fs == 16000:
            weighting_yaml              = config['paths']['weighting_yaml_16000']
            bank_yaml                   = config['paths']['bank_yaml_16000']
        else:
            weighting_yaml              = config['paths']['weighting_yaml_32000']
            bank_yaml                   = config['paths']['bank_yaml_32000']

        calibration_constants           = read_calibration_constants(calibration_constants_folder)
        valid_audio_files               = get_valid_audio_files(audio_path, processed_files_txt)
        timestamp_str                   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename                 = f"acoustics_{fs}_weighted_{timestamp_str}.csv"
        output_path                     = os.path.join(output_path, output_filename)

        logging.info(f"Audio path: {repr(audio_path)}")
        logging.info(f"Audio path: {audio_path}")
        logging.info(f"Processed file list path: {processed_files_txt}")
        logging.info(f"Processed file list exists: {os.path.exists(processed_files_txt)}")
        logging.info(f"Calibration constant: {calibration_constants_folder}")
        logging.info(f"Using weighting YAML: {weighting_yaml}")
        logging.info(f"Using bank YAML: {weighting_yaml}")

        logging.info(f"Using sample rate: {fs}")
        logging.info(f"Saving data to: {output_path}")
        logging.info(f"Processing {len(valid_audio_files)} new audio files...")

        # ---------------------------------------
        # Creacion de objeto calculadora
        # ---------------------------------------

        calculator = LeqLevelOct(
            fs                      = fs,
            calibration_constant    = float(0),
            window_size             = fs,  # 1 second analysis
            audio_path              = audio_path,
            weighting_yaml_path     = weighting_yaml,
            bank_yaml_path          = bank_yaml,
        )

        rows_written = 0
        csv_initialized = False

        with open(output_path, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)
            for audio_file in valid_audio_files:
                try:
                    file_rows_written = 0
                    device_id = "songmeter"
                    #---------------------------
                    # Check valid format
                    #---------------------------

                    if not audio_file.lower().endswith(".wav"):

                        logging.warning(f"Skipping non-wav file: {audio_file}")

                        continue
                    
                    #---------------------------
                    # Assign filepath and devide identifier
                    #---------------------------

                    filepath = os.path.join(audio_path, audio_file)
                    
                    logging.info(f"Device id: {device_id}")

                    #---------------------------
                    # Assign calibration constant to calculator
                    #---------------------------

                    C = calibration_constants.get(device_id, float(0))

                    calculator.C = C

                    #---------------------------
                    # Read audio file
                    #---------------------------

                    try:

                        x, fs_read = read_audio(filepath)
                        if x is None: continue

                    except Exception as e:

                        logging.warning(f"Error reading {audio_file}: {e}")
                        continue

                    #---------------------------
                    # Resample if needed
                    #---------------------------

                    if fs_read != calculator.fs:
                        try:

                            x,fs_read = resample_audio(calculator, audio_file, fs_read, x)

                        except Exception as e:
                            
                            logging.warning(f"Error resampling {audio_file}: {e}")
                            continue

                    #---------------------------
                    # Call processor and calculate
                    #---------------------------

                    file_data, col_names = calculator.process_audio_files(
                        x               = x,
                        audio_file      = audio_file,
                        bands           = mode,
                    )

                    #---------------------------
                    # Write rows into csv file
                    #---------------------------

                    if not csv_initialized:
                        writer.writerow(col_names)
                        csv_initialized = True

                    for file_rows in file_data:
                        writer.writerows(file_rows)
                        file_rows_written += len(file_rows)


                    if file_rows_written > 0:
                        rows_written += file_rows_written
                        update_processed_files(processed_files_txt, audio_file)
                        logging.info(f"Processed and marked: {audio_file}")
                    else:
                        logging.warning(
                            f"No usable data produced for {audio_file}; "
                            "not marking as processed."
                        )

                    logging.info(
                        f"Processed file: {audio_file} "
                        f"with device_id={device_id}, C={C}, fs={fs}, "
                        f"rows={file_rows_written}"
                    )

                except Exception as e:
                    logging.warning(f"Error processing file: {audio_file}, {e}")

        if rows_written == 0:
            logging.warning("No data to save.")
            try:
                os.remove(output_path)
                logging.info(f"Removed empty output file: {output_path}")
            except OSError:
                pass
            return

        logging.info(f"Total rows written: {rows_written}")
        logging.info(f"Output saved to {output_path}")
        print(f"Output saved to {output_path}")

    except KeyboardInterrupt:
        logging.error("Process interrupted by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


boot_timing("before main")
if __name__ == "__main__":
    main()
boot_timing("after main")