import cv2 
import os 
import sys, time
import numpy as np
import librosa
import random 
from math import ceil
from face import detect_face_landmarks

CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 1
FRAMES_PER_SECOND = 24
NUM_FRAMES = ceil(FRAMES_PER_SECOND * RECORD_SECONDS)
AUDIO_FRAMES = ceil(RATE * RECORD_SECONDS)

MFCC_WINDOW_LENGTH = 87
LANDMARKS_WINDOW_LENGTH = 24
OVERLAP_RATIO = 0


temp_audio_path = "temp/temp.wav"

def get_duration(v):
    cap = cv2.VideoCapture(v)

    fps = cap.get(cv2.CAP_PROP_FPS) 
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    
    return frame_count / fps

def get_example_original(v, start_time=None, audio_path=temp_audio_path):
    command = '''ffmpeg -hide_banner -loglevel panic -y -i "{}" -ab 160k -ac {} -ar {} -vn "{}"'''
    os.system(command.format(v, CHANNELS, RATE, audio_path))

    frames = []
    # timestamps = []
    
    cap = cv2.VideoCapture(v)
    cap.set(cv2.CAP_PROP_FPS, FRAMES_PER_SECOND)

    # Get the frames per second
    fps = cap.get(cv2.CAP_PROP_FPS) 

    # Get the total numer of frames in the video.
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    #print(fps, frame_count, v)
    # Calculate the duration of the video in seconds
    duration = frame_count / fps
    
    # Temporal Offset
    if not start_time:
        t = (random.random() - RECORD_SECONDS) * 0.9
        s = random.random() * (duration-RECORD_SECONDS)
        start_time = max(t, s)
        
    cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
    while True:
        ret, frame = cap.read()
        
        if ret:
            if len(frames) == NUM_FRAMES:
                break
            frames.append(frame)
        else:
            break
    # Release all space and windows once done 
    cap.release()

    signal, _ = librosa.load(temp_audio_path, sr=RATE, offset=start_time, duration=RECORD_SECONDS, dtype=np.float32)

    return frames, signal, fps

def extract(img_frames, audio_frames):
    mfcc = librosa.feature.mfcc(audio_frames, sr=RATE, n_mfcc=50)
    landmarks = [np.expand_dims(detect_face_landmarks(frame), axis=0) for frame in img_frames]
    landmarks = np.concatenate(landmarks, axis=0)
    return mfcc, landmarks

def extract_landmarks(img_frames):
    landmarks = [np.expand_dims(detect_face_landmarks(frame), axis=0) for frame in img_frames]
    landmarks = np.concatenate(landmarks, axis=0)
    return landmarks

def extract_mfcc(audio_frames):
    mfcc = librosa.feature.mfcc(audio_frames, sr=RATE, n_mfcc=50)
    return mfcc

def video_wrapper(v, start_time, audio_path):
    frames, signal, fps = get_example_original(v, start_time)
    #print(frames)
    mfcc, landmarks = extract(frames, signal)
    return np.concatenate([mfcc.reshape(1, -1), landmarks.reshape(1, -1) / 255], axis=1)

def make_windows(arr, window_length, overlap):
    step_size = int(window_length * (1 - overlap))

    windows = []
    i = 0
    while i < arr.shape[0] - window_length + 1:
        windows.append(np.expand_dims(arr[i: i+window_length], axis=0))
        i += step_size + 1
    del windows[-1]
    windows = np.concatenate(windows, axis=0)
    return windows

def extract_sliding_windows(v, name=0, overlap=0):
    command = '''ffmpeg -hide_banner -loglevel panic -y -i "{}" -ab 160k -ac {} -ar {} -vn "{}"'''
    os.system(command.format(v, CHANNELS, RATE, "temp/audio_{}.wav".format(name)))

    cap = cv2.VideoCapture(v)
    cap.set(cv2.CAP_PROP_FPS, FRAMES_PER_SECOND)

    # Get the frames per second
    fps = cap.get(cv2.CAP_PROP_FPS) 

    # Get the total numer of frames in the video.
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    #print(fps, frame_count, v)
    # Calculate the duration of the video in seconds
    duration = frame_count / fps
    
    frames = []
    while True:
        ret, frame = cap.read()
        
        if ret:
            frames.append(frame)
        else:
            break
    
    # Release all space and windows once done 
    cap.release()
    
    landmarks = extract_landmarks(frames)
    
    mfccs = []
    for i in range(int(duration)-1): 
        signal, _ = librosa.load(temp_audio_path, sr=RATE, duration=RECORD_SECONDS, offset=i, dtype=np.float32)
        mfccs.append(np.expand_dims(extract_mfcc(signal), axis=0))
    mfccs = np.concatenate(mfccs, axis=0)
    mfccs = mfccs.reshape(mfccs.shape[0], -1)

    landmarks_windows = make_windows(landmarks, LANDMARKS_WINDOW_LENGTH, overlap)
    landmarks_windows = landmarks_windows.reshape(landmarks_windows.shape[0], -1)
    
    print(mfccs.shape, landmarks_windows.shape)
    
    features = np.concatenate([mfccs, landmarks_windows / 255], axis=1)
    return features

if __name__ == "__main__":
    import joblib
    from joblib import Parallel, delayed
    import traceback
    from tqdm import tqdm 
    from itertools import cycle
    from copy import deepcopy

    videos1 = os.listdir("../recorded/1/")
    videos0 = os.listdir("../recorded/0/")
    print(videos0)
    
    NUM_THREADS = 8
    start_worker_id = 0
    '''
    def create_examples(worker_id):
        p_done = 0
        n_done = 0
        while True:
            for v0, v1 in tqdm(zip(videos0, videos1)):
                try:
                    frames, audio, fps = get_example_original("../recorded/1/" + v1)
                    if audio.shape[0] == AUDIO_FRAMES:
                        mfcc, landmarks = extract(frames, audio)
                        #print(mfcc.shape, landmarks.shape)
                        joblib.dump((mfcc, landmarks, 1), f"./features_24fps/pos_{worker_id}_{p_done}.jbl")
                        p_done += 1
                except Exception as e:
                    traceback.print_exc()
                    print(v0)
                    pass
                try:
                    frames, audio, fps = get_example_original("../recorded/0/" + v0)
                    if audio.shape[0] == AUDIO_FRAMES:
                        mfcc, landmarks = extract(frames, audio)
                        #print(mfcc.shape, landmarks.shape)
                        n_done += 1
                        joblib.dump((mfcc, landmarks, 0), f"./features_24fps/neg_{worker_id}_{n_done}.jbl")
                except Exception as e:
                    print(e)
                    pass

    Parallel(n_jobs=-1)(delayed(create_examples)(i) for i in range(start_worker_id, start_worker_id + NUM_THREADS))
    '''
    '''
    overlaps = [i / NUM_THREADS for i in range(NUM_THREADS)]
    def create_examples_sliding_window(videos0, videos1, worker_id, overlap):
        p_done = 0
        n_done = 0
        while True:
            for v0, v1 in tqdm(zip(videos0, videos1)):
                try:
                    features = extract_sliding_windows("../recorded/1/" + v1, worker_id, overlap)
                    joblib.dump((features, 1), f"./features_sliding_window/pos_{worker_id}_{p_done}.jbl")
                    p_done += 1
                except Exception as e:
                    traceback.print_exc()
                    print(v0)
                    pass
                try:
                    features = extract_sliding_windows("../recorded/1/" + v0, worker_id, overlap)
                    joblib.dump((features, 0), f"./features_sliding_window/neg_{worker_id}_{p_done}.jbl")
                    n_done += 1
                except Exception as e:
                    traceback.print_exc()
                    print(v1)
                    pass
    Parallel(n_jobs=-1)(delayed(create_examples_sliding_window)(deepcopy(videos0), deepcopy(videos1), i, overlap) for i, overlap in zip(range(start_worker_id, start_worker_id + NUM_THREADS), overlaps))
    '''
    features = extract_sliding_windows("../recorded/0/" + videos0[0])
    print(features.shape)
