/**
 * http://ejohn.org/blog/javascript-micro-templating/
 */
function John() {
    var cache = {};
 
    this.tmpl = function tmpl(str, data){
    // Figure out if we're getting a template, or if we need to
    // load the template - and be sure to cache the result.
    var fn = !/\W/.test(str) ?
        cache[str] = cache[str] ||
        tmpl(document.getElementById(str).innerHTML) :
     
        // Generate a reusable function that will serve as a template
        // generator (and which will be cached).
        new Function("obj",
            "var p=[],print=function(){p.push.apply(p,arguments);};" +
           
            // Introduce the data as local variables using with(){}
            "with(obj){p.push('" +
           
            // Convert the template into pure JavaScript
            str
                .replace(/[\r\t\n]/g, " ")
                .split("<%").join("\t")
                .replace(/((^|%>)[^\t]*)'/g, "$1\r")
                .replace(/\t=(.*?)%>/g, "',$1,'")
                .split("\t").join("');")
                .split("%>").join("p.push('")
                .split("\r").join("\\'")
            + "');}return p.join('');");
       
        // Provide some basic currying to the user
        return data ? fn( data ) : fn;
    };
}

(function(d3) {
    var svg = d3.select('.demo svg').attr('height', 100),
        container = d3.select('.demo'),
        TEMPLATE = new John(),
        HEIGHT = 100,
        SVG_MAX_WIDTH = 375,
        MAX_SIZE = 50,
        NOW = Date.now(),
        WIDTH = SVG_MAX_WIDTH,
        data = d3.range(MAX_SIZE)
                 .map(function(d) { return [NOW - (MAX_SIZE-d) * 200, 0]; }),
        DOC_HEIGHT = document.getElementsByTagName('body')[0].clientHeight,
        path = svg.append('path');

    function showAlert(scrollPos, prio) {
        d3.selectAll('[data-alert]').attr('style', 'display:none;');
        var activeAlert = d3.select('[data-alert="alert-' + prio + '"]');
        activeAlert.attr('style', 'display:block;');
        activeAlert.text(TEMPLATE.tmpl(activeAlert.attr('data-template'), { value: scrollPos }));
    }

    function render(data) {
        var XMIN = d3.min(data.map(function(d) { return d[0]; })),
            XMAX = d3.max(data.map(function(d) { return d[0]; })),
            x = d3.scale.linear()
                .domain([XMIN, XMAX])
                .range([50, WIDTH - 25]),
            y = d3.scale.linear()
                    .domain([10, DOC_HEIGHT])
                    .range([HEIGHT - 10, 10]),
            yAxis = d3.svg.axis()
                    .scale(y)
                    .ticks(5)
                    .tickSize(WIDTH - 75)
                    .tickFormat(function(d) { return d + ' px'; })
                    .orient('left'),
            line = d3.svg.line()
                    .x(function(d) { return x(d[0]); })
                    .y(function(d) { return y(d[1]); })
                    .interpolate('basis');

        svg.attr('width', WIDTH);
        path
            .datum(data)
            .attr('d', line);

        
        svg.select('.y-axis')
            .attr('transform', 'translate(' + (WIDTH - 25) + ', 0)')
            .call(yAxis);

        var currentScroll = data[data.length - 1][1];

        if (currentScroll < (1 / 3) * DOC_HEIGHT) {
            container.attr('class', 'demo grid prio-3');
            showAlert(currentScroll, 3);
        } else if (currentScroll > (2 / 3) * DOC_HEIGHT) {
            container.attr('class', 'demo grid prio-1');
            showAlert(currentScroll, 1);
        } else {
            container.attr('class', 'demo grid prio-2');
            showAlert(currentScroll, 2);
        }
    }

    setTimeout(function() {
        setInterval(function() {
            data.push([Date.now(), window.scrollY]);
            data.shift();

            render(data);
        }, 200);
        
    }, 0);

    window.onresize = function() {
        var svg = document.getElementsByTagName('svg')[0],
            svgStyle = window.getComputedStyle(svg);
        WIDTH = Math.min(parseInt(svgStyle.width, 10), 450);
        DOC_HEIGHT = document.getElementsByTagName('body')[0].clientHeight;
    };

})(window.d3);