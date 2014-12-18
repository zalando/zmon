angular.module('zmon2App').directive('networkmap', [ '$compile', '$http', '$templateCache', '$filter', function($compile, $http, $templateCache, $filter) {
    var getTemplate = function(name) {
        var baseUrl = '/templates/networkMap/';
        var templateUrl = baseUrl + name + '.html';
        return $http.get(templateUrl, { cache: $templateCache });
    };
    return {
        restrict: 'E',
        scope: {
            title: '@title',
            data: '=data',
            options: '=options'
        },
        templateUrl: '/templates/networkMap/networkMap.html',
        replace: true,
        link: function(scope, elem) {
            // These are used to avoid multiple checks at the same time, for performance reasons.
            var watchInterval = 2000;
            var lastWatchTime = 0;

            var divAlertIds;
            var divAlerts = $(elem).find("div");

            scope.activeAlertsInfo = {};

            // It is possible to override alerts for each shape with options, based on the shape's class name.
            // For example having {"options": {"shapeAlerts": {"country-uk": 1,4,18}}} will set alerts 1, 4 and 18
            // for the UK shape.
            if (scope.options && scope.options.shapeAlerts) {
                _.each(scope.options.shapeAlerts, function(key, value) {
                    $(elem).find("." + key).data("alertids", value);
                });
            }

            // Load custom template only if specified!
            if (scope.options && scope.options.template) {
                var loader = getTemplate(scope.options.template);
                var promise = loader.success(function(html) {
                    elem.html(html);
                }).then(function(response) {
                    elem.replaceWith($compile(elem.html())(scope));
                });
            }

            // Check if list of all alertIds is set, otherwise set it by getting all "data-alertids" from
            // divs on the HTML.
            if (!scope.options.alertIds) {
                var allAlertIds = [];

                _.each(divAlerts, function(div) {
                    div = $(div);
                    divAlertIds = div.data("alertids");

                    // Check if alert IDs are specified for the current div.
                    // If data is "", make the item dark-gray.
                    if (divAlertIds != undefined && divAlertIds != null && divAlertIds != "") {
                        var currentAlertIds = divAlertIds.toString().split(",");

                        // Clear priority from list of alert IDs.
                        for (var a = 0; a < currentAlertIds.length; a++) {
                            currentAlertIds[a] = currentAlertIds[a].split(":")[0];
                        }

                        allAlertIds = allAlertIds.concat(currentAlertIds);
                    } else if (divAlertIds == "") {
                        div.addClass("no-ids");
                    }
                });

                scope.options.alertIds = allAlertIds;
            }

            scope.getTooltip = function(ids) {
                var hasAlert = false;
                var tooltipHtml = "<div class='app-status-tooltip'><div class='alerts'><h6>Active Alerts</h6>";

                _.each(ids, function(id) {
                    var alert = scope.activeAlertsInfo[id];
                    if (alert) {
                        hasAlert = true;
                        tooltipHtml += "<div>";
                        tooltipHtml += "<span class='alert-name'>";
                        tooltipHtml += "<a href='/#/alert-details/" + id + "' title='" + alert.name + "' target='_black'>" + alert.name;
                        tooltipHtml += "</a></span>";
                        tooltipHtml += "<span class='alert-time'>" + alert.time + "</span>";
                        tooltipHtml += "<span class='alert-team'>" + alert.team + "</span>";
                        tooltipHtml += "</div>";
                    }
                });

                tooltipHtml += '</div></div>';
                return hasAlert ? tooltipHtml : undefined;
            };

            // Dirty helper to remove all tooltips except the one for the selected element
            scope.hideTooltips = function($event) {
                var $el = $($event.target);
                var ucl = $el.parent("div[data-alertids]").siblings('.tooltip');
                var sib = $el.siblings('.tooltip');
                $('.tooltip').not($(ucl)).not($(sib)).remove();
            };

            // Watch data updates to rebind classes.
            scope.$watch("data", function(newData) {
                var now = new Date();

                scope.activeAlertsInfo = {};
                evalOldestStartTimes(newData);

                // Function was called recently? Abort.
                if (now.getTime() - lastWatchTime < watchInterval) {
                    return;
                }

                lastWatchTime = now.getTime();

                // Remove all critical alerts before proceeding.
                divAlerts.removeClass("priority-1 priority-2 priority-3");

                // Check all divs withing the view.
                _.each(divAlerts, function(div) {
                    div = $(div);
                    divAlertIds = div.data("alertids");

                    if (divAlertIds != undefined && divAlertIds != null && divAlertIds != "") {
                        var arrIds = div.data("alertids").toString().split(",");
                        var hasAlert = false;
                        var forcedPrio = 0;
                        var prio = 3;

                        _.each(arrIds, function(id) {
                            // User is specifying the alert priority manually.
                            if (id.indexOf(":") > 0) {
                                var arr = id.split(":");
                                id = arr[0];
                                forcedPrio = parseInt(arr[1]);
                            }

                            _.each(newData, function(alertData) {
                                if (alertData.alert_definition.id == id) {
                                    hasAlert = true;

                                    if (alertData.alert_definition.priority < prio) {
                                        prio = alertData.alert_definition.priority;
                                    }

                                    // Add alert info to dict of active alerts
                                    scope.activeAlertsInfo[id] = {
                                        name: alertData.alert_definition.name,
                                        team: alertData.alert_definition.team,
                                        time: $filter('timespan')(new Date(alertData.oldestStartTime)) || ''
                                    };
                                }
                            });
                        });

                        if (forcedPrio > 0) {
                            prio = forcedPrio;
                        }

                        if (hasAlert) {
                            div.addClass("priority-" + prio);
                        }
                    }
                });
            });

            var evalOldestStartTimes = function(allAlerts) {
                if (typeof allAlerts === 'undefined') return;
                allAlerts.forEach(function(nextAlert, idx, arr) {
                    // Get the oldest start_time out of all of the entities of this specific allert
                    var alertId = nextAlert.alert_definition.id;
                    // Add the oldest entity's start_time for current alert as property 'oldestStartTime' of the alert
                    _.extend(nextAlert, {
                        'oldestStartTime': _.min(_.pluck(_.pluck(nextAlert.entities, 'result'), 'start_time'))
                    });
                });
            };
        }
    };
}]);
