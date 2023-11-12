import os
from datetime import timedelta
import whisper_at as whisper
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from flask import Flask
from flask import request

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv('AWS_DOMAIN'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    config=Config(signature_version='s3v4'),
)

app = Flask(__name__)

audio_tagging_time_resolution = 10
model = whisper.load_model(os.getenv('WHISPER_MODEL'))

def segments_to_str(text_segments) -> str:
    srt_asr_subtitles = ""
    for segment in text_segments:
        startTime = str(0)+str(timedelta(seconds=int(segment['start'])))+',000'
        endTime = str(0)+str(timedelta(seconds=int(segment['end'])))+',000'
        text = segment['text']
        segmentId = segment['id']+1
        if text != "":
            segment = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"
        else:
            segment = f"{segmentId}\n{startTime} --> {endTime}\n{text}\n\n"
        srt_asr_subtitles += segment
    return srt_asr_subtitles

@app.route("/", methods=['POST'])
def route():
    try:
        request.args["object"]
    except KeyError:
        return "No object provided"

    try:
        s3.head_object(Bucket='videos', Key=request.args["object"])
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return 'object not found'
    try:
        url = s3.generate_presigned_url('get_object', Params={'Bucket': "videos",
                                                              'Key': request.args["object"]},
                                                      ExpiresIn=3600)
    except ClientError as e:
        print(e)
        return None

    result = model.transcribe(url, at_time_res=audio_tagging_time_resolution)
    text_segments = result['segments']
    audio_tag_result = whisper.parse_at_label(result, language='follow_asr', top_k=5, p_threshold=-1, include_class_list=list(range(527)))
    
    # Convert text annotations to a whisper like array for latter conversion to srt
    all_seg = []
    id = 0
    for segment in audio_tag_result:
        cur_start = segment['time']['start']
        cur_end = segment['time']['end']
        cur_tags = segment['audio tags']
        cur_tags = [x[0] for x in cur_tags]
        cur_tags = '; '.join(cur_tags)
        all_seg.append({"id": id, "start": cur_start, "end": cur_end, "text": cur_tags})
        id += 1

    srt_asr_subtitles = segments_to_str(text_segments)
    srt_annotation_subtitles = segments_to_str(all_seg)

    response = {
        "srt_asr_subtitles": srt_asr_subtitles,
        "srt_annotation_subtitles": srt_annotation_subtitles
    }

    return response

if __name__ == "__main__":
    app.run(debug=True)
