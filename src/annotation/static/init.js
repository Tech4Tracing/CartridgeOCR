function init_app(img_id) {
    var canvas_id = 'canvas';
    var panel_id = 'annotations';
    var save_id = 'btn_save';
    var save_advance_id = 'btn_save_advance';
    var btn_radial_id = 'btn_radial';
    var btn_box_id = 'btn_box'
    hl = radialDraw(img_id, canvas_id, 'radial');
    ann = annotations(img_id, panel_id, hl);
    var next_url = '/annotate/'+(img_id+1);
    
    document.getElementById(save_id).onclick = (e) =>{ ann.save() };
    document.getElementById(save_advance_id).onclick = (e) => {
	    ann.save();
	    window.location.href = next_url;
    };

    function toggle_mode(mode) {
        box = document.getElementById(btn_box_id);
        rad = document.getElementById(btn_radial_id);
        if (mode==='box') {
            box.disabled = true;
            box.className = 'btn_selected';
            rad.disabled = false;
            rad.className = 'btn_unselected';
            hl.set_mode('box');
        } else { // mode === 'radial'
            box.disabled = false;
            box.className = 'btn_unselected';
            rad.disabled = true;
            rad.className = 'btn_selected';
            hl.set_mode('radial');
        }
    }

    document.getElementById(btn_box_id).onclick = (e) => { toggle_mode('box'); }
    document.getElementById(btn_radial_id).onclick = (e) => { toggle_mode('radial'); }
    document.getElementById(btn_radial_id).disabled = true;
}
