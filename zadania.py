import csv
from datetime import datetime
import logging
import os

import ephem
import logzero

from logzero import logger
from sense_hat import SenseHat

from picamera import PiCamera
from time import sleep

name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   19029.34944157  .00000994  00000-0  22959-4 0  9991"
line2 = "2 25544  51.6438 332.9972 0003094  62.2964  46.0975 15.54039537 97480"

sense = SenseHat()

dir_path = os.path.dirname(os.path.realpath(__file__)) # sciezka w ktorej znajduje sie ten skrypt

iss_geo = ephem.readtle(name, line1, line2) # obiekt do obliczania położenia stacji

start_time = datetime.datetime.now() # TODO: zapisz czas startu eksperymentu (za pomocą biblioteki datetime), przykład w CodeLabie

first_acc_measurement = sense.get_accelerometer_raw()

def configure_logging():
    logzero.logfile(dir_path + "/logfile.log")
    logger.name = "AstroPi"
    formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s')
    logzero.formatter(formatter)


def is_experiment_ongoing():

    """
    TODO: Napisz metodę sprawdzajaca, czy twoj eksperyment trwa, czyli czy aktualny czas jest mniejszy niż start_time + 3h.
    TODO: Warto odliczać nie dokładnie do 3h, tylko założyć jakiś margines, np 2h 59min, żeby miec pewność że nie przekroczymy czasu
    :return: True jeśli czas eksperymentu jeszcze się nie skończył, False w przeciwnym przypadku
    """

def get_iss_location():
    """
    TODO: Napisz metode obliczającą aktualne położenie ISS i zwracającą je w formie słownika z kluczami lat i lon
    TODO: przykladowo: {"lat": 50.13, "lon": 12.23}
    TODO: Uzyj do tego utworzonego wyzej obiektu iss_geo, możesz też podejrzeć wyciąganie szerokości i długości w CodeLabie
    """
    pass


def take_photo_of_earth():
    camera.start_preview()
    time.sleep(2)
    camera.capture('/home/pi/Desktop/%.jpg' % datetime.datetime.now())
    camera.stop_preview()


    """
    TODO: Metoda robiąca zdjęcie za pomocą PiCamery
    TODO: Najlepiej, żeby zapisywała zdjęcie pod jakąś sensowną, unikalną nazwą (na przykład aktualny czas)
    """

def is_accelerating():
    acceleration_now = sense.get_accelerometer_raw()
    wynik1 = abs(first_acc_measurement['x']) - abs(acceleration_now['x'])
    wynik2 = abs(first_acc_measurement['y']) - abs(acceleration_now['y'])
    wynik3 = abs(first_acc_measurement['z']) - abs(acceleration_now['z'])
    a = True
    if wynik1 >= 0.05 | wynik2 >= 0.05 | wynik3 >= 0.05:
        a = True
    else:
        a = False
    return a
    #"""
    #TODO: Metoda porownujaca aktualne wskazanie akcelerometru z wynikiem zapisanym na poczatku dzialania programu
    #TODO: Pamietaj, żeby porównać wszystkie 3 wymiary, uzywajac wartosci bezwzględnej - metoda abs()
    #:return: True jeśli przyspieszenie w którymkolwiek wymiarze różni się od początkowego o np. 0.05
    #"""

def get_time_str():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    #"""
    #Metoda zwracajaca string z aktualnym czasem (z dokladnoscia do milisekund)
    #:return:
    #"""

def write_csv_header():
    #"""
    #Metoda zapisujaca do pliku csv naglowek z kolumn interesujacych nas pomiarow
    #"""
    header = ['time', 'lat', 'lon',
              'acc_raw_x', 'acc_raw_y', 'acc_raw_z',
              'gyro_raw_x', 'acc_raw_y', 'acc_raw_z',
              'compass_raw_x', 'compass_raw_y', 'compass_raw_z',
              'pitch', 'roll', 'yaw',
              'pitch_acc', 'roll_acc', 'yaw_acc',
              'pitch_gyro', 'roll_gyro', 'yaw_gyro',
              'yaw_compass']
    csv_writer.writerow(header)

def write_all_measurements():
    #"""
    #TODO: analogicznie do write_csv_header, napisz metode tworzaca liste wynikow pomiarow, w kolejnosci zgodnej z nazwami kolumn
    #TODO: I zapisujaca ja do pliku za pomoca csv_writer.write_row(lista_wynikow)
    #TODO: Uzyj tutaj pomiarow z senseHata, dlugosci i szerokosci uzyskanej w metodzie get_iss_location() i czasu uzyskanego w get_time_str()
    #:return:
    #"""

csv_file_path = dir_path + "/data.csv"

configure_logging()
with open(csv_file_path, mode="w") as output_file:
    # Utworzenie obiektu używanego do zapisywania wyników do CSV
    csv_writer = csv.writer(output_file, delimiter=",")
    write_csv_header()
    logger.info("Test loggera")
    # TODO: Spróbuj umieścić tu prototypową główną pętle programu, uzywajac metod is_experiment_ongoing(), is_accelerating()
    # TODO: Wewnątrz pętli zapisuj wyniki do pliku csv za pomoca write_all_measurements() - tak jak mówiliśmy, najlepiej przez cały czas trwania eksperymentu
    # TODO: Używaj np. logger.info("Rozpoczeto przyspieszanie") do logowania ważnych momentów, odswieżaj wiadomość wyswietlaną na ekranie LED
    # TODO: Mozesz tez zaproponowac w którym momencie wykonywac zdjecia, logowac do loggera polozenie geograficzne stacji w poszczegolnych fazach
    # TODO: Może wpadniesz jeszcze na jakieś inne ciekawe pomysły.
