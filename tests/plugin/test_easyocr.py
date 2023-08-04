###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""Tests for easyocr plugin."""

from ocr_translate.plugins import easyocr

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
        ptr['intersection'] = easyocr.EasyOCRBoxModel.intersections(boxes_lrbt)
        merge = easyocr.EasyOCRBoxModel.merge_bboxes(boxes_lrbt)
        merge = [[int(_) for _ in el] for el in merge]
        ptr['merge'] = merge
        res.append(ptr)

    data_regression.check({'res': res})

# @pytest.mark.django_db
# def test_load_box_model_easyocr(monkeypatch):
#     """Test load box model. Success"""
#     model_id = 'easyocr'
#     monkeypatch.setattr(box.easyocr, 'Reader', lambda *args, **kwargs: 'mocked')

#     # Needed to make sure that changes doen by `load_box_model` are not persisted
#     monkeypatch.setattr(box, 'BOX_MODEL_ID', None)
#     monkeypatch.setattr(box, 'READER', None)
#     monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', None)

#     assert m.OCRBoxModel.objects.count() == 0
#     box.load_box_model(model_id)
#     assert m.OCRBoxModel.objects.count() == 1

#     assert box.BOX_MODEL_ID == model_id
#     assert box.READER == 'mocked' # Check that the mocked function was called and READER was set by loader

# def test_unload_box_model(monkeypatch):
#     """Test unload box model."""
#     model_id = 'easyocr'
#     monkeypatch.setattr(box, 'BOX_MODEL_ID', model_id)
#     monkeypatch.setattr(box, 'READER', 'mocked')
#     monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', 'test')

#     box.unload_box_model()

#     assert box.BBOX_MODEL_OBJ is None
#     assert box.BOX_MODEL_ID is None
#     assert box.READER is None


# def test_unload_box_model_cpu(monkeypatch, mock_called):
#     """Test unload box model with cpu."""
#     monkeypatch.setattr(box.torch.cuda, 'empty_cache', mock_called)
#     monkeypatch.setattr(box, 'dev', 'cpu')

#     box.unload_box_model()
#     assert not hasattr(mock_called, 'called')

# def test_unload_box_model_cuda(monkeypatch, mock_called):
#     """Test unload box model with cuda."""
#     monkeypatch.setattr(box.torch.cuda, 'empty_cache', mock_called)
#     monkeypatch.setattr(box, 'dev', 'cuda')

#     box.unload_box_model()
#     assert hasattr(mock_called, 'called')

# def test_box_pipeline_notimplemented(monkeypatch):
#     """Test box pipeline. With not implemented model."""
#     model_id = 'notimplemented'
#     monkeypatch.setattr(box, 'BOX_MODEL_ID', model_id)

#     with pytest.raises(NotImplementedError):
#         box._box_pipeline(None) # pylint: disable=protected-access

# def test_box_pipeline_easyocr(image_pillow, monkeypatch, mock_box_reader):
#     """Test box pipeline."""
#     model_id = 'easyocr'

#     monkeypatch.setattr(box, 'BOX_MODEL_ID', model_id)
#     monkeypatch.setattr(box, 'READER', mock_box_reader(model_id))

#     res = box._box_pipeline(image_pillow) # pylint: disable=protected-access

#     assert res == [[10,30,10,30], [40,50,40,50]]
