# whisper-at-api

## Usage

### Installing the prerequisites

```bash
pip install -r requirements.txt
```

### Running the API

You have to rename `example.env` to `.env` and source it

```bash
python app.py
```

#### Using docker-compose

You can also use the included docker compose file to directly spin up the app and an s3 minio server

```bash
docker compose up -d
```

### Making requests to the api

#### Curl example

You have to have an audio file inside your object storage named case_closed.wav in this case

```bash
curl --request POST \
  --url 'http://127.0.0.1:5000/?object=case_closed.wav'
```
