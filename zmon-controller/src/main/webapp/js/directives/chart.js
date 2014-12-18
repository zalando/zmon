angular.module('zmon2App').directive('chart', [ '$timeout', '$window', function($timeout, $window) {
    return {
        restrict: 'E',
        scope: {
            data: '=chartData',
            container: '@labelContainer',
            options: '=options'
        },
        link: function(scope, elem, attrs) {
            var chart = null,
                lastData = null,
                options = {
                    legend: {
                        show: scope.container ? true : false,
                        container: scope.container ? $('.chart-label-container[data-containerId="' + scope.container + '"]') : null
                    },
                    xaxis: {
                        color: 'rgba(255,255,255,0.3)',
                        tickColor: 'rgba(255,255,255,0.3)',
                        ticks: function(axis) {
                            return [[axis.min, $.plot.formatDate(new Date(axis.min), '%H:%M')],
                                    [axis.max, $.plot.formatDate(new Date(axis.max), '%H:%M')]];
                        },
                        font: {
                            color: 'rgba(255,255,255,0.9)'
                        }
                    },
                    yaxis: {
                        color: 'rgba(255,255,255,0.3)',
                        tickColor: 'rgba(255,255,255,0.3)',
                        labelWidth: 40,
                        tickFormatter: function(value) {
                            if (value >= 1000000000) {
                                return (value / 1000000000).toFixed(1) + "G";
                            }
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + "M";
                            }
                            if (value >= 1000) {
                                return (value / 1000).toFixed(1) + "K";
                            }
                            return value;
                        },
                        font: {
                            color: 'rgba(255,255,255,0.9)'
                        }
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.3)'
                    },
                    lines: {
                        fill: true
                    },
                    colors: ['#ffffff'],
                    selection: {
                        mode: 'xy'
                    }
                };


            if (typeof scope.options !== 'undefined') {
                options = _.extend(options, scope.options);
            }

            scope.$watch('data', function(newData) {
                // If all entities that threw an alert have non-plottable data, then newData=[] (see MainAlertService.transformResultsToChartData())
                if (newData && newData.length) {
                    lastData = newData;
                    elem.show();

                    if (!chart) {
                        // $.plot should occur after DOM is rendered and visible,
                        // otherwise flot fails to calculate its width.
                        // timeout seems to be the only way to do such a thing in angularjs.
                        $timeout(function() {
                            if (elem.height() && elem.width()) {
                                chart = $.plot(elem, newData, options);
                            }
                        }, 100);
                    } else {
                        chart.setData(newData);
                        chart.setupGrid();
                        chart.draw();
                    }

                    // Correct positioning of y-axis
                    elem.find('.flot-y-axis').css('margin-left', '-20px');
                } else {
                    elem.hide();
                }
            });

            scope.$watch('options', function(newOptions) {
                if (newOptions && scope.data) {
                    options = _.extend(options, newOptions);
                    $timeout(function() {
                        if (elem.height() && elem.width()) {
                            chart = $.plot(elem, scope.data, options);
                        }
                    }, 100);
                }
            }, true);

            // Watch to changes on the URL to update the chart when switching compact view on and off.
            scope.$on('$routeUpdate', function(){
                if (!lastData) {
                    return;
                }
                chart = $.plot(elem, lastData, options);
            });

            $(elem).dblclick(function() {
                delete options.xaxis.min;
                delete options.xaxis.max;
                delete options.yaxis.min;
                delete options.yaxis.max;
                chart = $.plot(elem, scope.data, options);
            });

            $(elem).bind("plotselected", function(event, ranges) {
                options.xaxis.min = ranges.xaxis.from;
                options.xaxis.max = ranges.xaxis.to;
                options.yaxis.min = ranges.yaxis.from;
                options.yaxis.max = ranges.yaxis.to;
                chart = $.plot(elem, scope.data, options);
            });

            angular.element($window).bind('resize', function() {
                if (scope.data && scope.data.length && elem.height()) {
                    lastData = scope.data;
                    chart = $.plot(elem, scope.data, options);
                }
            });
        }
    };
}]);
