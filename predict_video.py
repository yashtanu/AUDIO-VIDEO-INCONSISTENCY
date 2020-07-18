N_THREADS = 4
BETA = 0.5

import joblib
from joblib import Parallel, delayed
from data import video_wrapper, get_duration, RECORD_SECONDS, extract_sliding_windows
import numpy as np
from tqdm import tqdm
from copy import deepcopy
import traceback
import os

def get_clfs(clf_path):
    clf = joblib.load(clf_path)    
    clfs = [deepcopy(clf) for i in range(N_THREADS)]
    return clfs

def softmax(x):
    exp = np.exp(x)
    return exp / np.sum(exp, axis=1)

def convert_video(v, out_path="temp.mp4"):
    os.system('ffmpeg -y -i "{}" -r 24 "{}"'.format(v, out_path))

def predict_one(clf, v, start, audio_path):
    # Get window
    try:
        window = video_wrapper(v, start, audio_path)

        # Predict on window
        pred = clf.predict_proba(window)
        
        return pred

    except Exception as e:
        #traceback.print_exc()
        return None

def predict_video_sliding_window(clfs, v, audio_path):
    duration = get_duration(v)
    num_windows = int(duration / RECORD_SECONDS)
    
    sum_pred = np.zeros((1, 2))

    out = Parallel(n_jobs=N_THREADS)(delayed(predict_one)(clfs[i % N_THREADS], v, n * RECORD_SECONDS, audio_path) for i, n in tqdm(enumerate(range(num_windows))))    
    out = [item for item in out if item is not None]

    last_30 = out[-30:]
    sum_pred_30 = sum(last_30) / len(last_30)
    
    for pred in out:
        # Exponential Averaging
        sum_pred = (1 - BETA) * sum_pred + BETA * pred
    
    return sum_pred, sum_pred_30
'''
def predict_video_sliding_window(clf, v):
    features = extract_sliding_windows(v)
    pred = clf.predict_proba(features)

    exp_avg = np.zeros((1, 2))
    for i in range(pred.shape[0]):
        exp_avg = exp_avg * (1 - BETA) + BETA * pred
    return exp_avg, pred.mean(axis=0)[0] 
'''
if __name__ == "__main__":
    #clf = joblib.load("Modelling/mlp.jbl")
    clfs = get_clfs("/home/surya/Documents/Projects/InconsistencyDetection/v2/automl_small2_1s_24fps.jbl")
    video_path = "/home/surya/Documents/Projects/InconsistencyDetection/test_vids/mp4/real.mp4"

    out = predict_video_sliding_window(clfs, video_path)
    #print(out)
    print("Chance of speaker matching with audio (whole video): {}".format(out[0][0] * 100))
