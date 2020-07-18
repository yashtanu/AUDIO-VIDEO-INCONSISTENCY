from predict_video import predict_video_sliding_window, convert_video, get_clfs
from flask import Flask, render_template, request
import joblib
import os
import datetime

app = Flask(__name__, static_folder="./assets")

def clear():
   os.system("rm temp/*")

clf_path_video = "./mlp_24fps.jbl"
#clf_path_video = "./automl_small_1s_24fps.jbl"
clfs_video = get_clfs(clf_path_video)

@app.route('/', methods = ['POST', 'GET'])
def home():
   return render_template('index.html')

@app.route('/upload_file', methods = ['POST', 'GET'])
def upload_file():
   return render_template('upload_file.html')

@app.route('/livestream', methods = ['POST', 'GET'])
def livestream_view():
   return render_template('live_stream.html')

@app.route('/video_results', methods = ['GET', 'POST'])
def predict_on_video():
    if request.method == 'POST':
        f = request.files['video']
        f.save("temp/" + f.filename)
        
        convert_video("temp/" + f.filename, "temp/temp.mp4")
        
        out, last30 = predict_video_sliding_window(clfs_video, "temp/temp.mp4", "temp/temp.wav")
        print(out, last30)
        #clear()
        return render_template("upload_file.html", data=round(out[0][0] * 100, 2), data2=round(last30[0][0] * 100, 2))

if __name__ == '__main__':
   app.run(debug = True)

