(function($, d3) {
    var svg = d3.select('header > svg').attr('height', 100),
        data = [],
        DOC_HEIGHT = $(document).height(),
        DOC_WIDTH = $(document).width(),
        path = svg.append('path');

    function render(data) {
        var XMIN = d3.min(data.map(function(d) { return d[0]; })),
            XMAX = d3.max(data.map(function(d) { return d[0]; })),
            x = d3.scale.linear()
                .domain([XMIN, XMAX])
                .range([0, DOC_WIDTH]),
            y = d3.scale.linear()
                    .domain([0, DOC_HEIGHT])
                    .range([0, 100]),
            line = d3.svg.line()
                    .x(function(d) { return x(d[0]); })
                    .y(function(d) { return y(d[1]); });

        svg.attr('width', DOC_WIDTH);
        path
            .datum(data)
            .attr('d', line);

        if (data[data.length - 1][1] < DOC_HEIGHT / 2) {
            $('.alert').addClass('u-hidden');
        } else {
            $('.alert').removeClass('u-hidden');
        }
    }

    var inter = setInterval(function() {
        var timestamp = Date.now(),
            top = window.scrollY;
        data.push([timestamp, top]);
        if (data.length > 100) {
            data.shift();
        }
        render(data);
    }, 200);

})(window.jQuery, window.d3);