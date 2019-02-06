import csv
import logging
import os
import time
from collections import deque
from datetime import datetime
from datetime import timedelta

import ephem
import logzero
from logzero import logger

from picamera import PiCamera
from sense_hat import SenseHat

name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   19027.35358524  .00000676  00000-0  17987-4 0  9999"
line2 = "2 25544  51.6438 341.6552 0004773 319.7834 175.1710 15.53197810153372"

iss_geo = ephem.readtle(name, line1, line2)

sense = SenseHat()

camera = PiCamera()

experiment_time = timedelta(hours=2, minutes=59)

start_time = datetime.utcnow()

start_str = start_time.strftime("%d%m%Y_%H%M%S") # czas początku eksperymentu w stringu, używany do stworzenia nazw plików z danymi i loga

dir_path = os.path.dirname(os.path.realpath(__file__))

csv_data_path = dir_path + "/data_{}.csv".format(start_str)
logfile_path = dir_path + "/log_{}.log".format(start_str)

threshold = 0.0005


# Tutaj tworzę trzy listy, które będą przechowywać maksymalnie 20 ostatnich wyników pomiarów
# będziemy tu wpisywać różnicę między aktualnym pomiarem, a pomiarem z początku eksperymentu
# dzięki temu będziemy mogli sprawdzać, czy średnia różnica w przeciągu ostatnich 20 pomiarów była większa niż próg i
# w ten sposób możemy wyeliminować przypadkowe przeskoki (między stanem przyspiesza / nie przyspiesza)
# tych trzech list używamy w funkcji check_if_accelerating
# deque to taka specjalna lista w pythonie, która mieści maksymalnie zadaną liczbę elementów, i usuwa najstarsze, jeśli
# dodajemy do niej kolejne
last_x_diffs = deque([], 20)
last_y_diffs = deque([], 20)
last_z_diffs = deque([], 20)


# Tutaj dodałem jeszcze odczytywanie wysokości na krótej znajduje się stacja (elevation) - może nam się przyda
# do czegoś ta informacja
def get_iss_location():
    iss_geo.compute()
    return {"lat": iss_geo.sublat, "lon": iss_geo.sublong, "elev": iss_geo.elevation}


def get_time_str():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

# dodałem elev do headera (czyli będziemy mieć dodatkową kolumnę na informację o wysokości na jakiej jest stacja)
def write_csv_header():
    header = ['time', 'lat', 'lon', 'elev',
              'acc_raw_x', 'acc_raw_y', 'acc_raw_z',
              'gyro_raw_x', 'acc_raw_y', 'acc_raw_z',
              'compass_raw_x', 'compass_raw_y', 'compass_raw_z',
              'pitch', 'roll', 'yaw',
              'pitch_acc', 'roll_acc', 'yaw_acc',
              'pitch_gyro', 'roll_gyro', 'yaw_gyro',
              'yaw_compass']
    csv_writer.writerow(header)


# Teraz różnicę między aktualnym pomiarem,
# a pomiarem średnim z początku eksperymentu, zapisujemy do tych "rejestrów"
# last_x_diffs, last_y_diffs, last_z_diffs
# te rejestry same dbają o to, żeby trzymać tylko 20 ostatnich wyników
# (dlatego, że użyliśmy tego obiektu deque, a nie zwykłej listy
# Poza tym do wyników dopisujemy też elev (wysokość) stacji
def get_all_measurements():
    time = get_time_str()
    location = get_iss_location()
    acceleration_raw = sense.accelerometer_raw

    diff_x = abs(acceleration_raw['x'] - first_acc_measurement['x'])
    diff_y = abs(acceleration_raw['y'] - first_acc_measurement['y'])
    diff_z = abs(acceleration_raw['z'] - first_acc_measurement['z'])

    last_x_diffs.append(diff_x)
    last_y_diffs.append(diff_y)
    last_z_diffs.append(diff_z)

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
        location['elev'],
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
    sense.show_message("Reboost has already started")


def display_waiting_for_reboost():
    sense.show_message("Waiting for reboost")


def dispay_reboost_finished():
    sense.show_message("Reboost finished")


def experiment_start():
    # akcje do wykonania przed startem eksperymentu
    logger.info("Experiment started")
    location = get_iss_location()
    logger.info("ISS Location: {}".format(location))
    take_photo_of_earth()
    logger.info("Waiting for reboost...")
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



# Tutaj sprawdzamy czy średnia różnica przyspieszeń zapisanych w tych rejestrach jest większa niż próg
def check_if_accelerating():
    average_x_diff = sum(last_x_diffs) / 20
    average_y_diff = sum(last_y_diffs) / 20
    average_z_diff = sum(last_z_diffs) / 20
    return average_x_diff > threshold or average_y_diff > threshold or average_z_diff > threshold


def is_experiment_ongoing():
    return datetime.utcnow() < start_time + experiment_time


def configure_logging():
    # Konfiguracja logowania do pliku
    logzero.logfile(dir_path + "/logfile.log")
    logger.name = "AstroPi"
    formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s');
    logzero.formatter(formatter)


#  Dodałem linijkę, która zapisuje do loga fakt zrobienia zdjęcia i podaje jego nazwę
def take_photo_of_earth():
    filename = "{}.jpg".format(datetime.utcnow().strftime("%d%m%Y_%H%M%S_%f")[:-3])
    logger.info("Taking photo: {}".format(filename))
    camera.capture(dir_path + "/" + filename)


configure_logging()



# Na samym początku eksperymentu, pomyślałem, że możemy zmierzyć średnie wskazanie akcelerometru przez 20 pomiarów
# To może nam pomóc uzyskać lepszą wartość odniesienia, do sprawdzenia, czy stacja przyspiesza
# czyli teraz, zmienna first_acc_measurement nie będzie przechowywać pierwszej zarejestrowanej wartości, tylko średnią z
# 20 pierwszych pomiarów
def get_average_zero_acceleration():
    acc_x = []
    acc_y = []
    acc_z = []
    number_of_measurements = 20
    logger.info("Measure average initial acceleration (sensor offset)")
    for i in range(number_of_measurements): # pętla 20 pomiarów
        acc_raw = sense.get_accelerometer_raw()
        acc_x.append(acc_raw["x"]) # dodajemy każdy pomiar do listy
        acc_y.append(acc_raw["y"])
        acc_z.append(acc_raw["z"])
        time.sleep(0.1)
    # na koniec obliczamy średnią wartość przyspieszenia w każdym wymiarze, i zapisujemy do słownika
    average_acc_zero = {"x": sum(acc_x) / number_of_measurements,
                        "y": sum(acc_y) / number_of_measurements,
                        "z": sum(acc_z) / number_of_measurements}
    logger.info("Average acc_zero: {}".format(average_acc_zero))
    return average_acc_zero

with open(csv_data_path, mode="w") as output_file:

    reboost_start_recorded = False
    reboost_finish_recorded = False
    reboost_ongoing = False
    registered_accelerations = 0 # będziemy też zliczać ile razy zarejestrowaliśmy początek i koniec przyspieszenia

    # Utworzenie obiektu używanego do zapisywania wyników do CSV
    csv_writer = csv.writer(output_file, delimiter=",")
    write_csv_header()

    experiment_start()

    first_acc_measurement = get_average_zero_acceleration()

    while is_experiment_ongoing():
        results = get_all_measurements()
        csv_writer.writerow(results)
        if not reboost_ongoing:
            reboost_ongoing = check_if_accelerating()
            if reboost_ongoing:  # moment wykrycia przyspieszenia
                reboost_started()
                registered_accelerations += 1
                reboost_start_recorded = True
        else:
            reboost_ongoing = check_if_accelerating()
            if not reboost_ongoing:
                reboost_finished()
                reboost_finish_recorded = True
    else:  # gdy miną już 3h eksperymentu
        logger.info("Experiment finished successfully")
        location = get_iss_location()
        logger.info("ISS Location: {}".format(location))
        logger.info("Acceleration start recorded: {}".format(reboost_start_recorded))
        logger.info("Acceleration finish recorded: {}".format(reboost_finish_recorded))
        logger.info("Number of registered acceleration periods: {}".format(registered_accelerations))
        logger.info("Reboost ongoing when experiment ended: {}".format(reboost_ongoing))
        take_photo_of_earth()
