angular.module('zmon2App').controller('DashboardCtrl', ['$scope', '$log', '$routeParams', 'localStorageService', '$location', 'MainAlertService', 'CommunicationService', 'DowntimesService', 'LoadingIndicatorService', 'APP_CONST',
    function($scope, $log, $routeParams, localStorageService, $location, MainAlertService, CommunicationService, DowntimesService, LoadingIndicatorService, APP_CONST) {

        $scope.dashboardId = $routeParams.dashboardId || localStorageService.get('dashboardId');

        if (!$routeParams.dashboardId && $scope.dashboardId) {
            var p = '/dashboards/view/' + $scope.dashboardId;
            return $location.path(p);
        }

        $scope.DashboardCtrl = this;

        // Set in parent scope which page is active for the menu styling
        $scope.$parent.activePage = 'dashboard';

        $scope.alerts = [];
        $scope.alertsInDowntime = [];
        $scope.alertsLoaded = false;
        $scope.filter = {};
        $scope.checkResultsByCheckIdByEntity = {};
        $scope.showWidgets = JSON.parse(localStorageService.get('showWidgets'));
        $scope.compact = false;
        $scope.tagsEditOpen = false;
        $scope.allTags = [];
        $scope.showAlertsWithAllEntitiesInDowntime = $location.search().ad || false;

        $scope.$watch('showWidgets', function() {
            localStorageService.add('showWidgets', $scope.showWidgets);
        });

        $scope.charts = {};

        $scope.widgets = [];
        if ($scope.dashboardId > 0) {

            CommunicationService.getDashboard($scope.dashboardId).then(function(data) {
                var widgetConfigurations = JSON.parse(data.widget_configuration);
                // $scope.widgets contains the widget configuration and is passed to directive dashboard-widget (see dashboard.html)
                $scope.widgetsConf = $scope.layoutWidgets(widgetConfigurations);
                $scope.dashboardTags = data.tags;

                // Get compact view variable from query string, then from database, or set default to false.
                var isCompact = $location.search().compact || data.view_mode == "COMPACT" || false;

                // Toggle view mode: compact or full.
                $scope.toggleCompactView(isCompact);

                // If no showWidgets is set on local storage, check if dashboard has widgets and show them by default.
                if ($scope.showWidgets === null) {
                    $scope.showWidgets = ($scope.widgetsConf.length > 0);
                }
            });
        }

        $scope.layoutWidgets = function(widgetsConf) {
            if (widgetsConf.length === 0) {
                // nothing to do
                return;
            }
            // Get widths of widgets that have width set
            var widths = _.filter(_.pluck(widgetsConf, 'width'), function(v) {
                return typeof v !== 'undefined';
            });
            var totalWidth = _.reduce(widths, function(memo, num) {
                return memo + num;
            }, 0);
            // Q: What is 12?
            // A: 12 is the number of grid columns in Twitter Bootstrap
            var totalRemaining = 12 - totalWidth;
            var remaining = totalRemaining;
            var widgetsWithoutWidth = widgetsConf.length - widths.length;
            _.each(widgetsConf, function(widget) {
                if (widget.type === 'networkmap') {
                    widget.width = "full";
                } else if (typeof widget.width === 'undefined') {
                    widget.width = Math.floor(totalRemaining / widgetsWithoutWidth);
                    remaining = remaining - widget.width;
                }
            });
            // Make last widget take up all remaining space
            if (remaining > 0) {
                _.last(widgetsConf).width += remaining;
            }
            return widgetsConf;
        };

        $scope.configureWidgets = function() {
            $location.path('/dashboards/edit/' + $scope.dashboardId);
        };

        // Defines view mode to be either compact or full;
        // When triggered by dashboard button, it + updates the URL accordingly
        // OR is set according to passed value when
        $scope.toggleCompactView = function(isCompact) {
            if (isCompact === undefined) {
                $scope.compact = !$scope.compact;
            } else {
                $scope.compact = isCompact;
            }
            // Reflect it in URL
            if($scope.compact) {
                $location.search('compact', 'true');
                localStorageService.set('returnTo', '/#' + $location.url());
            } else {
                $location.search('compact', null);
                localStorageService.set('returnTo', '/#' + $location.url());
            }
        };

        // Show/Hide Alerts which all entities are in downtime
        $scope.toggleAlertsWithAllDowntime = function() {
            $scope.showAlertsWithAllEntitiesInDowntime = !$scope.showAlertsWithAllEntitiesInDowntime;
            if ($scope.showAlertsWithAllEntitiesInDowntime) {
                return $location.search('ad', true);
            }
            $location.search('ad', null);
        };

        // Show/Hide Alert Tags editor popup
        $scope.toggleTagsEditPopup = function() {
            $scope.tagsEditOpen = !$scope.tagsEditOpen;
        };

        // Close alert tags editor popup
        $scope.closeTagsEditPopup = function() {
            $scope.tagsEditOpen = false;
        };

        /* Creates in each alert a field 'oldestStartTime' whose value is the start_time of the oldest entity.
         * Also keeps track of this by alertId in the controller's oldestStartTime[]
         * Used for the 2nd level sorting (1st level sorting is done by alert priority)
         */
        $scope.evalOldestStartTimes = function(allAlerts) {
            allAlerts.forEach(function(nextAlert, idx, arr) {
                // Get the oldest start_time out of all of the entities of this specific allert
                var alertId = nextAlert.alert_definition.id;
                // Add the oldest entity's start_time for current alert as property 'oldestStartTime' of the alert
                _.extend(nextAlert, {
                    'oldestStartTime': _.min(_.pluck(_.pluck(nextAlert.entities, 'result'), 'start_time'))
                });
            });
        };

        /*
         * Returns a human readable string of the interval between alert's last update and its oldest entity
         */
        $scope.timeSinceLastUpdate = function(time) {
            return MainAlertService.millisecondsApart(time, MainAlertService.getLastUpdate());
        };

        $scope.refreshDashboardAlerts = function() {

            var queryStringParams = $location.search();
            $scope.filter = {};

            if ($scope.dashboardId) {

                CommunicationService.getDashboard($scope.dashboardId).then(function(data) {

                    // Set default alert teams
                    if (data.alert_teams.length) {
                        $scope.team = data.alert_teams.toString();
                        $scope.filter.team = $scope.team;
                    }

                    // Set default filter tags
                    if (data.tags && data.tags.length) {
                        $scope.dashboardTags = data.tags;
                        $scope.filter.tags = data.tags.toString();
                    }

                    // Override default alert teams with QS parameter
                    if (queryStringParams.team && queryStringParams.team.length) {
                        $scope.team = queryStringParams.team.toString();
                        $scope.filter.team = $scope.team;
                    }

                    //Override default filter tags with QS parameter
                    if (queryStringParams.tags) {
                        if (queryStringParams.tags === 'none') {
                            $scope.dashboardTags = [];
                            delete $scope.filter.tags;
                        } else {
                            $scope.dashboardTags = queryStringParams.tags.split(',');
                            $scope.filter.tags = $scope.dashboardTags;
                        }
                    }

                    $scope.showAllDashboardAlerts($scope.filter);

                });
                return;
            }

            // No dashboard specified. Redirect to dashboard list.
            document.location.href = "#dashboards?noFavourite";
        };


        $scope.showAllDashboardAlerts = function(filter) {
            CommunicationService.getAllAlerts(filter).then(
                function(data) {

                    $scope.alerts = data;

                    // For each alert, eval the oldest start time from the start_time's of all entities
                    $scope.evalOldestStartTimes(data);

                    // Set lowest priority on alerts in downtime
                    $scope.alertsInDowntime = [];
                    _.each(data, function(alert){
                        if ($scope.hasAllEntitiesInDowntime(alert)) {
                            alert.alert_definition.priority = 10;
                            $scope.alertsInDowntime.push(alert);
                        }
                    });

                    // For each alert, load check results history to show on graph.
                    _.each(data, function(alert) {
                        alert.inException = $scope.hasAllEntitiesFailing(alert);
                        loadCheckResults(alert);
                    });

                    $scope.alertsLoaded = true;

                    // Update lastUpdate timestamp but only if parent is available.
                    if ($scope.$parent) {
                        $scope.$parent.alertsLastUpdate = new Date() / 1000;
                    }
                }
            );
        };

        var loadCheckResults = function(alert) {

            // only get graphs for first entities
            var entitiesWithChart = _.pluck(alert.entities, 'entity');
            entitiesWithChart.sort();
            entitiesWithChart = _.first(entitiesWithChart, APP_CONST.MAX_ENTITIES_WITH_CHARTS);

            var alertId = alert.alert_definition.id;
            var checkId = alert.alert_definition.check_definition_id;

            _.each(entitiesWithChart, function(entity) {
                CommunicationService.getCheckResults(checkId, entity).then(
                    function(response) {

                        $scope.charts[alertId] = MainAlertService.transformResultsToChartData(response)[entity];

                        // Store the response per checkId & per entity; to be used by the widgets
                        // so they don't have to do async getCheckResults() calls each one by itself
                        if ($scope.checkResultsByCheckIdByEntity[checkId] === null || typeof $scope.checkResultsByCheckIdByEntity[checkId] !== 'object') {
                            $scope.checkResultsByCheckIdByEntity[checkId] = {};
                        }
                        $scope.checkResultsByCheckIdByEntity[checkId][entity] = response;
                    }
                );
            });
        };

        /**
         * Filters and returns only entities which are not in downtime right now
         */
        $scope.getNonDowntimeEntities = function(entitiesArray) {
            return _.filter(entitiesArray, function(nextEntity) {
                return nextEntity.result.downtimes.length === 0;
            });
        };

        /*
         * Returns truncated list of non-downtime entities; limit is MAX_ENTITIES_DISPLAYED entities
         */
        $scope.truncateNonDowntimeEntities = function(entitiesArray) {
            return $scope.getNonDowntimeEntities(entitiesArray).slice(0, APP_CONST.MAX_ENTITIES_DISPLAYED);
        };

        /*
         * Returns true/false, depending on whether an alert's non-downtime entities list had to be truncated
         */
        $scope.nonDowntimeEntitiesAreTruncated = function(entitiesArray) {
            return $scope.getNonDowntimeEntities(entitiesArray).length > APP_CONST.MAX_ENTITIES_DISPLAYED;
        };

        /**
         * Returns the rest of an alert's non-downtime entities that where left out due to the MAX_ENTITIES_DISPLAYED limit
         */
        $scope.restOfNonDowntimeEntities = function(entitiesArray) {
            return $scope.getNonDowntimeEntities(entitiesArray).slice(APP_CONST.MAX_ENTITIES_DISPLAYED);
        };

        /**
         * Returns true if all entities of passed alert are failed due to check-level exception
         */
        $scope.hasAllEntitiesFailing = function(alertInstance) {
            if (!alertInstance || !alertInstance.entities) return false;
            return _.every(alertInstance.entities, function(val) {
                if (!val.result) return false;
                if (val.result.captures && val.result.captures["exception"]) return true;
                return val.result && val.result["exc"];
            });
        };

        /**
         * Returns true if all entities of passed alert are actively in downtime, in which case it will hide the alert entirely
         * Also updates property of # of entities of this alert that are *not* in downtime
         */
        $scope.hasAllEntitiesInDowntime = function(alertInstance) {
            return DowntimesService.hasAllEntitiesInDowntime(alertInstance);
        };

        /*
         * Returns true when none or some entities are in downtime, or false only when all entities are in downtime.
         * Used as a filter, it will hide alerts which have ALL entities in downtime only.
         */
        $scope.hasNotAllEntitiesInDowntime = function(alertInstance) {
            return !DowntimesService.hasAllEntitiesInDowntime(alertInstance);
        };

        // Returns a comma separated list of entity names from an alert entities object
        $scope.getEntityNames = function(entities) {
            return _.pluck(entities, 'entity').sort().join(',');
        };

        // Add a tag to the tags array
        $scope.addTag = function(tag) {
            if (typeof $scope.dashboardTags === 'undefined' || $scope.dashboardTags == null) {
                $scope.dashboardTags = [];
            }
            if ($scope.dashboardTags.indexOf(tag.text) === -1) {
                $scope.dashboardTags.push(tag.text);
                $scope.filter.tags = $scope.dashboardTags.toString();
            };
            $location.search('tags', $scope.filter.tags)
            $scope.showAllDashboardAlerts($scope.filter);
        };

        // Remove a tag from the tags array
        $scope.removeTag = function(tag) {
            $scope.dashboardTags = _.without($scope.dashboardTags, tag.id);
            $scope.filter.tags = $scope.dashboardTags.toString();
            if ($scope.dashboardTags.length === 0) {
                delete $scope.dashboardTags;
                $scope.filter.tags = 'none';
            };
            $location.search('tags', $scope.filter.tags)
            $scope.showAllDashboardAlerts($scope.filter);
        };

        // Get all tags for autocomplete
        CommunicationService.getAllTags().then(function(data) {
            $scope.allTags = data;
        });

        /*
         * Start periodic update of data
         */
        $scope.startDashboardRefresh = function() {
            MainAlertService.startDataRefresh('DashboardCtrl', _.bind($scope.refreshDashboardAlerts, this), APP_CONST.DASHBOARD_REFRESH_RATE, true);

        };

        // Start data refresh
        $scope.startDashboardRefresh();

        // Init page state depending on URL's query string components
        if (!_.isEmpty($location.search().as)) {
            $scope.alertSearch = $location.search().as;
        }

        $scope.$watch('alertSearch', function(newVal) {
            $location.search('as', _.isEmpty(newVal) ? null : newVal);
            localStorageService.set('returnTo', '/#' + $location.url());
        });
    }
]);
