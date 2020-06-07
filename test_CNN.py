import os

from backslib.DetectorModule import DetectorModule
from backslib.CaffeDetector import CaffeDetector
from backslib.DarkNetDetector import DarkNetDetector
from backslib.TensorFlowDetector import TensorFlowDetector, TFLiteDetector

def get_images_list(pictures_folder) -> list:
    import os
    pics_list = []
    for name in os.listdir(pictures_folder):
        if name.endswith(".jpg"):
            pics_list.append(name)
    return pics_list


def load_true_values() -> list:
    import os
    values_file = open('test-dataset'+os.sep+'true_data.txt', 'r')
    output = []
    for line in values_file.readlines():
        output.append(int(line))
    return output


def test_detector(detector: DetectorModule, name:str):
    from datetime import datetime
    from time import time
    from backslib.DetectorModule import draw_rectangle
    import cv2
    import os
    detector.__startup__()
    detector.activate()
    folder_access_rights = 0o755
    test_folder = 'test-dataset'
    if not os.path.exists(test_folder+os.sep+name):
        os.mkdir(test_folder+os.sep+name, folder_access_rights)
    true_values = load_true_values()
    mAP = 0.0
    people_count = 0
    i = 0
    output_wins = open(test_folder+os.sep+name+os.sep+'test_0_wins.txt', 'w')
    output_hits = open(test_folder+os.sep+name+os.sep+'test_1_hits.txt', 'w')
    output_fp = open(test_folder+os.sep+name+os.sep+'test_2_false_positive.txt', 'w')
    output_fn = open(test_folder+os.sep+name+os.sep+'test_3_false_negative.txt', 'w')
    output_time = open(test_folder+os.sep+name+os.sep+'test_4_time.txt', 'w')
    output_map = open(test_folder+os.sep+name+os.sep+'test_5_mAP.txt', 'w')
    for image_name in get_images_list(test_folder):
        frame = cv2.imread(test_folder + os.sep + image_name)
        start_time = time()
        data = detector.get_person_detection(frame)
        work_time = time() - start_time
        true_frame = frame.copy()
        for box in data:
            people_count += 1
            mAP += box[1]
            draw_rectangle(true_frame, box[0], thickness=3)
        cv2.imwrite(test_folder + os.sep + name + os.sep + image_name, true_frame)
        founds_on_image = len(data)
        win = str(founds_on_image / max(1, true_values[i])).replace('.', ',')
        output_wins.write(win+'\n')
        output_hits.write(str(founds_on_image)+'\n')
        fp = str(max(0, founds_on_image-true_values[i])).replace('.', ',')
        output_fp.write(fp + '\n')
        fn = str(max(0, true_values[i]-founds_on_image)).replace('.', ',')
        output_fn.write(fn + '\n')
        work_time = str(work_time).replace('.', ',')
        output_time.write(work_time+'\n')
        i += 1
    aver_precision = str(mAP / max(1, people_count)).replace('.', ',')
    output_map.write(aver_precision)
    output_wins.close()
    output_hits.close()
    output_fp.close()
    output_fn.close()
    output_time.close()
    output_map.close()

    print(name+' OK')


networks_folder = 'neuralnetworks'

name_1 = 'caffe-mobilenet-ssdlite'
name_2 = 'caffe-vggnet-coco-300'
name_3 = 'caffe-vggnet-voc-300'
name_4 = 'tflite-coco-ssd'
name_5 = 'tf-mobilenet-ssd'
name_6 = 'tf-mobilenet-ssdlite'
name_7 = 'yolo3-coco'
name_8 = 'yolo3-tiny'

# det_1 = CaffeDetector(networks_folder+os.sep+name_1, 0.2, 0.007843, 15)
# det_2 = CaffeDetector(networks_folder+os.sep+name_2, 0.3, 1.0, 1)
# det_3 = CaffeDetector(networks_folder+os.sep+name_3, 0.3, 1.0, 15)
# det_4 = TFLiteDetector(networks_folder+os.sep+name_4, 0.25, corrector=load_true_values())
det_5 = TensorFlowDetector(networks_folder+os.sep+name_5, 0.4, 1)
# det_6 = TensorFlowDetector(networks_folder+os.sep+name_6, 0.4, 1)
# det_7 = DarkNetDetector(networks_folder+os.sep+name_7, 0.4)
# det_8 = DarkNetDetector(networks_folder+os.sep+name_8, 0.15)

# test_detector(det_1, name_1)
# test_detector(det_2, name_2)
# test_detector(det_3, name_3)
# test_detector(det_4, name_4)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
test_detector(det_5, name_5)
# test_detector(det_6, name_6)
# test_detector(det_7, name_7)
# test_detector(det_8, name_8)
