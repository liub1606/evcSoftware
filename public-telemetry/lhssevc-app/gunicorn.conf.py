import multiprocessing

bind = "127.0.0.1:8080"
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
# multithreading is cooked because of global vars
