(function($, d3) {
    var svg = d3.select('header > svg').attr('height', 100),
        HEIGHT = 100,
        WIDTH = 300,
        NOW = Date.now(),
        data = d3.range(50).map(function(d) { return [NOW - (50-d) * 200, 0]; }),
        DOC_HEIGHT = $(document).height(),
        path = svg.append('path');

    function render(data) {
        var XMIN = d3.min(data.map(function(d) { return d[0]; })),
            XMAX = d3.max(data.map(function(d) { return d[0]; })),
            x = d3.scale.linear()
                .domain([XMIN, XMAX])
                .range([50, WIDTH]),
            y = d3.scale.linear()
                    .domain([0, DOC_HEIGHT])
                    .range([0, HEIGHT]),
            yAxis = d3.svg.axis()
                    .scale(y)
                    .ticks(5)
                    .tickSize(WIDTH)
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
            .attr('transform', 'translate(' + (WIDTH + 50) + ', 0)')
            .call(yAxis);

        if (data[data.length - 1][1] < DOC_HEIGHT / 2) {
            $('header').removeClass('has-error');
        } else {
            $('header').addClass('has-error');
        }
    }

    var inter = setInterval(function() {
        var timestamp = Date.now(),
            top = window.scrollY;
        data.push([timestamp, top]);
        data.shift();

        render(data);
    }, 200);

})(window.jQuery, window.d3);