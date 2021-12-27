
function init_app(img_id) {
    var canvas_id = 'canvas';
    var panel_id = 'annotations';
    var save_id = 'btn_save';
    hl = radialDraw(img_id, canvas_id);
    ann = annotations(img_id, panel_id, hl);
    document.getElementById(save_id).onclick = (e) =>{ ann.save() };
}