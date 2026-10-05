vendorhub-integration

Overview

This project connects our application with a fake ERP called VendorHub.

The cron job gets vendor data from VendorHub and saves it in our database as supplier records.

When a user submits a DAN request or a case unit request, the request is put into RabbitMQ. The consumers pick the request from the queue, send it to VendorHub and update the result in our database.

Setup

1. Create and activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the required Python libraries

```bash
pip install pymongo pika requests apscheduler python-dotenv pytest responses
```

3. Create the environment file

```bash
cp .env.example .env
```

4. Start MongoDB and RabbitMQ

```bash
docker compose up -d
```

5. Seed the database

```bash
python -m scripts.seed
```

Run Fake VendorHub

```bash
cd fake-vendorhub
npm install
sails lift --port 9000
```

Run Vendor Sync

From the project root:

```bash
python -m cron.vendor_sync --run-now
```

The cron normally runs every day at 00:30 IST.

Run DAN Consumer

```bash
python -m consumers.dan_consumer
```

Run Unit Consumer

```bash
python -m consumers.unit_consumer
```

Send a DAN request to the queue

```bash
python scripts/send_to_queue.py --dan <DAN_ID> --user <USER_ID>
```

Send a case to the queue

```bash
python scripts/send_to_queue.py --case <CASE_ID> --user <USER_ID>
```

Run Tests

```bash
python -m pytest -q
```

Tasks Not Finished

I have not finished writing the tests yet.
