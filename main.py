import time
from Parser import Parser
from consts import *
import os
import ftplib

# ИНИЦИАЛИЗАЦИЯ

start_time = time.time()
print('Попытка соединения с FTP-сервером', FTP_HOST)
ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD)
print("Создание временной папки:", TMP_FOLDER_NAME)
try:
    os.mkdir("./tmp")
except FileExistsError:
    print("Временная папка уже существует")

# НАЧАЛО ПРОГРАММЫ

parser = Parser(ftp)
parser.start(9)

# КОНЕЦ ПРОГРАММЫ

print("Очистка временной папки:", TMP_FOLDER_NAME)
try:
    os.remove("./" + TMP_FOLDER_NAME + "/" + TMP_FILE_NAME)
except FileNotFoundError:
    print("Временная папка пуста")
print("Удаление временной папки")
try:
    os.rmdir("./" + TMP_FOLDER_NAME)
except FileNotFoundError:
    print("Папка уже удалена")

print("--- время выполнения %s ---" % (time.time() - start_time))
