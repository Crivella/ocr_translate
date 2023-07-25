"""Tests for ocr module."""

from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import ocr


def test_pipeline(image_pillow, mock_ocr_preprocessor, mock_ocr_tokenizer, mock_ocr_model, monkeypatch):
    """Test ocr pipeline."""

    model_id = 'test_model'
    lang = 'ja'

    monkeypatch.setattr(ocr, 'OCR_IMAGE_PROCESSOR', mock_ocr_preprocessor(model_id))
    monkeypatch.setattr(ocr, 'OCR_TOKENIZER', mock_ocr_tokenizer(model_id))
    monkeypatch.setattr(ocr, 'OCR_MODEL', mock_ocr_model(model_id))

    res = ocr._ocr(image_pillow, lang) # pylint: disable=protected-access

    assert res == 'abcde'

def test_pipeline_worker():
    """Test tsl pipeline with worker"""
    placeholder = 'placeholder'
    ocr.q.stop_workers()

    messages = [ocr.ocr(placeholder, 'ja', 'en', id_=i, block=False) for i in range(3)]
    assert all(isinstance(_, Message) for _ in messages)
    def gen():
        while not ocr.q.msg_queue.empty():
            yield ocr.q.msg_queue.get()
    res = list(gen())
    assert len(res) == len(messages)
