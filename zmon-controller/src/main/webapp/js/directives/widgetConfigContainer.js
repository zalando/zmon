angular.module('zmon2App').directive('widgetConfigContainer', ['$compile', '$log', 'MainAlertService',
    function ($compile, $log, MainAlertService) {
        return {
            restrict: 'E',
            scope: {
                widgets: '=',
                widgetsJson: '=',
                widgetTypes: '=',
                invalidJson: '=',
                isVisible: '=',
                emptyJson: '=?',
                exclude: '=?'
            },
            templateUrl: 'templates/widgetConfigContainer.html',
            link: function (scope, element, attrs, controller) {

                scope.selectedWidgetType = scope.widgetTypes[0];
                scope.emptyJson = scope.emptyJson || (scope.emptyJson = false);

                // Removes from the results set the filter definition at given index
                scope.removeWidget = function (idx) {
                    scope.widgets.splice(idx, 1);
                };

                // Add a new chart by inserting at the beginning of the widgets array an empty chart object.
                scope.addChart = function() {
                    var chart = {
                        type: 'chart',
                        options: {
                            series: {
                                stack: false
                            },
                            lines: {
                                show: true
                            },
                            legend: {
                                show: true,
                                position: 'ne',
                                backgroundOpacity: 0.1
                            },
                            cache_time: 0,
                            start_relative: {
                                value: '30',
                                unit: 'minutes'
                            }
                        }
                    }

                    if (scope.selectedWidgetType.type === "Kairos Chart") {
                        chart.options.metrics = [{
                            tags: {},
                            group_by: []
                        }]
                    }

                    scope.widgets = [ chart ].concat(scope.widgets);
                };

                scope.$watch('isVisible', function(formIsVisible) {
                    if (scope.invalidJson) {
                        return;
                    }
                    if (formIsVisible) {
                        return scope.widgets = JSON.parse(scope.widgetsJson);
                    }
                    scope.widgetsJson = angular.toJson(scope.widgets, true);
                });

                scope.$watch('widgetsJson', function() {
                    if (scope.widgetsJson) {
                        scope.widgets = JSON.parse(scope.widgetsJson);
                    }
                }, true);

            }
        };
    }
]);
