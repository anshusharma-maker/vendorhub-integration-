vendorhub-integration

Overview

This project connects our application with a fake ERP called VendorHub.

The cron job gets vendor data from VendorHub and saves it in our database as supplier records.

When a user submits a DAN request or a case unit request, the request is put into RabbitMQ. The consumers pick the request from the queue, send it to VendorHub and update the result in our database.

Setup

1. Create and activate the virtual environment

python3 -m venv .venv
source .venv/bin/activate

2. Install the required Python libraries

pip install pymongo pika requests apscheduler python-dotenv pytest responses

3. Create the environment file

cp .env.example .env

4. Start MongoDB and RabbitMQ

docker compose up -d

5. Seed the database

python -m scripts.seed

Run Fake VendorHub

cd fake-vendorhub
npm install
sails lift --port 9000

Run Vendor Sync

From the project root:

python -m cron.vendor_sync --run-now

The cron normally runs every day at 00:30 IST.

Run DAN Consumer

python -m consumers.dan_consumer

Run Unit Consumer

python -m consumers.unit_consumer

Send a DAN request to the queue

python scripts/send_to_queue.py --dan <DAN_ID> --user <USER_ID>

Send a case to the queue

python scripts/send_to_queue.py --case <CASE_ID> --user <USER_ID>

Run Tests

python -m pytest -q

Tasks Not Finished

I have not finished writing the tests yet.
