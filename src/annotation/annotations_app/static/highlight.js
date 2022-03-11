//initDraw(document.getElementById('imagearea'));
console.log('loading highlight');

function radialDraw(img_id, canvas_id, mode) {
    console.log('init radial draw');
    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    var points = [];
    var polygons = [];
    var mode = 'radial';

    var imgarea = document.getElementById(canvas_id);
    
    // TODO: only if points is non-empty.
    document.onkeydown = function(evt) {
        evt = evt || window.event;
        if (evt.key === 'Escape') {
            console.log('Esc key pressed.');
            points = []; 
            redraw();           
        }
    };

    function drawPolygon(points, polymode) {
        if (polymode==='radial') {
            drawRadialPolygon(points);
        } else {
            drawBox(points);
        }
    }

    function refresh_polygons(ctx) {
        //console.log(polygons);
        if (polygons.length>0) {
            polygons.forEach(function (p) {
                ctx.fillStyle = 'blue';
                console.log('drawing '+p);
                drawPolygon(p.points, p.mode);                
            });
        }
        ctx.fillStyle = "red";
    }

    var background = null;
    function redraw() {
        var canvas = document.getElementById(canvas_id);
        // use getContext to use the canvas for drawing
        var ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        canvas.width = 640;
        
        if (background===null) {
            background = new Image();
            // Make sure the image is loaded first otherwise nothing will draw.
            background.onload = function(){
                canvas.height = canvas.width/background.width * background.height;
                console.log('canvas w,h:'+canvas.width+' '+canvas.height+' '+background.width+' '+background.height);
                ctx.drawImage(background,0,0, canvas.width, canvas.height);   
                refresh_polygons(ctx);
            }
            background.src = "/images/"+img_id;
            
        } else {
            ctx.drawImage(background,0,0, canvas.width, canvas.height);  
            refresh_polygons(ctx);
        }
        
    }
    



    function setMousePosition(e) {
        // your mouse calculations
    
        const boundaries = e.currentTarget.getBoundingClientRect();
    
        mouse.x = e.x-boundaries.left;
        mouse.y = e.y-boundaries.top;
    }

    // registers a new callback when a polygon is added
    var add_callbacks = [];
    function on_newpolygon(f) {
        add_callbacks.push(f);
    }
    function process_add_callbacks(p) {
        console.log('processing callbacks');
        add_callbacks.forEach((f) => {f(p)});
    }

    var clickhandler = function(e, clicktype) {
        setMousePosition(e);
        if (points.length>0) {
            points.pop();
        }
        var cx = mouse.x/canvas.width;
        var cy = mouse.y/canvas.height;
        points.push({x: cx, y: cy});
        points.push({x: cx, y: cy});
        console.log(cx+','+cy);
        var threshold = mode === 'radial' ? 3 : 2;
        //if (clicktype === 'double') {
        if (points.length>threshold) {
            points.pop();
            polygons.push({'mode': mode, 'points': points});
            points = [];
            redraw();
            process_add_callbacks(polygons[polygons.length-1]);
        } else {
            redraw();
            console.log('clickhandler: ' + points);       
            drawPolygon(points, mode);
        } 
    }
    imgarea.onmouseup = function(e) { return clickhandler(e,'single');}
    imgarea.ondblclick = function(e) { return clickhandler(e,'double');}

    imgarea.onmousemove = function (e) {        
        setMousePosition(e);
        var cx = mouse.x/canvas.width;
        var cy = mouse.y/canvas.height;
        if (points.length>0) {
            points.pop();
            points.push({x: cx, y: cy});
            redraw();
            drawPolygon(points, mode);
        }
        //console.log(points);
        //console.log(e.x+' '+e.y);
        /*if (element !== null) {
            element.style.width = Math.abs(mouse.x - mouse.startX) + 'px';
            element.style.height = Math.abs(mouse.y - mouse.startY) + 'px';
            element.style.left = (mouse.x - mouse.startX < 0) ? mouse.x + 'px' : mouse.startX + 'px';
            element.style.top = (mouse.y - mouse.startY < 0) ? mouse.y + 'px' : mouse.startY + 'px';
        }*/
    }

    function drawBox(points) {
        // get the canvas element using the DOM
        var canvas = document.getElementById(canvas_id);
        
        // Make sure we don't execute when canvas isn't supported
        if (canvas.getContext) {

            // use getContext to use the canvas for drawing
            var ctx = canvas.getContext('2d');

            var cpoints = points.map((p) => { return {x: p.x*canvas.width, y: p.y*canvas.height}});
            
            ctx.globalAlpha = 0.25;

            if (cpoints.length!==2) {
                console.log('weird cpoints. exiting');
                return;
            }
            ctx.beginPath();
            ctx.rect(cpoints[0].x, cpoints[0].y, cpoints[1].x-cpoints[0].x, cpoints[1].y-cpoints[0].y);
            ctx.fill();
            ctx.globalAlpha = 1.0;
            ctx.lineWidth = 1;
            ctx.stroke();            
        }
    }
    
    function drawRadialPolygon(points) {
        // get the canvas element using the DOM
        var canvas = document.getElementById(canvas_id);
        
        // Make sure we don't execute when canvas isn't supported
        if (canvas.getContext) {

            // use getContext to use the canvas for drawing
            var ctx = canvas.getContext('2d');

            var srtPoints = [];           
            var r1, r2, dx1, dx2, dx3, dy1, dy2, theta1, theta2, dtheta, clockwise;
            var cpoints = points.map((p) => { return {x: p.x*canvas.width, y: p.y*canvas.height}});
            if (cpoints.length<3) {
                cpoints.forEach(function (p) {
                    srtPoints.push(p);
                });
            } else {
                srtPoints.push(cpoints[0]);
                srtPoints.push(cpoints[1]);
                srtPoints.push(cpoints[2]);
                dx1 = cpoints[1].x-cpoints[0].x;
                dy1 = cpoints[1].y-cpoints[0].y;
                r1 = Math.sqrt(dx1*dx1+dy1*dy1);
                // theta comes from points[2]-points[0] vs points[1]-points[0]
                dx2 = cpoints[2].x - cpoints[0].x;
                dy2 = cpoints[2].y - cpoints[0].y;
                r2 = Math.sqrt(dx2*dx2+dy2*dy2);
                srtPoints.push({x: cpoints[0].x + r2 * dx1/r1, y: cpoints[0].y + r2 * dy1/r1});
                theta1 = Math.atan2(dy1, dx1);            
                theta2 = Math.atan2(dy2, dx2);
                //console.log("arc "+r1+' '+dx1+' '+dy1+' '+dx2+' '+dy2+' '+dy1/dx1+' '+dy2/dx2);
                dtheta = theta2-theta1;
                while (dtheta<-Math.PI) dtheta+=2*Math.PI;
                while (dtheta>Math.PI) dtheta-=2*Math.PI;
                clockwise = dtheta<0;                
            }

            console.log('points length: '+cpoints.length);
            
            if (srtPoints.length==2) {
                ctx.globalAlpha = 1.0;
                ctx.lineWidth = 2;
            } else {
                ctx.globalAlpha = 0.1;
                ctx.lineWidth = 1;
            }
            ctx.beginPath();
            ctx.moveTo(srtPoints[0].x, srtPoints[0].y);
            ctx.lineTo(srtPoints[1].x, srtPoints[1].y);
            if (srtPoints.length>2) {                
                //console.log('arc '+r1+' '+theta1+' '+theta2);
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r1, theta1, theta2, clockwise);
            }                
            //ctx.lineTo(srtPoints[0].x, srtPoints[0].y);
            ctx.closePath();
            ctx.stroke();
            ctx.fill();

            ctx.globalAlpha = 0.25;

            if (srtPoints.length>=4) {
                ctx.beginPath();                
                ctx.moveTo(srtPoints[3].x, srtPoints[3].y);
                ctx.lineTo(srtPoints[1].x, srtPoints[1].y);                
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r1, theta1, theta2, clockwise);
                ctx.lineTo(srtPoints[2].x, srtPoints[2].y);                         
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r2, theta2, theta1, !clockwise);                
                //ctx.lineTo(p5.x, p5.y);
                ctx.stroke();
                ctx.fill();
            }
            ctx.globalAlpha = 1.0;
        }

    }

    function add_polygon(polygon, mode) {
        polygons.push({'mode': mode, 'points': polygon});
        redraw();
        // called by external services.
        //process_add_callbacks(polygons[polygons.length-1]);
    }

    function set_polygons(_polygons) {
        polygons = _polygons;
        redraw();
    }
    
    function set_mode(_mode) {
        if (_mode!=='radial' && _mode!=='box') {
            console.log('invalid mode')
        }
        mode = _mode;
    }

    redraw();

    return {
        on_newpolygon: on_newpolygon,
        add_polygon: add_polygon,
        set_polygons: set_polygons,
        set_mode: set_mode
    }
}


