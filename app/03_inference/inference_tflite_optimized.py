import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
DEPS_DIR = os.path.join(BASE_DIR,'deps')
sys.path.insert(0,DEPS_DIR)

import argparse
import numpy as np
import datetime
import time
import csv
import soxr
import soundfile as sf
import tflite_runtime.interpreter as tflite

import warnings

from utils import class_names_csv, load_config
from logging_config import setup_logging

config = load_config("/opt/noiseport/app/config.yaml")
logging = setup_logging(script_name="inference_tflite")

def filter_predictions(predictions,threshold):
    top_i = int(np.argmax(predictions))
    top_pred = float(predictions[top_i])
    if top_pred > threshold:
        return top_i, top_pred
    return None, None

def inference(path,file_list,id_micro, model_path, sample_rate,window_size, threshold,  logging, output_csv_path,processed_txt_path,  yamnet_class_map_csv   , num_threads):

    # ---------------------------
    # INIZIALATIN PROCESSED FILES
    # ---------------------------
    
    processed_files = load_processed_files(processed_txt_path)
    
    # --------------------------------------------------------
    # Create the TFLite interpreter
    # --------------------------------------------------------
    
    if model_path is not None: interpreter = tflite.Interpreter( model_path=model_path,num_threads=num_threads)                        
    else: raise Exception('Model Path doesnt exist.')

    yamnet_classes = class_names_csv(yamnet_class_map_csv)

    # --------------------
    # Processing audio files
    # --------------------

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    waveform_input_index = input_details[0]['index']
    scores_output_index = output_details[0]['index']

    # El modelo ya viene con shape fijo [15600], así que reservamos una vez
    interpreter.allocate_tensors()

    for audio_file in file_list:
        try:

            logging.info(f"Processing --> {audio_file}")

            if audio_file in processed_files:
                logging.info(f"Skipping {audio_file}, already processed.")
                continue
            
            file_start_time = time.time()

            # -----------------------------------------------------------
            # csv file name and folder
            # -----------------------------------------------------------
            wav_filename = os.path.basename(audio_file)  # e.g. 20250108_142606.wav

            # name wave file
            wav_file_raw = os.path.splitext(wav_filename)[0]

            # setting time
            local_tz = datetime.datetime.now().astimezone().tzinfo
            start_timestamp = datetime.datetime.strptime(wav_file_raw, '%Y%m%d_%H%M%S')
            start_timestamp = start_timestamp.replace(tzinfo=local_tz)
            

            if window_size is None: csv_filename = wav_filename.replace(".wav", "_tflt.csv")  # e.g. 20250108_142606.csv
            else: csv_filename = wav_filename.replace(".wav", f"_tflt_w_{window_size}.csv")  # e.g. 20250108_142606.csv
                
            csv_full_path = os.path.join(output_csv_path, csv_filename)


            # --------------------------------------------------------
            # 2 get input/output details --> Removed for optimization reasons
            # --------------------------------------------------------
            logging.info("")

            # --------------------------------------------------------
            # 3 prepare waveform input (0.975s @ 16kHz => 15600 samples)
            # Decode the WAV file
            # -----------------------------------------------------------
            t0 = time.perf_counter()
            wav_data, sr = sf.read(audio_file, dtype=np.int16)
            t1 = time.perf_counter()
            assert wav_data.dtype == np.int16, f'Bad sample type: {wav_data.dtype}'


            waveform = wav_data.astype(np.float32) / 32768.0 # Convert to [-1.0, +1.0]

            # convert to mono and the sample rate expected by YAMNet
            if len(waveform.shape) > 1:
                waveform = np.mean(waveform, axis=1)
                logging.info("Audio file converted to mono")
            if sr != sample_rate:
                #waveform = resampy.resample(waveform, sr, sample_rate)
                waveform = soxr.resample(waveform, sr, sample_rate)
                logging.info("Audio file resampled to 16KHz")
            t2 = time.perf_counter()

            # -----------------------------------------------------------
            # create a fresh CSV data list for this file
            # -----------------------------------------------------------
            with open(csv_full_path, mode="w", newline="") as final_csv:
                writer = csv.writer(final_csv)
                writer.writerow(["id_micro", "Filename", "Timestamp", "Unixtimestamp", "class", "probability"])


                if window_size is None:
                    logging.info("")
                    logging.info(f"Processing the whole audio file: {audio_file}")
                    # --------------------------------------------------------
                    # 4 resize input tensor and allocate
                    # --------------------------------------------------------
                    input_len = int(waveform.shape[0])
                    interpreter.resize_tensor_input(waveform_input_index, [input_len], strict=False)
                    interpreter.allocate_tensors()


                    # --------------------------------------------------------
                    # 5set input tensor and run inference
                    # --------------------------------------------------------
                    interpreter.set_tensor(waveform_input_index, waveform)
                    interpreter.invoke()
                    scores = interpreter.get_tensor(scores_output_index)  
        
                    # ---------------------------------------------------------
                    # predcition
                    # ---------------------------------------------------------
                    prediction = np.mean(scores, axis=0)

                    top_i,top_prediction = filter_predictions(prediction,threshold)
                    
                    if top_i is not None:
                        top_class = yamnet_classes[top_i]
                        top_prediction = f"{top_prediction:.4f}"
                    else:
                        top_class = []
                        top_prediction = []
                    

                    unix_ts = int(start_timestamp.timestamp())

                    writer.writerow([
                        id_micro,
                        audio_file,
                        str(start_timestamp),
                        unix_ts,
                        str(top_class),
                        str(top_prediction)
                    ])
                    

                # -------------------------------
                # WINDOWED
                # -------------------------------
                else:
                    logging.info(f"Processing windowed audio file: {audio_file}")

                    target_len = 15600
                    input_buffer = np.zeros((target_len,), dtype=np.float32)


                    for start_idx in range(0, len(waveform), target_len):

                        end_idx = min(start_idx + target_len, len(waveform))
                        valid_len = end_idx - start_idx

                        input_buffer.fill(0.0)
                        input_buffer[:valid_len] = waveform[start_idx:end_idx]

                        interpreter.set_tensor(waveform_input_index, input_buffer)
                        interpreter.invoke()
                        scores = interpreter.get_tensor(scores_output_index)

                        prediction = np.mean(scores, axis=0)

                        top_i, top_prediction = filter_predictions(prediction, threshold)
                        if top_i is not None:
                            top_class = yamnet_classes[top_i]
                            top_prediction = f"{top_prediction:.4f}"
                        else:
                            top_class = []
                            top_prediction = []

                        start_time_s = start_idx / sample_rate
                        window_timestamp_actual = start_timestamp + datetime.timedelta(seconds=int(start_time_s))
                        unix_ts = int(window_timestamp_actual.timestamp())

                        writer.writerow([
                            id_micro,
                            audio_file,
                            window_timestamp_actual,
                            unix_ts,
                            str(top_class),
                            str(top_prediction)
                        ])

            # ------------------------------------------------------
            # save csv
            # -----------------------------------------------------------

            logging.info(f"Final CSV file saved at {csv_full_path}")

            
            # ----------------------------
            # MARKING FILE AS PROCESSED
            # ----------------------------
            update_processed_files(processed_txt_path, audio_file)
            processed_files.add(audio_file)
            
            file_end_time = time.time()
            elapsed_time = file_end_time - file_start_time
            logging.info(f"Processing of {audio_file} took {elapsed_time:.2f} seconds")

        # -------------
        # END
        # ---------------
        except Exception as e:
                logging.error(f"Error processing file {audio_file}: {e}")
                continue



def load_processed_files(processed_file_path):
    """Load the set of processed filenames from a text file."""
    if os.path.exists(processed_file_path):
        with open(processed_file_path, "r") as f:
            return {line.strip() for line in f if line.strip()}
    return set()



def update_processed_files(processed_file_path, filename):
    """Append a processed filename to the text file."""
    with open(processed_file_path, "a") as f:
        f.write(filename + "\n")


def main():
    try:

        # ----------------------------
        # Load config
        # ----------------------------
        
        model_path = config['prediction']['model_tflite']
        window_size = config['prediction']['window_size']
        threshold = config['prediction']['threshold']
        num_threads = config['prediction']['interpreter_threads']
        prediction_yamnet_class_map_csv = config['prediction']['yamnet_class_map_csv']
        prediction_sample_rate = config['prediction']['sample_rate']

        step = config['prediction']['step_files']
        id_micro = config["sensor"]["id_micro"]
        path = config['paths']['prediction_files']
        output_csv_path = config['paths']['prediction_files']
        processed_txt_path = config['paths']['processed_files_predictions']


    except Exception as e:
        logging.error(f"Error getting the config info: {e}")

    
    logging.info(f"Path: {path}")
    logging.info(f"ID Micro: {id_micro}")
    logging.info(f"Model path: {model_path}")
    logging.info(f"Window size: {window_size}")
    logging.info(f"Probability treshold: {threshold}")
    logging.info(f"Num interpreter threads: {num_threads}")
    logging.info(f"Yamnet class map: {prediction_yamnet_class_map_csv}")
    logging.info(f"Prediction sample rate: {prediction_sample_rate}")
    logging.info(f"File step: {step}")
    logging.info(f"Output path: {output_csv_path}")


    try:

        # ----------------------------
        # Parse audio files in folder
        # ----------------------------

        audio_files = sorted([f for f in os.listdir(path) if f.lower().endswith('.wav')])
        audio_files = audio_files[::step]  
        full_paths = [os.path.join(path, file) for file in audio_files]

    except Exception as e:
        logging.error(f"Error getting the audio files: {e}")
        return

    logging.info(f"Found {len(audio_files)} audio files: {audio_files}")

        # ----------------------------
        # Make inference
        # ----------------------------

    try:
        inference(
            path                    = path,
            file_list               = full_paths,
            id_micro                = id_micro,
            model_path              = model_path,
            yamnet_class_map_csv    = prediction_yamnet_class_map_csv,
            sample_rate             = prediction_sample_rate,
            window_size             = window_size,
            threshold               = threshold,
            output_csv_path         = output_csv_path,
            processed_txt_path      = processed_txt_path,
            num_threads             = num_threads,    
            logging                 = logging
        )

        logging.info("Inference finished.")
    
    except Exception as e:
        logging.error(f"Error making inference: {e}")



if __name__ == '__main__':
    main()
