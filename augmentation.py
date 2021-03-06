import cv2
import numpy as np
import random

def xywh2xyxy(box_xywh):
    box_xyxy = box_xywh.copy()
    box_xyxy[:, 0] = box_xywh[:, 0] - box_xywh[:, 2] / 2.
    box_xyxy[:, 1] = box_xywh[:, 1] - box_xywh[:, 3] / 2.
    box_xyxy[:, 2] = box_xywh[:, 0] + box_xywh[:, 2] / 2.
    box_xyxy[:, 3] = box_xywh[:, 1] + box_xywh[:, 3] / 2.
    box_xyxy = np.clip(box_xyxy, 0., 1.)
    return box_xyxy


def xyxy2xywh(box_xyxy):
    box_xywh = box_xyxy.copy()
    box_xywh[:, 0] = (box_xyxy[:, 0] + box_xyxy[:, 2]) / 2.
    box_xywh[:, 1] = (box_xyxy[:, 1] + box_xyxy[:, 3]) / 2.
    box_xywh[:, 2] = box_xyxy[:, 2] - box_xyxy[:, 0]
    box_xywh[:, 3] = box_xyxy[:, 3] - box_xyxy[:, 1]
    box_xywh = np.clip(box_xywh, 0., 1.)
    return box_xywh


def LetterBoxResize(img, dsize, bboxes=None, class_ids=None):
    original_height, original_width = img.shape[:2]
    target_width, target_height = dsize

    ratio = min(
        float(target_width) / original_width,
        float(target_height) / original_height)
    resized_height, resized_width = [
        round(original_height * ratio),
        round(original_width * ratio)
    ]

    img = cv2.resize(img, dsize=(resized_width, resized_height))

    pad_left = (target_width - resized_width) // 2
    pad_right = target_width - resized_width - pad_left
    pad_top = (target_height - resized_height) // 2
    pad_bottom = target_height - resized_height - pad_top

    # padding
    img = cv2.copyMakeBorder(img,
                             pad_top,
                             pad_bottom,
                             pad_left,
                             pad_right,
                             cv2.BORDER_CONSTANT,
                             value=(127, 127, 127))

    try:
        if img.shape[0] != target_height and img.shape[1] != target_width:  # 둘 중 하나는 같아야 함
            raise Exception('Letter box resizing method has problem.')
    except Exception as e:
        print('Exception: ', e)
        exit(1)

    if class_ids is not None and bboxes is not None:
        # padding으로 인한 객체 translation 보상
        bboxes[:, [0, 2]] *= resized_width
        bboxes[:, [1, 3]] *= resized_height

        bboxes[:, 0] += pad_left
        bboxes[:, 1] += pad_top

        bboxes[:, [0, 2]] /= target_width
        bboxes[:, [1, 3]] /= target_height

        return img, bboxes, class_ids, [original_width, original_height], [resized_width, resized_height], [pad_left, pad_top] 
    return img


def ColorJittering(img, delta_h=15, scale_s=.5, scale_v=.5):

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(float)
    
    img_hsv[..., 0] += random.randint(-delta_h, delta_h)
    img_hsv[..., 0] = np.clip(img_hsv[..., 0], 0, 179)

    img_hsv[..., 1] *= random.uniform(1. - scale_s, 1. + scale_s)
    img_hsv[..., 1] = np.clip(img_hsv[..., 1], 0, 255)

    img_hsv[..., 2] *= random.uniform(1. - scale_v, 1. + scale_v)
    img_hsv[..., 2] = np.clip(img_hsv[..., 2], 0, 255)

    img_hsv = img_hsv.astype(np.uint8)
    img = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)

    return img

def HorFlip(img, bboxes_xywh, p=0.5):
    if random.random() < p:
        img = cv2.flip(img, 1)#1이 호리즌탈 방향 반전
        bboxes_xywh[:, 0] = 1. - bboxes_xywh[:, 0]
        return img, bboxes_xywh
    return img, bboxes_xywh

def RandomTranslation(img, bboxes_xyxy, classes, p=1.0):
    if random.random() < p:
        height, width = img.shape[0:2]

        l_bboxes = round(width * np.min(bboxes_xyxy[:, 0]))
        r_bboxes = width-round(width * np.max(bboxes_xyxy[:, 2]))

        t_bboxes = round(height * np.min(bboxes_xyxy[:, 1]))
        b_bboxes = height-round(height * np.max(bboxes_xyxy[:, 3]))

        tx = random.randint(-l_bboxes, r_bboxes)
        ty = random.randint(-t_bboxes, b_bboxes)

        # translation matrix
        tm = np.float32([[1, 0, tx],
                         [0, 1, ty]])  # [1, 0, tx], [1, 0, ty]

        img = cv2.warpAffine(img, tm, (width, height), borderValue=(127, 127, 127))

        bboxes_xyxy[:, [0, 2]] += (tx / width)
        bboxes_xyxy[:, [1, 3]] += (ty / height)
        bboxes_xyxy = np.clip(bboxes_xyxy, 0., 1.)

        return img, bboxes_xyxy, classes
    return img, bboxes_xyxy, classes

def RandomScale(img, bboxes_xyxy, classes, p=1.0, threshold_w=32, threshold_h=32):
    
    if random.random() < p:
        img_h, img_w = img.shape[:2]
        
        min_bbox_w = np.min(bboxes_xyxy[:, 2] - bboxes_xyxy[:, 0]) * img_w
        min_bbox_h = np.min(bboxes_xyxy[:, 3] - bboxes_xyxy[:, 1]) * img_h

        if min_bbox_w < threshold_w or min_bbox_h < threshold_h:
            min_scale = 1.
        else:
            min_scale = np.maximum(threshold_w/min_bbox_w, threshold_h/min_bbox_h)

        max_bbox_w = np.max(bboxes_xyxy[:, 2] - bboxes_xyxy[:, 0]) * img_w
        max_bbox_h = np.max(bboxes_xyxy[:, 3] - bboxes_xyxy[:, 1]) * img_h

        max_scale = np.minimum(img_w/max_bbox_w, img_h/max_bbox_h)

        cx = img_w//2
        cy = img_h//2

        for _ in range(10):#maximum trial    
            random_scale = random.uniform(min_scale, max_scale)

            #센터 기준으로 확대 혹은 축소
            tx = cx - random_scale * cx
            ty = cy - random_scale * cy

            min_bbox_x = round(img_w * np.min(bboxes_xyxy[:, 0])) * random_scale + tx
            max_bbox_x = round(img_w * np.max(bboxes_xyxy[:, 2])) * random_scale + tx

            min_bbox_y = round(img_h * np.min(bboxes_xyxy[:, 1])) * random_scale + ty
            max_bbox_y = round(img_h * np.max(bboxes_xyxy[:, 3])) * random_scale + ty

            if min_bbox_x < 0 or max_bbox_x >= img_w:
                continue

            if min_bbox_y < 0 or max_bbox_y >= img_h:
                continue
 
            # # scale matrix
            sm = np.float32([[random_scale, 0, tx],
                            [0, random_scale, ty]])  # [1, 0, tx], [1, 0, ty]

            img = cv2.warpAffine(img, sm, (img_w, img_h), borderValue=(127, 127, 127))

            bboxes_xyxy *= random_scale
            bboxes_xyxy[:, [0, 2]] += (tx / img_w)
            bboxes_xyxy[:, [1, 3]] += (ty / img_h)
            bboxes_xyxy = np.clip(bboxes_xyxy, 0., 1.)

            return img, bboxes_xyxy, classes

    return img, bboxes_xyxy, classes

def RandomCropPreserveBBoxes(img, bboxes_xyxy, classes, p=1.0):
    if random.random() < p:
        height, width = img.shape[0:2]

        outer_l_bboxes = int(round(width * np.min(bboxes_xyxy[:, 0])))
        outer_r_bboxes = int(round(width * np.max(bboxes_xyxy[:, 2])))

        outer_t_bboxes = int(round(np.min(height * bboxes_xyxy[:, 1])))
        outer_b_bboxes = int(round(height * np.max(bboxes_xyxy[:, 3])))

        l = random.randint(0, outer_l_bboxes)
        t = random.randint(0, outer_t_bboxes)
        r = random.randint(outer_r_bboxes, width)
        b = random.randint(outer_b_bboxes, height)

        img = img[t:b, l:r]

        bboxes_xyxy[:, [0, 2]] *= width
        bboxes_xyxy[:, [1, 3]] *= height

        bboxes_xyxy[:, [0, 2]] -= l
        bboxes_xyxy[:, [1, 3]] -= t

        bboxes_xyxy[:, [0, 2]] /= (r-l)
        bboxes_xyxy[:, [1, 3]] /= (b-t)

        return img, bboxes_xyxy, classes
    return img, bboxes_xyxy, classes

def drawBBox(img, bboxes_xyxy):
    h, w = img.shape[:2]

    bboxes_xyxy[:, [0, 2]] *= w
    bboxes_xyxy[:, [1, 3]] *= h

    for bbox_xyxy in bboxes_xyxy:
        print(bbox_xyxy)
        cv2.rectangle(img,
                      (int(bbox_xyxy[0]), int(bbox_xyxy[1])),
                      (int(bbox_xyxy[2]), int(bbox_xyxy[3])),
                      (0, 255, 0),2)

def RandomCrop(img, bboxes_xyxy, classes, w_constraint=2, h_constraint=2, iou_constraint=0.55, p=1.0):
    if random.random() < p:
        img_h, img_w = img.shape[0:2]

        bboxes_w = (bboxes_xyxy[:, 2] - bboxes_xyxy[:, 0])*img_w
        bboxes_h = (bboxes_xyxy[:, 3] - bboxes_xyxy[:, 1])*img_h
        bboxes_area = bboxes_w * bboxes_h

        min_cropped_img_w = 0
        min_cropped_img_h = 0

        for _ in range(10):
            cropped_img_w = random.randint(min_cropped_img_w, img_w)
            cropped_img_h = random.randint(min_cropped_img_h, img_h)

            l = random.randint(0, img_w - cropped_img_w)
            t = random.randint(0, img_h - cropped_img_h)
            r = l + cropped_img_w
            b = t + cropped_img_h

            cropped_bboxes_xyxy = bboxes_xyxy.copy()

            cropped_bboxes_xyxy[:, [0, 2]] *= img_w
            cropped_bboxes_xyxy[:, [1, 3]] *= img_h

            cropped_bboxes_xyxy[:, [0, 2]] = np.clip(cropped_bboxes_xyxy[:, [0, 2]], l, r)
            cropped_bboxes_xyxy[:, [1, 3]] = np.clip(cropped_bboxes_xyxy[:, [1, 3]], t, b)

            cropped_bboxes_xyxy = cropped_bboxes_xyxy.astype(int)

            cropped_bboxes_w = cropped_bboxes_xyxy[:, 2] - cropped_bboxes_xyxy[:, 0] 
            cropped_bboxes_h = cropped_bboxes_xyxy[:, 3] - cropped_bboxes_xyxy[:, 1]
            cropped_bboxes_area = cropped_bboxes_w * cropped_bboxes_h

            valid_objects = (cropped_bboxes_w > w_constraint) & (cropped_bboxes_h > h_constraint)
            if np.count_nonzero(valid_objects) == 0:
                continue
            
            cropped_bboxes_area = cropped_bboxes_area[valid_objects]
            cropped_bboxes_xyxy = cropped_bboxes_xyxy[valid_objects]

            iou = cropped_bboxes_area/bboxes_area[valid_objects]
            if np.count_nonzero(iou < iou_constraint) > 0: #iou_constraint 퍼센트 이상 가려진 물체가 있으면 다시 RandomCrop, 너무 많이 Crop된걸 찾도록 학습시키면 상식적으로 이상혀~ 비주얼라이제이션 해보면 알음
                continue
            
            mask = np.zeros((img_h, img_w), dtype=np.uint8)
            mask[t:b, l:r] = 1
            img[mask == 0] = 127
            
            cropped_bboxes_xyxy = cropped_bboxes_xyxy.astype(np.float32)
            cropped_bboxes_xyxy[:, [0, 2]] /= img_w
            cropped_bboxes_xyxy[:, [1, 3]] /= img_h
            
            classes = classes[valid_objects]

            return img, cropped_bboxes_xyxy, classes
    return img, bboxes_xyxy, classes

if __name__ == '__main__':
    from numpy.random import RandomState
    prng = RandomState(21)

    while(True):
        img = cv2.imread("test_example/000017.jpg", cv2.IMREAD_COLOR)

        import dataset
        label = np.loadtxt("test_example/000017.txt",
                                  dtype=np.float32,
                                  delimiter=' ').reshape(-1, 5)

        classes, bboxes_xywh = label[:, 0:1], label[:, 1:]

        # bboxes_xyxy = xywh2xyxy(bboxes_xywh)

        # img, bboxes_xyxy, classes = RandomCrop(img, bboxes_xyxy, classes)
        #img, bboxes_xyxy, classes = RandomCropPreserveBBoxes(img, bboxes_xyxy, classes)
        
        # bboxes_xywh = xyxy2xywh(bboxes_xyxy)
        img, bboxes_xywh, classes, _ ,_ ,_ = LetterBoxResize(img, (608, 608), bboxes_xywh, classes)
        img, bboxes_xywh = HorFlip(img, bboxes_xywh)
        bboxes_xyxy = xywh2xyxy(bboxes_xywh)
        
        img, bboxes_xyxy, classes = RandomCrop(img, bboxes_xyxy, classes)
        img, bboxes_xyxy, classes = RandomTranslation(img, bboxes_xyxy, classes)
        img, bboxes_xyxy, classes = RandomScale(img, bboxes_xyxy, classes)

        img = ColorJittering(img)
        
        if len(bboxes_xyxy) != len(classes):
            print("bbox랑 class 수랑 일치하지 않다. augmentation 과정에서 실수가 있는 게 분명해")

        drawBBox(img, bboxes_xyxy)
        cv2.imshow("img", img)
        ch = cv2.waitKey(0)

        if ch == 27:
            break
