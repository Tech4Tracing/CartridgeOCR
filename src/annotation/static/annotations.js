function annotations(img_id, panel_id, highlights) {
    var annotations = [];
    function init() {
        // TODO: fetch annotations
        highlights.on_newpolygon(add);

        var url = "/annotations/"+img_id;
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);

        //Send the proper header information along with the request
        //xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        
        xhr.onreadystatechange = function() {//Call a function when the state changes.
            if(xhr.readyState == 4 && xhr.status == 200) {
                console.log(xhr.responseText);
                result = JSON.parse(xhr.responseText);     
                result.forEach((a) => {
                    //a.geometry = JSON.parse(a.geometry);
                    //a.metadata = JSON.parse(a.metadata);
                    a.temp_id = annotations.length;
                    a.committed = true;
                    annotations.push(a);
                    highlights.add_polygon(a.geometry);
                });
                refresh();   
            }
        }
        xhr.send();

    }
    
    function add(polygon) {
        console.log('adding a new polygon');
        annotations.push({
            temp_id: annotations.length,
            geometry: polygon,
            metadata:{},
            annotation: '',
            committed: false,
            db_id: null
        });
        refresh();
    }
    
    function geom_to_str(g) {
        s = '';
        g.forEach((p)=> s+='('+p.x+','+p.y+') ');
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
            }
        });
    }

    function delete_annotation(annotation_id) {
        console.log('deleting '+annotation_id);
        annotations.forEach((a) => {
            if (a.temp_id === annotation_id) {
                console.log('found annotation '+annotation_id);
                if (a.committed) {                    
                    var db_id = a.anno_id;
                    console.log('db_id: '+db_id);
                    var url = "/delete_annotation/"+db_id;
                    var xhr = new XMLHttpRequest();
                    xhr.open("DELETE", url, true);

                    //Send the proper header information along with the request
                    //xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
                    
                    xhr.onreadystatechange = function() {//Call a function when the state changes.
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
        highlights.set_polygons(annotations.map((a)=>a.geometry));
        refresh();
    }

    function makeAnnotationDiv(a) {
        console.log('creating annotation '+a);
        var e = document.createElement('div');
        e.className = 'annotation';
        e.id = 'a_' + a.temp_id;        
                
        var input = document.createElement('input');
        input.id = 'i_' + a.temp_id;
        input.onkeyup = (x) => {input_keypress(a.temp_id)}; 
        input.value = (a.annotation===null)?'':a.annotation;       
        var input_div = document.createElement('div');
        input_div.appendChild(makeElement('Text: '));
        input_div.appendChild(input);
    
        e.replaceChildren(...[
            makeElement("<a class='delete_handle' id='d_"+a.temp_id+"'>X</a>"),
            input_div,
            makeElement('<p>Type: radial</p>'),
            makeElement('<p>Points: ' + geom_to_str(a.geometry)+'</p>')
        ]);
        var d = e.querySelector('#d_'+a.temp_id);
        console.log(e.firstChild);
        console.log(e.id);
        d.onclick = () => {delete_annotation(a.temp_id)};
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
        // TODO: push
        annotations.forEach((a)=>{
            if (a.committed) return;
            // update the annotation text
            var text_id = 'i_'+a.temp_id;
            var annotation = document.getElementById(text_id).value;
            console.log('setting '+a.temp_id+' value to '+annotation);
            a.annotation = annotation;

            var url = "/post_annotation";

            var payload = JSON.stringify({
                geometry: a.geometry,
                img_id: img_id,
                annotation: a.annotation,
                metadata: a.metadata
            });
            var xhr = new XMLHttpRequest();
            xhr.open("POST", url, true);

            //Send the proper header information along with the request
            xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
           
            xhr.onreadystatechange = function() {//Call a function when the state changes.
                if(xhr.readyState == 4 && xhr.status == 200) {
                    console.log(xhr.responseText);
                    result = JSON.parse(xhr.responseText);
                    if (result.id) {
                        a.anno_id = result.id;
                    }
                    a.committed = true;
                }
            }
            xhr.send(payload);
        });
    }

    /*function updated(callback) {

    }*/

    init();
    return {
        'add': add,
        'save': save,
        'refresh': refresh,
        //'updated': updated,
    }
}