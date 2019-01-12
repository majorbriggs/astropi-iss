from sense_hat import SenseHat
import csv
import time
from datetime import datetime

sense = SenseHat()
i = 1
try:
    with open("output.csv", mode="w") as output_file:
        csv_writer = csv.writer(output_file, delimiter="\t")
        header = ["i", "czas", "accx", "accy", "accz"]
        csv_writer.writerow(header)
        while True:
            acc = sense.get_accelerometer_raw()

            gyro = sense.get_gyroscope()
            accx = round(acc["x"], 4)
            accy = round(acc["y"], 4)
            accz = round(acc["z"], 4)
            czas = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
            results = [i, czas, accx, accy, accz]
            print(results)
            i += 1
            csv_writer.writerow(results)
            time.sleep(0.3)
except KeyboardInterrupt:
    pass
