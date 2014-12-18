angular.module('zmon2App').directive('widgetConfigChart', ['$compile', '$log', 'MainAlertService',
    function ($compile, $log, MainAlertService) {
        return {
            restrict: 'E',
            scope: {
                widget: '=',
                chartData: '=',
            },
            templateUrl: 'templates/widgetConfigChart.html',
            link: function (scope, element, attrs, controller) {

                var options = scope.widget.options || {};

                scope.availableAggregators = [ "avg", "dev", "min", "max", "sum", "count", "least squares" ];
                scope.availableAggregatorUnits = [ "seconds", "minutes", "hours" ];
                scope.availableTimeRangeUnits = [ "seconds", "minutes", "hours", "days", "weeks", "months", "years" ];
                scope.series = scope.widget.series;
                scope.groupByTags = [ "entity", "key" ];
                scope.aggregators = [];
                scope.area = true;
                scope.isKairosChart = false;
                scope.metric = { tags: {} };

                if (options.metrics instanceof Array && options.metrics.length) {
                    scope.isKairosChart = true;
                    scope.metric = options.metrics[0];
                }

                if (options.lines) {
                    var lines = options.lines;
                    if (lines instanceof Array) {
                        lines = lines[0];
                    }
                    scope.area = lines.fill;
                }

                scope.addAggregation = function () {
                    scope.aggregators = [{
                        name: '',
                        align_sampling: true,
                        sampling: {
                            value: 0,
                            unit: ''
                        }
                    }];
                };

                scope.$watch('series', function() {
                    if (typeof scope.series === 'undefined' || scope.series.length === 0) {
                        return delete scope.widget.series;
                    }
                    scope.widget.series = scope.series;
                }, true);

                scope.$watch('groupByTags', function() {
                    if (options.metrics && options.metrics.length && scope.groupByTags.length ) {
                        var metric = options.metrics[0];
                        metric.group_by = [{
                            name: "tag",
                            tags: scope.groupByTags
                        }];
                    }
                }, true);

                scope.$watch('aggregators', function() {
                    if (typeof scope.aggregators !== 'undefined' && scope.aggregators.length) {
                        var a = scope.aggregators[0];
                        if (a.name && a.sampling.value && a.sampling.unit) {
                            options.metrics[0].aggregators = scope.aggregators;
                        }
                    }
                }, true);

                scope.$watch('area', function(value) {
                    var area = {
                        lines: {
                            fill: value
                        }
                    };
                    _.extend(options, area);
                });

                // Find Tag key
                if (options.metrics instanceof Array && options.metrics.length) {
                    var metric = options.metrics[0];
                    scope.aggregators = metric.aggregators;

                    if (metric.group_by instanceof Array && metric.group_by.length) {
                        var groupBy = metric.group_by[0];
                        scope.groupByTags = groupBy.tags;
                    }
                }
            }
        };
    }
]);
