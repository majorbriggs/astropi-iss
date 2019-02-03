import csv
import time
import os
from datetime import datetime
from datetime import timedelta
import logzero
from logzero import logger
import logging
import ephem
from sense_hat import SenseHat
from picamera import PiCamera
# Dane kalibracyjne do biblioteki podającej położenie geograficzne ISS

name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   19027.35358524  .00000676  00000-0  17987-4 0  9999"
line2 = "2 25544  51.6438 341.6552 0004773 319.7834 175.1710 15.53197810153372"

# Inicjalizacja biblioteki podającej położenie ISS
iss_geo = ephem.readtle(name, line1, line2)

sense = SenseHat()

camera = PiCamera()

experiment_time = timedelta(seconds=5)

dir_path = os.path.dirname(os.path.realpath(__file__))
csv_data_path = dir_path + "/data.csv"

# Próg od którego uznajemy, że stacja zaczęła przyspieszać
threshold = 0.05

# Czas pomiędzy zapisami pomiarów
pause_time = 0.1

# zapis momentu uruchomienia skryptu
start_time = datetime.utcnow()


def get_iss_location():
    iss_geo.compute()
    return {"lat": iss_geo.sublat, "lon": iss_geo.sublong}


def get_time_str():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def write_csv_header():
    header = ['time', 'lat', 'lon',
              'acc_raw_x', 'acc_raw_y', 'acc_raw_z',
              'gyro_raw_x', 'acc_raw_y', 'acc_raw_z',
              'compass_raw_x', 'compass_raw_y', 'compass_raw_z',
              'pitch', 'roll', 'yaw',
              'pitch_acc', 'roll_acc', 'yaw_acc',
              'pitch_gyro', 'roll_gyro', 'yaw_gyro',
              'yaw_compass']
    csv_writer.writerow(header)


def get_all_measurements():
    time = get_time_str()
    location = get_iss_location()
    acceleration_raw = sense.accelerometer_raw
    gyro_raw = sense.gyro_raw
    compass_raw = sense.compass_raw

    orientation = sense.orientation
    orientation_acc = sense.accelerometer
    orientation_gyro = sense.gyroscope
    orientation_compass = sense.compass
    results = [
        time,
        location['lat'],
        location['lon'],
        acceleration_raw['x'],
        acceleration_raw['y'],
        acceleration_raw['z'],
        gyro_raw['x'],
        gyro_raw['y'],
        gyro_raw['z'],
        compass_raw['x'],
        compass_raw['y'],
        compass_raw['z'],
        orientation['pitch'],
        orientation['roll'],
        orientation['yaw'],
        orientation_acc['pitch'],
        orientation_acc['roll'],
        orientation_acc['yaw'],
        orientation_gyro['pitch'],
        orientation_gyro['roll'],
        orientation_gyro['yaw'],
        orientation_compass
    ]
    return results


def display_reboost_started():
    # TODO: wyświetl na ekranie LED, że przyspieszenie się rozpoczęło
    pass


def display_waiting_for_reboost():
    # TODO: wyświetl na ekranie LED, że czekamy na reboost
    pass


def dispay_reboost_finished():
    # TODO: wyświetl na ekranie LED, że reboost się skończył
    pass


def before_experiment_start():
    # akcje do wykonania przed startem eksperymentu
    results = get_all_measurements()
    csv_writer.writerow(results)
    location = get_iss_location()
    logger.info("Location: {}".format(location))
    take_photo_of_earth()
    display_waiting_for_reboost()


def reboost_started():
    # akcje do wykonania w momencie wykrycia rozpoczęcia przyspieszenia
    logger.info("Reboost started")
    take_photo_of_earth()
    display_reboost_started()


def reboost_finished():
    # akcje do wykonania w momencie wykrycia zakończenia przyspieszenia
    logger.info("Reboost finished")
    take_photo_of_earth()
    dispay_reboost_finished()


def check_if_accelerating():
    # sprawdzenie czy rozpoczęło się przyspieszanie (porównanie aktualnego pomiaru z początkowym)
    # abs - wartość bezwzględna
    new_measurement = sense.get_accelerometer_raw()
    diff_x = abs(new_measurement['x'] - first_acc_measurement['x'])
    diff_y = abs(new_measurement['y'] - first_acc_measurement['y'])
    diff_z = abs(new_measurement['z'] - first_acc_measurement['z'])
    # Uznajemy, że rozpoczęło się przyspieszanie jeśli różnica między początkowym przyspieszeniem a aktualnym
    # w którymkolwiek wymiarze (x, y, z) jest większa od progu ze zmiennej threshold
    return diff_x > threshold or diff_y > threshold or diff_z > threshold


def is_experiment_ongoing():
    # Sprawdzenie, czy od początku eksperymentu nie minął już zadany czas (z małym marginesem)
    return datetime.now() < start_time + experiment_time


def configure_logging():
    # Konfiguracja logowania do pliku
    logzero.logfile(dir_path + "/logfile.log")
    logger.name = "AstroPi"
    # Każda linijka będzie w formacie name, czas, poziom wiadomości (DEBUG, INFO, ERROR), treść wiadomości
    # standardowo "poziom" wiadomości loga określa jej "wagę" i wiąże się z tym jakiej metody loggera używamy
    # w tym skrypcie wszystkie wiadomości w logu mają poziom INFO (bo wywołujemy metodę logger.info("tresc wiadomosci") )
    # gdybyśmy chcieli wrzucić do loga informację o wystąpieniu jakiegoś błędu, użylibyśmy logger.error("tresc wiadomosci")
    formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s');
    logzero.formatter(formatter)


def take_photo_of_earth():
    camera.capture(dir_path + "/{}.jpg".format(get_time_str()))


configure_logging()

with open(csv_data_path, mode="w") as output_file:
    reboost_start_recorded = False
    reboost_finish_recorded = False
    reboost_ongoing = False

    # Utworzenie obiektu używanego do zapisywania wyników do CSV
    csv_writer = csv.writer(output_file, delimiter=",")
    write_csv_header()
    first_acc_measurement = sense.get_accelerometer_raw()

    # Zapisz poczatkowe wyniki
    before_experiment_start()

    while is_experiment_ongoing(): # sprawdzane przy każdym wykonaniu pętli czy t < 3h
        results = get_all_measurements()
        csv_writer.writerow(results)
        time.sleep(pause_time)  # Może nie jest potrzebne? ograniczamy w ten sposób ilość zebranych wyników.
        if not reboost_ongoing:
            reboost_ongoing = check_if_accelerating()
            if reboost_ongoing:  # moment wykrycia przyspieszenia
                reboost_started()
                reboost_start_recorded = True  # zapisujemy fakt wykrycia przyspieszenia (użyty na końcu w logu przy podsumowaniu)
        else:
            # Warto sprawdzić ile linijek wygenerowałoby się przez 15 minut przyspieszania stacji
            reboost_ongoing = check_if_accelerating()  # jeśli wykryjemy że przyspieszenie wróciło do wartości początkowej
            if not reboost_ongoing:
                reboost_finished()
                reboost_finish_recorded = True
    else:  # gdy miną już 3h eksperymentu
        logger.info("Experiment finished successfully")
        location = get_iss_location()
        logger.info("Location: {}".format(location))
        logger.info("Start of reboost recorded: {}".format(reboost_start_recorded))
        logger.info("Finish of reboost recorded: {}".format(reboost_finish_recorded))
        logger.info("Reboost ongoing when experiment ended: {}".format(reboost_ongoing))
        take_photo_of_earth()