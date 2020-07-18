from predict_video import predict_video_sliding_window, convert_video, get_clfs
from flask import Flask, render_template, request
import joblib
import os
import datetime

app = Flask(__name__, static_folder="./assets")


def clear():
   os.system("rm temp/*")

clf_path_video = "./mlp2_24fps.jbl"
#clf_path_video = "./automl_small_1s_24fps.jbl"
clfs_video = get_clfs(clf_path_video)


@app.route('/webcam_api', methods = ['POST'])
def webcam_api():
    if request.method == 'POST':
        print(request.form, request.files)
        timestamp = datetime.datetime.now().strftime("%Y_%m_%m_%H_%M_%S_%f")
        f = request.files['video']
        f.save(f"temp/{f.filename}_{timestamp}.webm")
        convert_video(f"temp/{f.filename}_{timestamp}.webm", f"temp/temp_{timestamp}.mp4")
        
        last30, out = predict_video_sliding_window(clfs_video, f"temp/temp_{timestamp}.mp4", f"temp/temp_{timestamp}.wav")
        #os.system(f"rm temp/temp_{timestamp}*")
        print(out, last30)
        #clear()
        return {'prediction': out[0][0] * 100, 'prediction_last30': last30[0][0] * 100}

if __name__ == "__main__":
    app.run(port=8000, debug = True)