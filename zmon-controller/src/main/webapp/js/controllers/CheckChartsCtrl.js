angular.module('zmon2App').controller('CheckChartsCtrl', ['$scope', '$routeParams', '$location', 'localStorageService', 'MainAlertService', 'CommunicationService', 'FeedbackMessageService', 'LoadingIndicatorService', 'APP_CONST',
    function($scope, $routeParams, $location, localStorageService, MainAlertService, CommunicationService, FeedbackMessageService, LoadingIndicatorService, APP_CONST) {

        $scope.$parent.activePage = 'check-charts';

        // Constants useful for date normalization
        var DAY = 1000 * 60 * 60 * 24;
        var WEEK = DAY * 7;

        // Used to find correct Y axis scale
        var max = 0;
        var min = null;

        // Start loading animation
        LoadingIndicatorService.start();

        // Store final destination in case user is not logged in
        localStorageService.set('returnTo', '/#' + $location.url());

        // Get ID of check from url parameters
        $scope.check_id = $routeParams.checkId;

        // Fetch check name
        CommunicationService.getCheckDefinition($scope.check_id).then(function(data) {
            $scope.check_name = data.name;
        });

        // All entities dict by name
        $scope.entities = {};

        // List of names of all available entities for this check
        $scope.availableEntities = [];
        $scope.selectedEntities = []

        // Controls to enable and disable charts by type: 1 day or 2 weeks and date range.
        $scope.dayChartEnabled = true;
        $scope.weeksChartEnabled = true;
        $scope.useDateRange = false;
        $scope.compareMode = false;

        // Keep account for chart data series selection
        $scope.dataSeries = [];
        $scope.selectedDataSeries = [];


        /*
         * Date settings
         */
        $scope.dateOptions = {
            format: 'dd-MMMM-yyyy',
            calendar: {
                'year-format': "'yy'",
                'starting-day': 1
            },
            time: {
                hstep: 1,
                mstep: 15,
                ismeridian: false
            }
        }

        // Pop up calendar
        $scope.showCalendar = function($event, cal) {
            $event.preventDefault();
            $event.stopPropagation();
            _.each($scope.openedCalendars, function(isOpen, cal) {
                $scope.openedCalendars[cal] = false;
            });
            $scope.openedCalendars[cal] = true;
        };

        // Opened calendar flags
        $scope.openedCalendars = {
            'from': false,
            'to': false
        }


        /*
         * Chart settings
         */

        $scope.chartOptions = {
            xaxis: {
                color: null,
                tickColor: null,
                font: null,
                mode: "time",
                timezone: "browser"
            },
            yaxis: {
                color: null,
                tickColor: null,
                font: null,
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
                }
            },
            grid: {
                hoverable: true
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s: %y"
            },
            lines: {},
            colors: ["#2980B9", "#D35400", "#F39C12", "#7F8CFF", "#C0392B", "#7F8C8D"],
            selection: {
                mode: "xy",
                color: "lightblue"
            }
        };

        $scope.chartOptionsHour = angular.copy($scope.chartOptions);
        $scope.chartOptionsDays = angular.copy($scope.chartOptions);

        $scope.chartOptionsHour.xaxis.timeformat = "%H:%M";
        $scope.chartOptionsDays.xaxis.timeformat = "%d.%m";

        // Set custom date range and reload charts
        $scope.apply = function() {
            setTimes();
            fetchSelectedEntities();
            setStateToUrl();
        };

        // Show/hide custom date range form
        $scope.toggleDateRange = function() {
            if ($scope.useDateRange) {
                $scope.dayChartEnabled = true;
                $scope.weeksChartEnabled = true;
            } else {
                $scope.dayChartEnabled = false;
                $scope.weeksChartEnabled = false;
                $scope.apply();
            }
            setStateToUrl();
        };

        // Show/hide 1 day and/or 2 weeks charts
        $scope.toggleDefaultChart = function(id) {
            $scope.useDateRange = false;
            initDates();
            fetchSelectedEntities();

            $location.search('dayChart', null);
            $location.search('weeksChart', null);

            if (id == 'dayChart' && $scope.dayChartEnabled) {
                $location.search('dayChart', 'no');
            }
            if (id == 'weeksChart' && $scope.weeksChartEnabled) {
                $location.search('weeksChart', 'no');
            }
            setStateToUrl();
        };

        // Show/Hide charts for a selected entity
        $scope.toggleEntity = function(entity) {
            entity.selected = !entity.selected;
            fetchSelectedEntities();
            setStateToUrl();
        };

        // Update charts after a change on data series selection
        $scope.toggleDataSeries = function(id) {
            // Include/Exclude data series from array of unselected
            if ($scope.selectedDataSeries.indexOf(id) === -1) {
                $scope.selectedDataSeries.push(id);
            } else {
                $scope.selectedDataSeries = _.without($scope.selectedDataSeries, id);
            }
            setSelectedDataSeriesUrl();
            fetchSelectedEntities();
        };

        // Select/Unselect all data series
        $scope.toggleAllDataSeries = function() {
            if ($scope.selectedDataSeries.length === $scope.dataSeries.length) {
                $scope.selectedDataSeries = [];
                _.each($scope.dataSeries, function(s) {
                    s.selected = false;
                });
            } else {
                _.each($scope.dataSeries, function(s) {
                    s.selected = true;
                    if ($scope.selectedDataSeries.indexOf(s.name) === -1) {
                        $scope.selectedDataSeries.push(s.name);
                    }
                });
            };
            setSelectedDataSeriesUrl();
            fetchSelectedEntities();
        }

        // Select/Unselect all available entities
        $scope.toggleAllEntities = function() {
            if ($scope.selectedEntities.length === $scope.availableEntities.length) {
                _.each($scope.selectedEntities, function(eid) {
                    $scope.entities[eid].selected = false;
                });
                $scope.selectedEntities = [];
            } else {
                _.each($scope.availableEntities, function(eid) {
                    $scope.entities[eid].selected = true;
                    if ($scope.selectedEntities.indexOf(eid) === -1) {
                        $scope.selectedEntities.push(eid);
                    }
                });
            };
            setSelectedEntitiesUrl();
            fetchSelectedEntities();
        }

        $scope.$watch('compareMode', function(mode) {
            if (mode) {
                $scope.chartOptionsHour.yaxis.max = max;
                $scope.chartOptionsDays.yaxis.max = max;
                $scope.chartOptionsHour.yaxis.min = min;
                return $scope.chartOptionsDays.yaxis.min = min;
            }
            delete $scope.chartOptionsHour.yaxis.max;
            delete $scope.chartOptionsDays.yaxis.max;
            delete $scope.chartOptionsHour.yaxis.min;
            delete $scope.chartOptionsDays.yaxis.min;
        });

        // Get all entities available for this alert
        var getAvailableEntities = function(cb) {
            CommunicationService.getCheckResults($scope.check_id, null, 1).then(function(data) {
                $scope.availableEntities = _.pluck(data, 'entity').sort();
                _.each($scope.availableEntities, function(e) {
                    $scope.entities[e] = {
                        name: e,
                        data: [[],[]],
                        selected: false
                    };
                });

                cb();
            });
        };

        // Gets chart data for the specified chart types and prepares it to be plotted.
        var getEntityCharts = function(entity) {

            var params = {
                check_id: $scope.check_id,
                entity_id: entity.name,
                aggregate: 15,
                aggregate_unit: "minutes",
                start_date: new Date(),
                end_date: new Date()
            }

            params.start_date.setDate(params.start_date.getDate() -1);

            if ($scope.useDateRange) {
                params.start_date = new Date($scope.dates.startDate);
                params.end_date = new Date($scope.dates.endDate);
            }

            params.end_date.setHours(params.end_date.getHours() - 1);
            getChartsData(params, function(cd1) {
                params.start_date = $scope.useDateRange ? new Date($scope.dates.endDate) : new Date();
                params.start_date.setHours(params.start_date.getHours() -1);
                params.end_date = $scope.useDateRange ? $scope.dates.endDate : new Date();
                params.aggregate = 1;
                getChartsData(params, function(cd2) {
                    entity.data[0] = mergeChartData(cd1, cd2);
                });
                LoadingIndicatorService.stop();
                setStateToUrl();
                setMaxY(entity);
            });

            // Fetch weeks chart if not using custom date range
            if (!$scope.useDateRange) {
                var start_date = new Date();
                start_date.setDate(start_date.getDate() - 14);
                params.start_date = start_date;
                params.end_date = new Date();
                params.aggregate = 30;
                getChartsData(params, function(c3) {
                    c3 = sortChartData(c3);
                    _.each(c3, function(cd3) {
                        cd3.data = normalizeChartData(cd3.data, 2*WEEK);
                    });
                    entity.data[1] = c3;
                    setMaxY(entity);
                });
                setStateToUrl();
            }
        };

        // Fetch chart data from server. Dates in miliseconds.
        var getChartsData = function(params, cb) {
            params.start_date = params.start_date.getTime();
            params.end_date = params.end_date.getTime();
            CommunicationService.getCheckCharts(params).then(
                function(data) {
                    var chartData = {};
                    getDataSeries(data);
                    chartData[params.entity_id] = [];
                    var labels = _.pluck(data.group_results, 'key').sort();
                    var palette = getColorPalette(labels);
                    _.each(data.group_results, function(gr, i) {
                        if ($scope.selectedDataSeries.indexOf(gr.key) !== -1) {
                            chartData[params.entity_id].push({
                                label: gr.key,
                                data: gr.values,
                                color: palette[gr.key]
                            });
                        }
                    });
                    cb(chartData[params.entity_id]);
                },
                function(httpStatus) {
                    cb();
                }
            );
        };

        // Concatenates chart data for 1-day and custom-date charts
        var mergeChartData = function(c1, c2) {
            c1 = sortChartData(c1);
            c2 = sortChartData(c2);
            _.each(c1, function(cd1, i) {
                _.each(c2, function(cd2) {
                    if ((typeof cd1.label === 'undefined' && typeof cd2.label === 'undefined')
                        || (typeof cd1.label !== 'undefined' && cd1.label === cd2.label)) {
                        cd1.data = cd1.data.concat(cd2.data);
                    }
                });
                var customDateGap = $scope.dates.endDate - $scope.dates.startDate;
                cd1.data = normalizeChartData(cd1.data, $scope.useDateRange ? customDateGap : DAY);
            });
            return c1;
        };

        // Sort chart data according to their labels
        var sortChartData = function(data) {
            return data.sort(function(a, b) {
                if (typeof a.label === 'undefined' || typeof b.label === 'undefined') {
                    return 0;
                };
                var labelA = a.label.toLowerCase();
                var labelB = b.label.toLowerCase();
                if (labelA < labelB) { return -1; };
                if (labelA > labelB) { return 1; };
                return 0;
            });
        };

        // Normalize chart data to a specific time gap
        var normalizeChartData = function(data, gap) {
            if (!(data instanceof Array) && data.length !== 0) {
                return data;
            }
            var first = data[0][0];
            var last = data[data.length-1][0];
            if (first > last - gap) {
                data = [ [last - gap, null] ].concat(data);
            };
            return data;
        };

        // Gets all data series for this alert, from all charts and derives
        // state from querystring. None selected by default.
        var getDataSeries = function(data) {
            if ($location.search().series) {
                $scope.selectedDataSeries = $location.search().series.split(',');
            }
            _.each(_.pluck(data.group_results, 'key').sort(), function(label, index) {
                if (_.pluck($scope.dataSeries, 'name').indexOf(label) === -1) {
                    var s = false;
                    if ($location.search().series) {
                        s = $location.search().series.split(',').indexOf(label) !== -1;
                    } else if (index < 5) {
                        s = true;
                    }
                    $scope.dataSeries.push({
                        name: label,
                        selected: s
                    });
                    if (s) {
                        $scope.selectedDataSeries.push(label);
                    };
                }
            });
        };

        // Set initial custom dates
        var initDates = function() {

            var now = new Date();
            var startDate = new Date();
            var endDate = new Date();

            startDate.setDate(startDate.getDate() -1);

            if ($location.search().startDate) {
                startDate = new Date($location.search().startDate);
            }

            if ($location.search().endDate) {
                endDate = new Date($location.search().endDate);
            }

            $scope.dates = {
                startDate: startDate,
                endDate: new Date(endDate),
                startTime: new Date(startDate),
                endTime: new Date(endDate)
            }

        };

        // Applies hour and minutes to custom date range dates
        var setTimes = function() {
            $scope.dates.startDate.setHours($scope.dates.startTime.getHours());
            $scope.dates.startDate.setMinutes($scope.dates.startTime.getMinutes());
            $scope.dates.endDate.setHours($scope.dates.endTime.getHours());
            $scope.dates.endDate.setMinutes($scope.dates.endTime.getMinutes());
        };

        // Gets chart data for each of the selected entities
        var fetchSelectedEntities = function() {
            LoadingIndicatorService.start();
            var isAnyEntitySelected = false;
            _.each($scope.entities, function(e) {
                if (e.selected) {
                    isAnyEntitySelected = true;
                    getEntityCharts(e);
                }
            });

            // If no entity is selected (default), LoadIndicator must be stopped.
            if (!isAnyEntitySelected) {
                LoadingIndicatorService.stop();
            }
        };

        // Set application state from query string parameters
        var getStateFromUrl = function() {
            var qs = $location.search();
            if (qs.entity_id) {
                _.each(qs.entity_id.split(','), function(e) {
                    if (typeof $scope.entities[e] !== 'undefined') {
                        $scope.entities[e].selected = true;
                    }
                });
            }

            if (typeof qs.startDate !== 'undefined' || typeof qs.endDate !== 'undefined') {
                $scope.useDateRange = true;
                $scope.dayChartEnabled = false;
                $scope.weeksChartEnabled = false;
            }
            if (qs.dayChart === 'no') {
                $scope.dayChartEnabled = false;
            }
            if (qs.weeksChart === 'no') {
                $scope.weeksChartEnabled = false;
            }

        };

        // Set application state in URL query string
        var setStateToUrl = function() {

            // Get list of selected entities
            $scope.selectedEntities = [];
            _.each($scope.availableEntities, function(entityId) {
                if ($scope.entities[entityId].selected) {
                    $scope.selectedEntities.push(entityId);
                }
            });

            // Set entity ids on url
            if ($scope.selectedEntities.length) {
                $location.search('entity_id', $scope.selectedEntities.join(','));
            } else {
                $location.search('entity_id', null);
            }

            // Set custom date range
            if ($scope.useDateRange) {
                var sd = formatDate($scope.dates.startDate);
                var ed = formatDate($scope.dates.endDate);;
                $location.search('startDate', sd);
                $location.search('endDate', ed);
            } else {
                $location.search('startDate', null);
                $location.search('endDate', null);
            }
        };

        // Set Selected Data Series state to URL
        var setSelectedDataSeriesUrl = function() {
            $location.search('series', null);
            if ($scope.selectedDataSeries.length) {
                $location.search('series', $scope.selectedDataSeries.join(','));
            }
        };

        var setSelectedEntitiesUrl = function() {
            $location.search('entity_id', null);
            if ($scope.selectedEntities.length) {
                $location.search('entity_id', $scope.selectedEntities.join(','));
            }
        };

        // Format date for url parameters
        var formatDate = function(d) {
            var f = '';
            f = [ d.getFullYear(), d.getMonth()+1, d.getDate()  ].join('-');
            f += ' ' + d.getHours() + ':' + d.getMinutes();
            return f;
        };

        // Fin the maximum and minimum for vertical values for all data in all entities
        var setMaxY = function(entity) {
            var points = [];
            for (var i = 0; i < entity.data.length; i++) {
                var entityData = entity.data[i];
                for (var j = 0; j < entityData.length; j++) {
                    var serie = entityData[j].data;
                    for (var i = 0; i < serie.length; i++) {
                        var point = serie[i];
                        if (point.length && point[1]) {
                            var p = point[1];
                            points.push(p);
                        }
                    }
                }
            };
            var _max = Math.max.apply(this, points);
            var _min = Math.min.apply(this, points);
            max = _max > max ? _max : max;
            min = _min < min || min === null ? _min : min;
            if ($scope.compareMode) {
                $scope.chartOptionsHour.yaxis.max = max;
                $scope.chartOptionsDays.yaxis.max = max;
                $scope.chartOptionsHour.yaxis.min = min;
                $scope.chartOptionsDays.yaxis.min = min;
            }
        };

        // Non-refreshing; one-time listing
        MainAlertService.removeDataRefresh();

        // Init dates for custom date range
        initDates();

        // Starts. Gets entities list, state of app from URL and fetch charts.
        getAvailableEntities(function() {
           getStateFromUrl();
           fetchSelectedEntities();
        });
    }
]);
