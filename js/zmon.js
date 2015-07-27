(function($, d3) {
    var svg = d3.select('header > svg').attr('height', 100),
        header = d3.select('body > header'),
        HEIGHT = 100,
        SVG_MAX_WIDTH = 375,
        MAX_SIZE = 50,
        NOW = Date.now(),
        WIDTH = SVG_MAX_WIDTH,
        data = d3.range(MAX_SIZE)
                 .map(function(d) { return [NOW - (MAX_SIZE-d) * 200, 0]; }),
        DOC_HEIGHT = $(document).height(),
        path = svg.append('path');

    function showAlert(prio) {
        $('[data-alert]').hide();
        $('[data-alert="alert-' + prio + '"]').show();
    }

    function render(data) {
        var XMIN = d3.min(data.map(function(d) { return d[0]; })),
            XMAX = d3.max(data.map(function(d) { return d[0]; })),
            x = d3.scale.linear()
                .domain([XMIN, XMAX])
                .range([50, WIDTH]),
            y = d3.scale.linear()
                    .domain([10, DOC_HEIGHT])
                    .range([HEIGHT - 10, 10]),
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

        var currentScroll = data[data.length - 1][1];

        if (currentScroll < (1 / 3) * DOC_HEIGHT) {
            header.attr('class', 'prio-3');
            showAlert(3);
        } else if (currentScroll > (2 / 3) * DOC_HEIGHT) {
            header.attr('class', 'prio-1');
            showAlert(1);
        } else {
            header.attr('class', 'prio-2');
            showAlert(2);
        }
    }

    var inter = setInterval(function() {
        var timestamp = Date.now(),
            top = window.scrollY;
        data.push([timestamp, top]);
        data.shift();

        render(data);
    }, 200);

    $(window).resize(function() {
        WIDTH = Math.min($('svg').width(), 450);
    });

})(window.jQuery, window.d3);