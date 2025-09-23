import requests
import json
import csv
import os
from datetime import datetime


class LibreViewAPI:
    def __init__(self):
        self.base_url = "https://api.libreview.io"
        self.token = None
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'product': 'llu.android',
            'version': '4.7'
        }
        self.csv_filename = "libre_view_sensor_data.csv"

    def save_to_csv(self, data_type, data):
        """Save data to CSV file"""
        try:
            file_exists = os.path.isfile(self.csv_filename)

            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                if data_type == "connections":
                    if not file_exists:
                        # Write header for connections data
                        writer.writerow([
                            'Timestamp', 'Data Type', 'Patient ID', 'First Name', 'Last Name',
                            'Status', 'Gender', 'Date of Birth', 'Target Low', 'Target High'
                        ])

                    for connection in data:
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Connection',
                            connection.get('patientId', 'N/A'),
                            connection.get('firstName', 'N/A'),
                            connection.get('lastName', 'N/A'),
                            connection.get('status', 'N/A'),
                            connection.get('gender', 'N/A'),
                            connection.get('dateOfBirth', 'N/A'),
                            connection.get('targetLow', 'N/A'),
                            connection.get('targetHigh', 'N/A')
                        ])
                    print(f"✅ Connection data saved to {self.csv_filename}")

                elif data_type == "glucose_current":
                    if not file_exists:
                        # Write header for current glucose data
                        writer.writerow([
                            'Timestamp', 'Data Type', 'Patient ID', 'Glucose Value (mg/dL)',
                            'Trend', 'Measurement Time', 'Status', 'Is High', 'Is Low'
                        ])

                    glucose_measurement = data.get('connection', {}).get('glucoseMeasurement', {})
                    if glucose_measurement:
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Current Glucose',
                            data.get('connection', {}).get('patientId', 'N/A'),
                            glucose_measurement.get('ValueInMgPerDl', 'N/A'),
                            glucose_measurement.get('TrendMessage', 'N/A'),
                            glucose_measurement.get('Timestamp', 'N/A'),
                            'HIGH' if glucose_measurement.get('isHigh') else 'LOW' if glucose_measurement.get(
                                'isLow') else 'NORMAL',
                            glucose_measurement.get('isHigh', False),
                            glucose_measurement.get('isLow', False)
                        ])
                    print(f"✅ Current glucose data saved to {self.csv_filename}")

                elif data_type == "glucose_historical":
                    if not file_exists:
                        # Write header for historical glucose data
                        writer.writerow([
                            'Timestamp', 'Data Type', 'Patient ID', 'Glucose Value (mg/dL)',
                            'Measurement Time', 'Graph Index'
                        ])

                    graph_data = data.get('data', {}).get('graphData', [])
                    patient_id = data.get('data', {}).get('connection', {}).get('patientId', 'N/A')

                    for i, reading in enumerate(graph_data):
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Historical Glucose',
                            patient_id,
                            reading.get('ValueInMgPerDl', 'N/A'),
                            reading.get('Timestamp', 'N/A'),
                            reading.get('GraphIndex', 'N/A')
                        ])
                    print(f"✅ Historical glucose data ({len(graph_data)} readings) saved to {self.csv_filename}")

                elif data_type == "sensor_info":
                    if not file_exists:
                        # Write header for sensor information
                        writer.writerow([
                            'Timestamp', 'Data Type', 'Patient ID', 'Device ID',
                            'Serial Number', 'Sensor State', 'Sensor Age'
                        ])

                    sensor = data.get('connection', {}).get('sensor', {})
                    if sensor:
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Sensor Info',
                            data.get('connection', {}).get('patientId', 'N/A'),
                            sensor.get('deviceId', 'N/A'),
                            sensor.get('sn', 'N/A'),
                            sensor.get('sensorState', 'N/A'),
                            sensor.get('sensorAge', 'N/A')
                        ])
                    print(f"✅ Sensor information saved to {self.csv_filename}")

        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")

    def step1_login(self, email, password):
        """Step 1: Initial login"""
        print("=" * 60)
        print("STEP 1: INITIAL LOGIN")
        print("=" * 60)

        login_url = f"{self.base_url}/llu/auth/login"
        login_data = {"email": email, "password": password}

        print("🔐 Logging in...")
        print(f"Email: {email}")

        try:
            response = requests.post(login_url, headers=self.headers, json=login_data)
            print(f"📡 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')

                if status == 0:
                    print("✅ LOGIN SUCCESSFUL - No acceptance required")
                    self.token = data.get('ticket', {}).get('token')
                    return True, data
                elif status == 4:
                    print("⚠️ Acceptance required (Status 4)")
                    step_type = data.get('data', {}).get('step', {}).get('type')
                    self.token = data.get('data', {}).get('authTicket', {}).get('token')
                    return step_type, data
                else:
                    print(f"❌ Login failed with status: {status}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def step2_accept_document(self, doc_type):
        """Step 2: Accept Terms of Use or Privacy Policy"""
        print("\n" + "=" * 60)
        print(f"STEP 2: ACCEPT {doc_type.upper()}")
        print("=" * 60)

        accept_url = f"{self.base_url}/auth/continue/{doc_type}"

        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.token}"

        doc_name = "Terms of Use" if doc_type == "tou" else "Privacy Policy"
        print(f"📝 Accepting {doc_name}...")

        try:
            response = requests.post(accept_url, headers=headers)
            print(f"📡 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')

                if status == 0:
                    print(f"✅ {doc_name.upper()} ACCEPTED SUCCESSFULLY!")
                    new_token = data.get('data', {}).get('authTicket', {}).get('token')
                    if new_token:
                        self.token = new_token
                    return True, data
                elif status == 4:
                    next_step = data.get('data', {}).get('step', {}).get('type')
                    print(f"⚠️ Next acceptance required: {next_step}")
                    new_token = data.get('data', {}).get('authTicket', {}).get('token')
                    if new_token:
                        self.token = new_token
                    return next_step, data
                else:
                    print(f"❌ {doc_name} acceptance failed with status: {status}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def step3_final_login(self, email, password):
        """Step 3: Final login after all acceptances"""
        print("\n" + "=" * 60)
        print("STEP 3: FINAL LOGIN")
        print("=" * 60)

        login_url = f"{self.base_url}/llu/auth/login"
        login_data = {"email": email, "password": password}

        print("🔐 Final login...")

        try:
            response = requests.post(login_url, headers=self.headers, json=login_data)
            print(f"📡 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 0:
                    print("✅ FINAL LOGIN SUCCESSFUL!")
                    self.token = data.get('ticket', {}).get('token')
                    return True, data
                else:
                    print(f"❌ Final login failed with status: {data.get('status')}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def step4_get_connections(self):
        """Step 4: Get patient connections (sensors)"""
        print("\n" + "=" * 60)
        print("STEP 4: GET CONNECTIONS (SENSORS)")
        print("=" * 60)

        connections_url = f"{self.base_url}/llu/connections"

        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.token}"

        print("🔗 Getting sensor connections...")

        try:
            response = requests.get(connections_url, headers=headers)
            print(f"📡 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 0:
                    connections = data.get('data', [])
                    print(f"✅ FOUND {len(connections)} SENSOR CONNECTION(S)")

                    for i, connection in enumerate(connections):
                        print(f"\n📟 SENSOR {i + 1}:")
                        print(f"   Patient ID: {connection.get('patientId')}")
                        print(f"   Name: {connection.get('firstName')} {connection.get('lastName')}")
                        print(f"   Status: {connection.get('status')}")

                    # Save connections data to CSV
                    self.save_to_csv("connections", connections)

                    return True, connections
                else:
                    print(f"❌ Connections retrieval failed with status: {data.get('status')}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def step5_get_glucose_data(self, patient_id):
        """Step 5: Get glucose data from sensor"""
        print("\n" + "=" * 60)
        print("STEP 5: GET GLUCOSE DATA FROM SENSOR")
        print("=" * 60)

        glucose_url = f"{self.base_url}/llu/connections/{patient_id}/graph"

        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.token}"

        print(f"📈 Getting glucose data from sensor...")

        try:
            response = requests.get(glucose_url, headers=headers)
            print(f"📡 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 0:
                    print("✅ GLUCOSE DATA RETRIEVED SUCCESSFULLY!")

                    # Extract glucose data
                    glucose_data = data.get('data', {})
                    connection = glucose_data.get('connection', {})
                    glucose_measurement = connection.get('glucoseMeasurement', {})

                    print("\n" + "🩸" * 20)
                    print("🎯 CURRENT GLUCOSE READING")
                    print("🩸" * 20)

                    if glucose_measurement:
                        value = glucose_measurement.get('ValueInMgPerDl')
                        trend = glucose_measurement.get('TrendMessage', 'N/A')
                        timestamp = glucose_measurement.get('Timestamp', 'N/A')

                        print(f"🩸 Glucose Value: {value} mg/dL")
                        print(f"📊 Trend: {trend}")
                        print(f"⏰ Time: {timestamp}")

                        # Status indicator
                        is_high = glucose_measurement.get('isHigh', False)
                        is_low = glucose_measurement.get('isLow', False)

                        if is_high:
                            print("⚠️  STATUS: HIGH")
                        elif is_low:
                            print("⚠️  STATUS: LOW")
                        else:
                            print("✅ STATUS: NORMAL")

                    # Sensor information
                    sensor = connection.get('sensor', {})
                    if sensor:
                        print(f"\n📟 SENSOR INFORMATION:")
                        print(f"   Device ID: {sensor.get('deviceId')}")
                        print(f"   Serial Number: {sensor.get('sn')}")

                    # Historical data summary
                    graph_data = glucose_data.get('graphData', [])
                    print(f"\n📅 HISTORICAL DATA: {len(graph_data)} readings available")

                    # Show latest 3 readings
                    if graph_data:
                        print(f"\n🕒 LATEST 3 READINGS:")
                        for i, reading in enumerate(graph_data[-3:]):
                            time = reading.get('Timestamp', 'N/A')
                            value = reading.get('ValueInMgPerDl', 'N/A')
                            print(f"   {i + 1}. {value} mg/dL at {time}")

                    # Save all data to CSV
                    self.save_to_csv("glucose_current", glucose_data)
                    self.save_to_csv("glucose_historical", {"data": glucose_data})
                    self.save_to_csv("sensor_info", glucose_data)

                    return True, data
                else:
                    print(f"❌ Glucose data retrieval failed with status: {data.get('status')}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def get_sensor_data(self, email, password):
        """Get sensor data directly"""
        print("🚀 STARTING LIBREVIEW SENSOR DATA RETRIEVAL")
        print("=" * 60)

        # Initialize CSV file (clear previous content if needed)
        try:
            if os.path.exists(self.csv_filename):
                os.remove(self.csv_filename)
                print(f"🗑️  Previous CSV file removed: {self.csv_filename}")
        except:
            pass

        # Step 1: Initial login
        result, data = self.step1_login(email, password)

        if not result:
            return False

        # Step 2: Handle document acceptances
        if result in ["tou", "pp"]:
            current_step = result
            max_steps = 3

            for step_num in range(max_steps):
                print(f"\n📄 Acceptance step {step_num + 1}: {current_step.upper()}")
                result, data = self.step2_accept_document(current_step)

                if result is True:
                    print("✅ All documents accepted!")
                    break
                elif result in ["tou", "pp"]:
                    current_step = result
                else:
                    print("❌ Document acceptance failed")
                    return False

        # Step 3: Final login
        result, data = self.step3_final_login(email, password)
        if not result:
            return False

        # Step 4: Get connections (sensors)
        result, connections = self.step4_get_connections()
        if not result or not connections:
            print("❌ No sensor connections found")
            return False

        # Step 5: Get glucose data from first sensor
        first_patient_id = connections[0].get('patientId')
        result, glucose_data = self.step5_get_glucose_data(first_patient_id)

        if result:
            print(f"\n🎉 SENSOR DATA RETRIEVAL COMPLETED SUCCESSFULLY!")
            print(f"📊 All data saved to: {self.csv_filename}")
            return True
        else:
            return False


def main():
    # Your credentials
    EMAIL = "ranaweeranuwantha@gmail.com"
    PASSWORD = "Sam1sung$#@!"

    # Create API instance
    api = LibreViewAPI()

    # Get sensor data
    success = api.get_sensor_data(EMAIL, PASSWORD)

    if success:
        print("\n✅ SENSOR DATA RETRIEVED AND SAVED SUCCESSFULLY!")
        print(f"📁 CSV file created: {api.csv_filename}")
        print("You can now open the CSV file in Excel or any spreadsheet application!")
    else:
        print("\n❌ Failed to retrieve sensor data.")


if __name__ == "__main__":
    main()