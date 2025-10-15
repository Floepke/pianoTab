DEBUG = True
def log(*args, **kwargs):
    if DEBUG:
        print("[LOG]", *args, **kwargs)