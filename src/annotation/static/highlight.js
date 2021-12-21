//initDraw(document.getElementById('imagearea'));
console.log('loading highlight');

function initDraw() {
    console.log('initdraw');
    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    imgarea = document.getElementById('imagearea');
    
    /*function setMousePosition(e) {
        var ev = e || window.event; //Moz || IE
        if (ev.pageX) { //Moz
            mouse.x = ev.pageX + window.pageXOffset;
            mouse.y = ev.pageY + window.pageYOffset;
        } else if (ev.clientX) { //IE
            mouse.x = ev.clientX + document.body.scrollLeft;
            mouse.y = ev.clientY + document.body.scrollTop;
        }
    };*/
   
    function setMousePosition(e) {
        // your mouse calculations
    
        const boundaries = e.currentTarget.getBoundingClientRect();
    
        mouse.x = e.x-boundaries.left;
        mouse.y = e.y-boundaries.top;
    }

    var element = null;
    imgarea.onmousemove = function (e) {        
        setMousePosition(e);
        //console.log(e.x+' '+e.y);
        if (element !== null) {
            element.style.width = Math.abs(mouse.x - mouse.startX) + 'px';
            element.style.height = Math.abs(mouse.y - mouse.startY) + 'px';
            element.style.left = (mouse.x - mouse.startX < 0) ? mouse.x + 'px' : mouse.startX + 'px';
            element.style.top = (mouse.y - mouse.startY < 0) ? mouse.y + 'px' : mouse.startY + 'px';
        }
    }

    imgarea.onmouseup = function (e) {
        if (element !== null) {
            element = null;
            imgarea.style.cursor = "default";
            console.log("finsihed.");
        } 
    }

    imgarea.onmousedown = function (e) {
          if(element===null){
            console.log("begun.");
            setMousePosition(e);
            mouse.startX = mouse.x;
            mouse.startY = mouse.y;
            element = document.createElement('div');
            element.className = 'rectangle'
            element.style.left = mouse.startX + 'px';
            element.style.top = mouse.startY + 'px';
            imgarea.appendChild(element);
            imgarea.style.cursor = "crosshair";
            e.preventDefault();
          }
    }
}

function radialDraw(img_id) {
    console.log('init radial draw');
    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    var points = [];
    var polygons = [];
    

    imgarea = document.getElementById('canvas');
    
    document.onkeydown = function(evt) {
        evt = evt || window.event;
        if (evt.key === 'Escape') {
            console.log('Esc key pressed.');
            points = []; 
            drawBackground();           
        }
    };


    function refresh_polygons(ctx) {
        
        console.log(polygons);
        if (polygons.length>0) {
        
            polygons.forEach(function (p) {
                ctx.fillStyle = 'blue';
                console.log('drawing'+p);
                drawRadialPolygon(p);
            });
        }
        ctx.fillStyle = "red";
    }

    var background = null;
    function drawBackground() {
        var canvas = document.getElementById('canvas');
        // use getContext to use the canvas for drawing
        var ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        canvas.width = 480;
        
        if (background===null) {
            background = new Image();
            // Make sure the image is loaded first otherwise nothing will draw.
            background.onload = function(){
                canvas.height = canvas.width/background.width * background.height;
                console.log('canvas w,h:'+canvas.width+' '+canvas.height+' '+background.width+' '+background.height);
                ctx.drawImage(background,0,0, canvas.width, canvas.height);   
                refresh_polygons(ctx);
            }
            background.src = "/img/"+img_id;
            
        } else {
            ctx.drawImage(background,0,0, canvas.width, canvas.height);  
            refresh_polygons(ctx);
        }
        
    }
    

    drawBackground();



    function setMousePosition(e) {
        // your mouse calculations
    
        const boundaries = e.currentTarget.getBoundingClientRect();
    
        mouse.x = e.x-boundaries.left;
        mouse.y = e.y-boundaries.top;
    }

    var clickhandler = function(e, clicktype) {
        setMousePosition(e);
        if (points.length>0) {
            points.pop();
        }
        points.push({x: mouse.x, y: mouse.y});
        points.push({x: mouse.x, y: mouse.y});
        console.log(mouse.x+','+mouse.y);
        if (clicktype === 'double') {
            polygons.push(points);
            points = [];
            drawBackground();
        } else {
            drawBackground();
            drawRadialPolygon(points);
        }
        console.log(points);
    }
    imgarea.onmouseup = function(e) { return clickhandler(e,'single');}
    imgarea.ondblclick = function(e) { return clickhandler(e,'double');}

    imgarea.onmousemove = function (e) {        
        setMousePosition(e);
        
        if (points.length>0) {
            points.pop();
            points.push({x: mouse.x, y: mouse.y});
            drawBackground();
            drawRadialPolygon(points);
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

    function drawRadialPolygonOld(points) {
        // get the canvas element using the DOM
        var canvas = document.getElementById('canvas');
        
        
        // Make sure we don't execute when canvas isn't supported
        if (canvas.getContext) {

            // use getContext to use the canvas for drawing
            var ctx = canvas.getContext('2d');

            var srtPoints = [];
            var p5 = srtPoints[0];
            var r1, r2, r3, dx1, dx2, dx3, dy1, dy2, dy3;
            if (points.length<3) {
                points.forEach(function (p) {
                    srtPoints.push(p);
                });
            } else {
                srtPoints.push(points[0]);
                srtPoints.push(points[1]);
                dx1 = points[1].x-points[0].x;
                dy1 = points[1].y-points[0].y;
                r1 = Math.sqrt(dx1*dx1+dy1*dy1);
                // theta comes from points[2]-points[0] vs points[1]-points[0]
                dx2 = points[2].x - points[0].x;
                dy2 = points[2].y - points[0].y;
                r2 = Math.sqrt(dx2*dx2+dy2*dy2);
                srtPoints.push({x: points[0].x + r1 * dx2/r2, y: points[0].y + r1 * dy2/r2});
                if (points.length>3) {
                    dx3 = points[3].x - points[0].x;
                    dy3 = points[3].y - points[0].y;
                    r3 = Math.sqrt(dx3*dx3+dy3*dy3);
                    srtPoints.push({x: points[0].x + r3 * dx2/r2, y: points[0].y + r3 * dy2/r2});
                    p5 = {x: points[0].x + r3 * dx1/r1, y: points[0].y + r3 * dy1/r1};
                }
            }


            ctx.globalAlpha = 0.25;
            ctx.beginPath();
            ctx.moveTo(srtPoints[0].x, srtPoints[0].y);
            ctx.lineTo(srtPoints[1].x, srtPoints[1].y);
            if (srtPoints.length>2) {
                var theta1 = Math.atan2(dy1, dx1);            
                var theta2 = Math.atan2(dy2, dx2);
                //console.log("arc "+r1+' '+dx1+' '+dy1+' '+dx2+' '+dy2+' '+dy1/dx1+' '+dy2/dx2);
                var dtheta = theta2-theta1;
                while (dtheta<-Math.PI) dtheta+=2*Math.PI;
                while (dtheta>Math.PI) dtheta-=2*Math.PI;
                clockwise = dtheta<0;
                console.log('arc '+r1+' '+theta1+' '+theta2);
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r1, theta1, theta2, clockwise);
            }    
            
            ctx.lineTo(srtPoints[0].x, srtPoints[0].y);

            ctx.stroke();
            ctx.fill();

            ctx.globalAlpha = 0.5;

            if (points.length>=4) {
                ctx.beginPath();
                
                ctx.moveTo(p5.x, p5.y);
                ctx.lineTo(srtPoints[1].x, srtPoints[1].y);
                var theta1 = Math.atan2(dy1, dx1);            
                var theta2 = Math.atan2(dy2, dx2);
                var dtheta = theta2-theta1;
                while (dtheta<-Math.PI) dtheta+=2*Math.PI;
                while (dtheta>Math.PI) dtheta-=2*Math.PI;
                clockwise = dtheta<0;
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r1, theta1, theta2, clockwise);
                ctx.lineTo(srtPoints[3].x, srtPoints[3].y);                         
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r3, theta2, theta1, !clockwise);                
                //ctx.lineTo(p5.x, p5.y);
                ctx.stroke();
                ctx.fill();
            }

        }

    }
    
    function drawRadialPolygon(points) {
        // get the canvas element using the DOM
        var canvas = document.getElementById('canvas');
        
        
        // Make sure we don't execute when canvas isn't supported
        if (canvas.getContext) {

            // use getContext to use the canvas for drawing
            var ctx = canvas.getContext('2d');

            var srtPoints = [];
            var p5 = srtPoints[0];
            var r1, r2, r3, dx1, dx2, dx3, dy1, dy2, dy3, theta1, theta2, dtheta, clockwise;
            if (points.length<3) {
                points.forEach(function (p) {
                    srtPoints.push(p);
                });
            } else {
                srtPoints.push(points[0]);
                srtPoints.push(points[1]);
                srtPoints.push(points[2]);
                dx1 = points[1].x-points[0].x;
                dy1 = points[1].y-points[0].y;
                r1 = Math.sqrt(dx1*dx1+dy1*dy1);
                // theta comes from points[2]-points[0] vs points[1]-points[0]
                dx2 = points[2].x - points[0].x;
                dy2 = points[2].y - points[0].y;
                r2 = Math.sqrt(dx2*dx2+dy2*dy2);
                srtPoints.push({x: points[0].x + r2 * dx1/r1, y: points[0].y + r2 * dy1/r1});
                theta1 = Math.atan2(dy1, dx1);            
                theta2 = Math.atan2(dy2, dx2);
                //console.log("arc "+r1+' '+dx1+' '+dy1+' '+dx2+' '+dy2+' '+dy1/dx1+' '+dy2/dx2);
                dtheta = theta2-theta1;
                while (dtheta<-Math.PI) dtheta+=2*Math.PI;
                while (dtheta>Math.PI) dtheta-=2*Math.PI;
                clockwise = dtheta<0;
                /*if (points.length>3) {
                    dx3 = points[3].x - points[0].x;
                    dy3 = points[3].y - points[0].y;
                    r3 = Math.sqrt(dx3*dx3+dy3*dy3);
                    srtPoints.push({x: points[0].x + r3 * dx2/r2, y: points[0].y + r3 * dy2/r2});
                    p5 = {x: points[0].x + r3 * dx1/r1, y: points[0].y + r3 * dy1/r1};
                }*/
            }


            ctx.globalAlpha = 0.25;
            ctx.beginPath();
            ctx.moveTo(srtPoints[0].x, srtPoints[0].y);
            ctx.lineTo(srtPoints[1].x, srtPoints[1].y);
            if (srtPoints.length>2) {                
                console.log('arc '+r1+' '+theta1+' '+theta2);
                ctx.arc(srtPoints[0].x, srtPoints[0].y, r1, theta1, theta2, clockwise);
            }                
            ctx.lineTo(srtPoints[0].x, srtPoints[0].y);
            ctx.stroke();
            ctx.fill();

            ctx.globalAlpha = 0.5;

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

    function drawPolygon(points) {
        // get the canvas element using the DOM
        var canvas = document.getElementById('canvas');
        
        
        // Make sure we don't execute when canvas isn't supported
        if (canvas.getContext) {

            // use getContext to use the canvas for drawing
            var ctx = canvas.getContext('2d');
            
            // calculate max and min x and y
            var minX = points[0].x;
            var maxX = points[0].x;
            var minY = points[0].y;
            var maxY = points[0].y;

            for (var i = 1; i < points.length; i++) {
                if (points[i].x < minX) minX = points[i].x;
                if (points[i].x > maxX) maxX = points[i].x;
                if (points[i].y < minY) minY = points[i].y;
                if (points[i].y > maxY) maxY = points[i].y;
            }


            // choose a "central" point
            var center = {
                x: minX + (maxX - minX) / 2,
                y: minY + (maxY - minY) / 2
            };

            // precalculate the angles of each point to avoid multiple calculations on sort
            for (var i = 0; i < points.length; i++) {
                points[i].angle = Math.acos((points[i].x - center.x) / lineDistance(center, points[i]));

                if (points[i].y > center.y) {
                    points[i].angle = Math.PI + Math.PI - points[i].angle;
                }
            }

            // sort by angle
            srtPoints = [...points];
            srtPoints = srtPoints.sort(function(a, b) {
                return a.angle - b.angle;
            });

            // Draw shape
            ctx.beginPath();
            ctx.moveTo(srtPoints[0].x, srtPoints[0].y);

            for (var i = 1; i < srtPoints.length; i++) {
                ctx.lineTo(srtPoints[i].x, srtPoints[i].y);
            }

            ctx.lineTo(srtPoints[0].x, srtPoints[0].y);

            ctx.stroke();
            ctx.fill();
        }
    }

    function lineDistance(point1, point2) {
        var xs = 0;
        var ys = 0;

        xs = point2.x - point1.x;
        xs = xs * xs;

        ys = point2.y - point1.y;
        ys = ys * ys;

        return Math.sqrt(xs + ys);
    }

    /*imgarea.onmouseup = function (e) {
        if (element !== null) {
            element = null;
            imgarea.style.cursor = "default";
            console.log("finsihed.");
        } 
    }*/

    /*imgarea.onmousedown = function (e) {
          if(element===null){
            console.log("begun.");
            setMousePosition(e);
            mouse.startX = mouse.x;
            mouse.startY = mouse.y;
            element = document.createElement('div');
            element.className = 'rectangle'
            element.style.left = mouse.startX + 'px';
            element.style.top = mouse.startY + 'px';
            imgarea.appendChild(element);
            imgarea.style.cursor = "crosshair";
            e.preventDefault();
          }
    }*/
}


