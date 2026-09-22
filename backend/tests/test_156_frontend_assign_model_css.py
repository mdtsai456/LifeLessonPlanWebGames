"""測試 156：配置頁的模型預覽是正方形，且不接收指標。素材庫縮圖高度維持 180px。"""


def test_assign_model_viewer_is_square(client):
    css = client.get("/css/styles.css").text
    rule = css.split(".drag-card model-viewer,", 1)[1].split("}", 1)[0]
    assert ".slot-tile model-viewer" in rule
    assert "width: 100%" in rule
    assert "aspect-ratio: 1" in rule
    assert "height: auto" in rule
    assert "pointer-events: none" in rule
    thumb = css.split(".model-thumb,", 1)[1].split("}", 1)[0]
    assert "height: 180px" in thumb
