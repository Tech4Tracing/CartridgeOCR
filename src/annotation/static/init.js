function init_app(img_id) {
    var canvas_id = 'canvas';
    var panel_id = 'annotations';
    var save_id = 'btn_save';
    var save_advance_id = 'btn_save_advance';
    hl = radialDraw(img_id, canvas_id);
    ann = annotations(img_id, panel_id, hl);
    var next_url = '/annotate/'+(img_id+1);
    
    document.getElementById(save_id).onclick = (e) =>{ ann.save() };
    document.getElementById(save_advance_id).onclick = (e) => {
	ann.save();
	window.location.href = next_url;
    };
}
