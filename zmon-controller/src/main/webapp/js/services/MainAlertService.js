angular.module('zmon2App').factory('MainAlertService', ['$http', '$q', '$log', '$interval', '$sanitize', 'CommunicationService',
    function($http, $q, $log, $interval, $sanitize, CommunicationService) {
        var service = {};

        service.getNow = function() {
            return (new Date()).getTime() / 1000;
        };

        // Keep track, by the requester's uniqId, of:
        //  (1) the $interval promise for this data refresh
        //  (2) the refresh rate
        //  (3) the
        service.dataRefreshIntervalPromises = {};
        service.dataRefreshRates = {};
        service.dataRefreshCallbacks = {};
        service.serviceStatus = {
            isStatusRefreshing: false,
            lastUpdate: service.getNow(),
            hasDataRefresh: false, // whether current page is subject to data refreshing
            isDataRefreshing: false, // if page which is subject to data refreshing is currently indeed refreshing
            checkInvocationsCache: {}
        };

        /*
         * Given two timestamps in epoch, returns how many milliseconds apart they are; order doesn't matter
         */
        service.millisecondsApart = function(ts1, ts2) {
            return Math.round(Math.abs(ts1 - ts2) * 1000);
        };

        service.logError = function(errMsg) {
            $log.error('ERROR:: ' + errMsg);
        };

        service.getLastUpdate = function() {
            return this.serviceStatus.lastUpdate;
        };

        service.getQueueSize = function() {
            return this.serviceStatus.queueSize;
        };

        service.getStatus = function() {
            // Async refresh for next time
            this.refreshStatus();
            // Return what we have now
            return this.serviceStatus;
        };

        /**
         * Transforms results from CommunicationService.getCheckResults() to chart compatible format
         * Returns an object whose keys are entity names and whose value are :
         *      Case 1: arrays of objects with "label" and "data" keys where "data" is an array of [x,y] subarrays of the points to plot
         *      Case 2: arrays of [x,y] subarrays of the points to plot
         */
        service.transformResultsToChartData = function(checkResults) {
            var returnVal = _.foldl(checkResults, function(memo, curr) {

                if (typeof curr.results === 'undefined') {
                    console.error(new Date(), 'ERROR No results in current check object for', curr);
                    return memo;
                }

                // Make sure there are no y-axis values that are not plottable; the only acceptable value types are Object and Number
                // If a single of the values is not Object or Number, then this entity is ommitted from the chart
                memo.hasNonPlottableValues = _.some(curr.results, function(xyObj) {
                    if (typeof xyObj.value === 'object') {
                        return _.some(xyObj.value, function(series) {
                            return isNaN(series);
                        });
                    } else {
                        return isNaN(xyObj.value);
                    }
                });

                // Made it here, we know all values are plottable
                /** CASE 1: transform for checkResults of a single entity and values are objects: e.g. load averages {"load1": 1.22, "load5": 1.34, "load15": 2.47}
                    Returned data format is an object:
                        {
                            "GLOBAL": [
                                {
                                    "label": "count",
                                    "data": [
                                        [
                                            1392210976107,
                                            15
                                        ],
                                        ....
                                        [
                                            1392209824769,
                                            15
                                        ]
                                    ]
                                }
                            ]
                        }
                 */
                if (typeof curr.results[0].value === 'object') {
                    // console.log('1) CURR ENTITY = ', curr.entity);
                    // Temporary collection for nested alert results. Maybe it's possible to map the results
                    // to chart data without a temporary variable, I didn't manage.
                    try {
                        var tmp = {};
                        _.each(_.keys(curr.results[0].value), function(key) {
                            tmp[key] = _.map(curr.results, function(result) {
                                return [Math.round(result.ts * 1000), result.value[key]];
                            });
                        });
                        memo[curr.entity] = _.map(_.keys(tmp).sort(), function(key) {
                            return {
                                label: key,
                                data: tmp[key]
                            };
                        });
                    } catch (err) {
                        console.error(new Date(), 'ERROR CASE 1 On entity: ', curr.entity, err);
                    }
                } else {
                    if (checkResults.length === 1) {
                        /** CASE 2: transform for checkResults of a single entity and values are simple numbers e.g. order failure for entity GLOBAL
                            Returned data format is an object:
                            {
                                "GLOBAL": [
                                    [
                                        [
                                            1392210976007,
                                            6.00006
                                        ],
                                        ...
                                        [
                                            1392209824702,
                                            6.500040000000001
                                        ]
                                    ]
                                ]
                            }
                         *
                         */
                        memo[curr.entity] = [_.map(curr.results, function(nextPoint) {
                            try {
                            // a [x,y] point
                                return [Math.round(nextPoint.ts * 1000), nextPoint.value];
                            } catch (err) {
                                console.error(new Date(), 'ERROR On CASE 2 for entity', curr.entity, err);
                            }
                        })];
                    } else {
                        /** CASE 3: transform for checkResults of multiple entities and values are simple numbers e.g. redis queue sizes of various entities
                            Returned data format is an array:
                            [
                                {
                                    "label": "entity-1",
                                    "data": <array of [x,y] points>
                                },
                                {
                                    "label": "entity-2",
                                    "data": <array of [x,y] points>
                                }
                            ]
                        */
                        if (!Array.isArray(memo)) {
                            memo = [];
                        }
                        // var minTs = _.min(_.pluck(curr.results, 'ts'));
                        // var maxTs = _.max(_.pluck(curr.results, 'ts'));
                        try {
                            var data = _.map(curr.results, function(nextPoint, idx) {
                                return [Math.round(nextPoint.ts * 1000), nextPoint.value];
                            });
                            memo.push({
                                label: curr.entity,
                                data: data,
                                lines: {
                                    show: true,
                                    fill: false
                                }
                            });
                        } catch (err) {
                            console.error('CASE 3 Catch error', err, curr);
                        }
                    }
                }
                return memo;
            }, {});
            return returnVal;
        };

        /*
         * Refreshes serviceStatus i.e. queueSize, lastUpdate etc.
         */
        service.refreshStatus = function() {
            var that = this;
            try {
            CommunicationService.getStatus().then(function(data) {
                var now = that.getNow();

                that.serviceStatus.queueSize = parseInt(data.queue_size);
                that.serviceStatus.workersTotal = parseInt(data.workers_total);
                that.serviceStatus.workersActive = parseInt(data.workers_active);
                that.serviceStatus.checkInvocations = parseInt(data.check_invocations);
                that.serviceStatus.checksPerSecond = 0;
                that.serviceStatus.previousUpdate = that.serviceStatus.lastUpdate;
                that.serviceStatus.lastUpdate = now;
                that.serviceStatus.isStatusRefreshing = true;
                that.serviceStatus.workers = data.workers;
                that.serviceStatus.queues = data.queues;

                // Calculate checks per second for each worker.
                _.each(that.serviceStatus.workers, function(worker) {
                    var lastCheckInvocations = that.serviceStatus.checkInvocationsCache[worker.name] ? that.serviceStatus.checkInvocationsCache[worker.name] : worker.check_invocations;

                    worker.lastExecutionTime = moment.utc(worker.last_execution_time * 1000).fromNow();
                    worker.checksPerSecond = (worker.check_invocations - lastCheckInvocations) / (now - that.serviceStatus.previousUpdate);

                    that.serviceStatus.checkInvocationsCache[worker.name] = worker.check_invocations;

                    // filter scheduler nodes from check count
                    if(worker.name.indexOf('s-')!=0) {
                        that.serviceStatus.checksPerSecond += worker.checksPerSecond;
                    }
                });
            });
            } catch (err) {
                console.error(new Date(), 'ERROR MainAlertService.refreshStatus', err);
                service.pauseDataRefresh();
            }
        };

        /*
         * Stops all data refreshes, if any, without removing them though
         * E.g. for the dashboard, it will stop the refresh of the alerts + the refreshes of each one of the widgets
         */
        service.pauseDataRefresh = function() {
            var that = this;
            this.serviceStatus.isDataRefreshing = false;
            _.each(_.keys(that.dataRefreshIntervalPromises), function(uniqId) {
                $interval.cancel(that.dataRefreshIntervalPromises[uniqId]);
            });
        };

        /**
         * Stops all data refreshes and re-inits the data refreshing accounting
         */
        service.pauseAndCleanUpDataRefresh = function() {
            this.pauseDataRefresh();
            this.dataRefreshIntervalPromises = {};
            this.dataRefreshRates = {};
            this.dataRefreshCallbacks = {};
        };

        /*
         * Starts the refresh of the data (based on passed callback) and keeps track of it using a uniqId of the entity that requests this refresh
         * The param "uniqId" can be e.g. 'dashboardCtrl' or 'gauge-1-restsn03:100' which is a combination of "widgetType-checkId-entityName"
         * This way we can keep track of multiple data refreshes, as is the case for the dashboard page where we have 1 data refresh for the alerts and 1 data refresh for each of the widgets
         */
        service.startDataRefresh = function(uniqId, dataRefreshCallback, dataRefreshRate, isPageLoad) {
            if (isPageLoad) {
                // Pause current data refresh, if any, and clean up
                this.pauseAndCleanUpDataRefresh();
            }

            this.serviceStatus.hasDataRefresh = true;
            this.serviceStatus.isDataRefreshing = true;

            this.dataRefreshRates[uniqId] = dataRefreshRate;
            this.dataRefreshCallbacks[uniqId] = dataRefreshCallback;
            // Exec the passed callback that fetches the corresponding data
            dataRefreshCallback();

            this.dataRefreshIntervalPromises[uniqId] = $interval(_.bind(function() {
                dataRefreshCallback();
            }, this), dataRefreshRate);
        };

        service.resumeDataRefresh = function() {
            var that = this;
            this.serviceStatus.isDataRefreshing = true;
            _.each(_.keys(this.dataRefreshIntervalPromises), function(uniqId) {
                that.startDataRefresh(uniqId, that.dataRefreshCallbacks[uniqId], that.dataRefreshRates[uniqId]);
            });
        };

        service.removeDataRefresh = function() {
            // Pause current data refresh, if any, and clean up
            this.pauseAndCleanUpDataRefresh();
            // Reflect that in the serviceStatus
            this.serviceStatus.hasDataRefresh = false;
            this.serviceStatus.isDataRefreshing = false;
        };

        return service;
    }
]);
