function annotations(image_id, panel_id, highlights) {
    var annotations = [];
    function init() {
        // TODO: fetch annotations
        highlights.on_newpolygon(add);

        var url = "/api/v0/images/"+image_id+"/annotations";
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        
        xhr.onreadystatechange = function() {
            if(xhr.readyState == 4 && xhr.status == 200) {
                console.log(xhr.responseText);
                result = JSON.parse(xhr.responseText);
                if (result.total!==0) {     
                    result.annotations.forEach((a) => {
                        // TODO: fix this in the API.
                        if (a.metadata_=== null) {
                            a.metadata_ = "{}";
                        }
                        if (a.geometry === null) {
                            a.geometry = "[]";
                        }
                        a.geometry = JSON.parse(a.geometry);
                        a.metadata_ = JSON.parse(a.metadata_);
                        a.temp_id = annotations.length;
                        a.committed = true;
                        annotations.push(a);
                        var mode = a.metadata_.mode || 'radial';
                        highlights.add_polygon(a.geometry, mode);
                    });
                }
                refresh();   
            }
        }
        xhr.send();

    }
    
    // highlights.js sends polygons in format {'mode': mode, 'points': [points]}
    function add(polygon) {
        console.log('adding a new polygon');
        annotations.push({
            temp_id: annotations.length,
            geometry: polygon.points,
            metadata_:{mode: polygon.mode},
            annotation: '',
            committed: false,
            db_id: null
        });
        refresh();
    }
    
    function geom_to_str(g) {
        s = '';
        g.forEach((p)=> s+='('+Math.round(p.x*1000)/1000+','+Math.round(p.y*1000)/1000+') ');
        return s;
    }

    function makeElement(s) {
        var d = document.createElement('div');
        d.innerHTML = s;
        return d.firstChild;
    }

    function input_keypress(annotation_id) {
        var value = document.getElementById('i_'+annotation_id).value;
        console.log('keyup value: '+value);
        annotations.forEach((a) => {
            if (a.temp_id===annotation_id) {
                a.annotation = value;
                a.committed = false;
            }
        });
    }

    function delete_annotation(annotation_id) {
        console.log('deleting '+annotation_id);
        annotations.forEach((a) => {
            if (a.temp_id === annotation_id) {
                console.log('found annotation '+annotation_id);
                if (a.committed) {                    
                    var db_id = a.id;
                    // TODO: assert db_id is present and well-formed
                    console.log('db_id: '+db_id);
                    var url = "/api/v0/annotations/"+db_id;
                    var xhr = new XMLHttpRequest();
                    xhr.open("DELETE", url, true);
                   
                    xhr.onreadystatechange = function() {
                        if(xhr.readyState == 4 && xhr.status == 200) {
                            console.log('deleted '+annotation_id);
                            console.log(xhr.responseText);                
                        } else {
                            //console.log(xhr.readyState+' '+xhr.status);
                        }
                    }
                    xhr.send();
                }
            }
        });
        function without(a){console.log(a.temp_id+' '+annotation_id); return a.temp_id!==annotation_id;}
        annotations = annotations.filter(without, annotation_id);
        console.log('annotations: '+annotations.length);
        // TODO: callback to refresh the canvas.
        highlights.set_polygons(annotations.map((a)=> {return {'points': a.geometry, 'mode': a.metadata_.mode || 'radial'}}));
        refresh();
    }

    // TODO: this is complex enough it needs its own class.
    function makeAnnotationDiv(a) {
        var uncommitted_color = '#FFDAB9';
        console.log('creating annotation '+a);
        var e = document.createElement('div');
        e.className = 'annotation';
        if (!a.committed) {
            e.style['background-color'] = uncommitted_color;
        }
        e.id = 'a_' + a.temp_id;        
                
        var input = document.createElement('input');
        input.id = 'i_' + a.temp_id;
        input.onkeyup = (x) => {
            input_keypress(a.temp_id); 
            // Forcing a refresh would lose focus so we make the style change here.           
            e.style['background-color'] = uncommitted_color;
        }; 
        input.value = (a.annotation===null)?'':a.annotation;       
        var input_div = document.createElement('div');
        input_div.appendChild(makeElement('Text: '));
        input_div.appendChild(input);
        var mode = a.metadata_.mode || 'radial';
        e.replaceChildren(...[
            makeElement("<a class='delete_handle' id='d_"+a.temp_id+"'>X</a>"),
            input_div,
            makeElement('<p>Type: '+ mode +'</p>'),
            makeElement('<div><div>Text Up Direction:</div> \
            <div> <input type="radio" id="rd_dir_outward_'+a.temp_id+'" name="rd_direction_'+a.temp_id+'" value="outward" > \
            <label for="rd_dir_outward">outward</label> \
            <input type="radio" id="rd_dir_inward_'+a.temp_id+'" name="rd_direction_'+a.temp_id+'", value="inward" > \
            <label for="rd_dir_inward">inward</label> \
            <input type="radio" id="rd_dir_clockwise_'+a.temp_id+'" name="rd_direction_'+a.temp_id+'", value="clockwise" > \
            <label for="rd_dir_clockwise">clockwise</label> \
            <input type="radio" id="rd_dir_anticlockwise_'+a.temp_id+'" name="rd_direction_'+a.temp_id+'", value="anticlockwise" > \
            <label for="rd_dir_anticlockwise">anticlockwise</label> </div></div>'),                 
            makeElement('<div style="padding-top:10px;"><input type="checkbox" id="ck_illegible_'+a.temp_id+'" name="meta_'+a.temp_id+'"> \
            <label for="ck_illegible_'+a.temp_id+'">illegible</label> \
            <input type="checkbox" id="ck_symbol_'+a.temp_id+'" name="meta_'+a.temp_id+'"> \
            <label for="ck_symbol_'+a.temp_id+'">symbol</label> \
            '),
            makeElement('<p>Points: ' + geom_to_str(a.geometry)+'</p>')
        ]);
        var d = e.querySelector('#d_'+a.temp_id);
        
        d.onclick = () => {delete_annotation(a.temp_id)};
        if (a.metadata_ && a.metadata_.direction) {
            var dir = a.metadata_.direction;
            var d_elt = e.querySelector('#rd_dir_'+dir+'_'+a.temp_id);
            d_elt.checked = true;
        } else {
            var d_elt = e.querySelector('#rd_dir_outward_'+a.temp_id);
            d_elt.checked = true;
        }

        var radios = e.querySelectorAll('input[type=radio][name="rd_direction_'+a.temp_id+'"]');
        console.log('radios: '+radios.length);
        radios.forEach(radio => radio.addEventListener('change', () => {
            console.log('reset'); 
            a.committed=false;
            e.style['background-color'] = uncommitted_color;
        }));
        
        var checkboxes = e.querySelectorAll('input[type=checkbox][name="meta_'+a.temp_id+'"]');
        checkboxes.forEach(check => check.addEventListener('change', () => {
            console.log('reset'); 
            a.committed=false;
            e.style['background-color'] = uncommitted_color;            
        }));
        
        if (a.metadata_ && a.metadata_.illegible) {
            var d_elt = e.querySelector('#ck_illegible_'+a.temp_id);
            d_elt.checked = true;
        }
        if (a.metadata_ && a.metadata_.symbol) {
            var d_elt = e.querySelector('#ck_symbol_'+a.temp_id);
            d_elt.checked = true;
        }

        //e.innerHTML = '<p>Text: <input id="i_'+a.temp_id+'"></p><p>Type: radial</p><p>Points: '+geom_to_str(a.geometry)+'</p>';        
        return e;
    }

    function refresh() {
        var e = document.getElementById(panel_id);
        while (e.firstChild) {
            e.removeChild(e.lastChild);
        }
        console.log('Updating annotations');
        annotations.forEach(function (a) {
            e.appendChild(makeAnnotationDiv(a));            
        });
    }

    function save() {
        annotations.forEach((a)=>{
            if (a.committed) return;

            // replace the annotation. TODO: maybe there is a race condition? we want to update
            var url = "/api/v0/annotations/";
            var method = 'POST'
            if (a.id) {
                var db_id = a.id;
                console.log('db_id: '+db_id);
                method = 'PUT'
                url = "/api/v0/annotations/"+db_id;
            }

            // update the annotation text
            var text_id = 'i_'+a.temp_id;
            var annotation = document.getElementById(text_id).value;
            console.log('setting '+a.temp_id+' value to '+annotation);
            a.annotation = annotation;
            // need to preserve the mode but we should reconstruct the rest of the metadata.
            a.metadata_ = {'mode':a.metadata_.mode};

            var dir_id = 'rd_direction_'+a.temp_id;
            var direction = document.querySelector('input[name="'+dir_id+'"]:checked').value;
            console.log('Direction: '+direction);
            // TODO: where is the best place to put this assignment.
            a.metadata_.direction = direction;
            
            var meta_id = 'meta_'+a.temp_id;
            var checked = document.querySelectorAll('input[name="'+meta_id+'"]:checked');
            checked.forEach((c) => {
                console.log('found metadata '+c.id);
                var value = c.id.split('_')[1]; // the id contains the metadata.
                a.metadata_[value]=true;
            }
            );

            var payload = JSON.stringify({
                geometry: a.geometry,
                image_id: image_id,
                annotation: a.annotation,
                metadata_: a.metadata_
            });
            var xhr = new XMLHttpRequest();

	    // making this async causes bug #20
            xhr.open(method, url, false); 

            xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhr.onreadystatechange = function() {
                if(xhr.readyState == 4 && xhr.status == 200) {
                    console.log(xhr.responseText);
                    result = JSON.parse(xhr.responseText);
                    if (result.id) {
                        a.id = result.id;
                    }
                    a.committed = true;
                    // reset the parent element styling.
                    var e = document.getElementById('a_'+a.temp_id);
                    e.style['background-color'] = '#FFFFFF';
                }
            }
            xhr.send(payload);
        });
    }

    init();
    return {
        'add': add,
        'save': save,
        'refresh': refresh,
        //'updated': updated,
    }
}
