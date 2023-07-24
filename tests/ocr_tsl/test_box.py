"""Tests for box module."""

from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import box

boxes = [
    ((10,10,30,30), (15,15,20,20)), # b2 inside b1
    ((15,15,20,20), (10,10,30,30)), # b1 inside b2

    ((30,30,50,50), (10,10,20,35)), # l1 > r2
    ((30,30,50,50), (55,10,75,35)), # r1 < l2
    ((30,30,50,50), (10,10,35,20)), # b1 > t2
    ((30,30,50,50), (10,55,35,75)), # t1 < b2

    ((30,30,50,50), (10,10,35,35)), # b2-tr inside b1
    ((30,30,50,50), (45,10,75,35)), # b2-tl inside b1
    ((30,30,50,50), (40,45,75,75)), # b2-bl inside b1
    ((30,30,50,50), (10,45,35,75)), # b2-br inside b1

    ((10,50,70,60), (50,10,60,70)), # intersection, but cornder not inside

    ((10,10,30,30), (29,29,51,40), (50,10,60,30)), # 3x intersection
    ((10,10,30,30), (29,29,51,40), (60,10,70,30)), # 2x intersection + 1
]
ids = [
        'b2_inside_b1',
        'b1_inside_b2',
        'l1_>_r2',
        'r1_<_l2',
        'b1_>_t2',
        't1_<_b2',
        'b2-tr_inside_b1',
        'b2-tl_inside_b1',
        'b2-bl_inside_b1',
        'b2-br_inside_b1',
        'int_nocorners',
        '3x_intersection',
        '2x_intersection_+_1',
]

def test_intersection_merge(data_regression):
    """Test intersections function."""

    res = []
    for boxes_lbrt,idx in zip(boxes,ids):
        ptr = {}
        ptr['idx'] = idx
        boxes_lrbt = []
        for l,b,r,t in boxes_lbrt:
            boxes_lrbt.append((l,r,b,t))
        ptr['box_lst'] = boxes_lrbt
        ptr['intersection'] = box.intersections(boxes_lrbt)
        merge = box.merge_bboxes(boxes_lrbt)
        merge = [[int(_) for _ in el] for el in merge]
        ptr['merge'] = merge
        res.append(ptr)

    data_regression.check({'res': res})

def test_box_pipeline_easyocr(image_pillow, monkeypatch, mock_box_reader):
    """Test box pipeline."""
    model_id = 'easyocr'

    monkeypatch.setattr(box, 'BOX_MODEL_ID', model_id)
    monkeypatch.setattr(box, 'READER', mock_box_reader(model_id))

    res = box._box_pipeline(image_pillow) # pylint: disable=protected-access

    assert res == [[10,30,10,30], [40,50,40,50]]

def test_box_pipeline_worker():
    """Test tsl pipeline with worker"""
    placeholder = 'placeholder'
    box.q.stop_workers()

    messages = [box.box_pipeline(placeholder, id_=i, block=False) for i in range(3)]
    assert all(isinstance(_, Message) for _ in messages)
    def gen():
        while not box.q.msg_queue.empty():
            yield box.q.msg_queue.get()
    res = list(gen())
    assert len(res) == len(messages)
