verdictSubmit=false;
cnt=0;
data = [];
document.getElementById("rec").style.visibility="hidden";
function startRecording() {
	cnt=0;
	document.getElementById("startButton").disabled=true;
	var video = document.querySelector("#videoElement");
	
	var streamRecorder;
	var webcamstream;
	var verdict=false;
	if (navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ audio: true, video: true })
        .then(function (stream) {
            console.log('Stream data check::::', stream);
            video.srcObject  = stream;
            webcamstream = stream;

            var types = ["video/webm", 
             "audio/webm", 
             "video/webm\;codecs=vp8", 
             "video/webm\;codecs=daala", 
             "video/webm\;codecs=h264", 
             "audio/webm\;codecs=opus", 
             "video/mpeg",
             ];

			for (var i in types) { 
			  console.log( "Is " + types[i] + " supported? " + (MediaRecorder.isTypeSupported(types[i]) ? "Maybe!" : "Nope :(")); 
			  verdict=true;
			}
			console.log("verdict:"+verdict);
			if(verdict){
			document.getElementById("rec").style.visibility="visible";
			console.log('Starting now:', webcamstream);
			// streamRecorder = webcamstream.record();
			// setTimeout(sendStreamData, 2000);
			let recorder = new MediaRecorder(webcamstream, {
				mimeType: 'video/webm'
			});
			
		 
			recorder.ondataavailable = event => data.push(event.data);
			// recorder.ondataavailable = videoDataHandler;
			recorder.start(timeslice=128);

			console.log(recorder.state + " for " + (30000) + " seconds...");
			setTimeout(function() {
				recorder.stop();
				verdictSubmit=true;
                cnt=cnt+1;
			   //data = [];

				if(verdictSubmit && cnt==1){
					document.getElementById("loader").style.visibility="visible";
					console.log("Visible - verdictSubmit")
					console.log("Submit to server start rec");
                    postVideoToServer(new Blob(data.splice(0, data.length)));
                    document.getElementById("rec").style.visibility="hidden";
                    document.getElementById("startButton").disabled=false;
  
			}
				//recorder.start(timeslice=30000);
			}, 30000);
			console.log("Verdict Submit 1:"+verdictSubmit);
			
			verdictSubmit=false
			console.log("Verdict Submit start rec:"+verdictSubmit);
		}

				})
				.catch(function (error) {
					console.log("Something went wrong:", error);
				});
		
	}
	
}

// function stopRecorder(){
// 	  var video = document.querySelector("#videoElement");
	
// 	var stopVideo = document.querySelector("#stop");
// 	stop=document.getElementById("stop");
// 	stopVideo.addEventListener("click", stop, false);
//    function stop(e) {
//       var stream = video.srcObject;
//       var tracks = stream.getTracks();

//       for (var i = 0; i < tracks.length; i++) {
//         var track = tracks[i];
//         track.stop();
//       }
// 		verdictSubmit=true
// 		cnt=cnt+1;
// 		console.log("stop rec");
// 		console.log("Verdict Submit 2:"+verdictSubmit);
// 		if(verdictSubmit && cnt==1){
// 				console.log("Submit to server");
// 				postVideoToServer(new Blob(data.splice(0, data.length)));
// 			}
// 			verdictSubmit=false
// 			console.log("Verdict Submit stop rec:"+verdictSubmit);
// 		//postVideoToServer(new Blob(data.splice(0, data.length)));
//       video.srcObject = null;
//     }
// }


function videoDataHandler (event) {
    var blob = event.data;
    // document.getElementById(‘blob-video’).setAttribute(‘src’, window.URL.createObjectURL(blob));
};

function sendStreamData(data) {
    console.log('Final Values:', data);
    // streamRecorder = streamData.record();
    // streamRecorder.getRecordedData(postVideoToServer);
    postVideoToServer(data);
}

function postVideoToServer(videoblob) {
    // var data = {};
    // data.video = videoblob;
    // data.metadata = 'video metadata';
    // data.action = "upload_video";
    // console.log('DATA:', data);
    var formData = new FormData();
    formData.append('video', videoblob);
    fetch('http://127.0.0.1:5000/webcam_api', {
        method: 'POST',
        body: formData
    }).then(function(response) {
        console.log('Response 1:', response);
        return response.json();
    }).then(function(result) {
		
		tag = document.getElementById("result");
		tag.textContent = result['prediction'];
		
		tag2 = document.getElementById("result2");
		tag2.textContent = result['prediction_last30'];
		
		document.getElementById("loader").style.visibility="hidden";
        console.log("Hidden - API response")
					
        console.log('Final result:', result);
    })
}