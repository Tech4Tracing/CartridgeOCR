function init_app(img_id) {
    var canvas_id = 'canvas';
    var panel_id = 'annotations';
    var save_id = 'btn_save';
    var save_advance_id = 'btn_save_advance';
    var btn_radial_id = 'btn_radial';
    var btn_box_id = 'btn_box';
    var chk_nav_annot = 'chk_nav_annot';

    hl = radialDraw(img_id, canvas_id, 'radial');
    ann = annotations(img_id, panel_id, hl);
    // TODO: fix this notion of prev/next
    var next_url = '/annotate/'+img_id+'/next';
    
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
    document.getElementById(chk_nav_annot).checked = get_cookie('show_annot')==='true';
    document.getElementById(chk_nav_annot).onchange = (e) => { set_cookie('show_annot', document.getElementById(chk_nav_annot).checked, 30);}

    function next_image(id) {
        //var chk = document.getElementById(chk_nav_annot).checked;
        console.log('cookie: '+get_cookie('show_annot'));
        var url = '/annotate/'+id+'/next'; //+'?show_annot='+chk;
        window.location.href = url;
    }

    function prev_image(id) {
        // var chk = document.getElementById(chk_nav_annot).checked;
        console.log('cookie: '+get_cookie('show_annot'));
        var url = '/annotate/'+id+'/prev'; //+'?show_annot='+chk;
        window.location.href = url;
    }

    function set_cookie(cName, cValue, expDays) {
        let date = new Date();
        date.setTime(date.getTime() + (expDays * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = cName + "=" + cValue + "; " + expires + "; path=/";
    }

    function get_cookie(cName) {
        const name = cName + "=";
        const cDecoded = decodeURIComponent(document.cookie); //to be careful
        const cArr = cDecoded .split('; ');
        let res;
        cArr.forEach(val => {
            if (val.indexOf(name) === 0) res = val.substring(name.length);
        })
        return res;
    }
    console.log('cookie: '+get_cookie('show_annot'));
    return {
        prev_image: prev_image,
        next_image: next_image,
        set_cookie: set_cookie,
        get_cookie: get_cookie    
    }
}
