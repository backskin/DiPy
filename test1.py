from backslib import create_video_slideshow, crop_all, resize_all


# create_video_slideshow('test-dataset', 1.5)
# create_video_slideshow()
# resize_all('real-photos', 'rf-1', 720, 540)
# crop_all('rf-1', 'rf-2', 90)
# resize_all('rf-2', 'rf-3', 640, 480)
# create_video_slideshow('rf-3', 1.5)

def print_max(name, file):
    max_value = 0.0
    for line in file.readlines():
        val = line.split()[2]
        if float(val) > max_value:
            max_value = float(val)
    print(name + ' ' + str(max_value))


def eee_boii():
    import os
    for name in os.listdir('resources\\templogs'):
        log = open('resources\\templogs'+os.sep+name, 'r')
        print_max(name, log)


log_time = open('log_time.txt', 'w')
log_temp = open('log_temp.txt', 'w')
orig_log = open('CPUtemp_20200429.log', 'r')

for line in orig_log.readlines():
    subs = line.split()
    time_c = subs[0]
    temp_c = subs[2]
    temp_c = temp_c.replace('.', ',')
    log_time.write(time_c+'\n')
    log_temp.write(temp_c+'\n')
log_temp.close()
log_time.close()
orig_log.close()

# eee_boii()