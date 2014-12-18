angular.module('zmon2App').factory('CommunicationService', ['$http', '$q', '$log', 'APP_CONST', 'PreconditionsService',
    function($http, $q, $log, APP_CONST, PreconditionsService) {
        var service = {},
            alertIdCache = {},
            alertNameCache = {};

        /*
         * Get all the alerts based on passed filter object (empty object to get everything).
         * Format of passed param object: {'team':'Platform/Software'}
         */
        service.getAllAlerts = function(filter) {
            var params = {};
            if (filter.team) {
                params.team = filter.team;
            }
            if (filter.tags) {
                params.tags = filter.tags;
            }
            return doHttpCall("GET", "rest/allAlerts", params);
        };

        /*
         * Get alerts by ID.
         */
        service.getAlertsById = function(ids) {
            if (!ids) {
                ids = "";
            } else if (_.isArray(ids)) {
                ids = ids.join(',');
            }
            var params = {
                id: ids
            };
            return doHttpCall("GET", "rest/alertsById", params);
        };

        service.getAlertDetails = function(alertId) {
            PreconditionsService.isNotEmpty(alertId);
            PreconditionsService.isNumber(alertId);
            var params = {
                "alert_id": alertId
            };
            return doHttpCall("GET", "rest/alertDetails", params);
        };

        /*
         * Returns check results for passed checkId with optional limitCount & entityId filter
         */
        service.getCheckResults = function(checkId, entityId, limitCount) {
            PreconditionsService.isNotEmpty(checkId);
            PreconditionsService.isNumber(checkId);
            var params = {
                "check_id": checkId
            };
            if (entityId) {
                PreconditionsService.isNumber(entityId);
                params.entity = entityId;
            }
            if (limitCount) {
                PreconditionsService.isNumber(limitCount);
                params.limit = limitCount;
            }
            return doHttpCall("GET", "rest/checkResults", params);
        };

        service.getCheckResultsForAlert = function(alertId, limitCount) {
            PreconditionsService.isNotEmpty(alertId);
            PreconditionsService.isNumber(alertId);
            var params = {
                "alert_id": alertId
            };
            if (limitCount) {
                PreconditionsService.isNumber(limitCount);
                params.limit = limitCount;
            }
            return doHttpCall("GET", "rest/checkAlertResults", params);
        };

        service.getCheckCharts = function(params) {
            PreconditionsService.isNotEmpty(params.check_id);
            PreconditionsService.isNumber(params.check_id);
            PreconditionsService.isNotEmpty(params.entity_id);
            PreconditionsService.isNotEmpty(params.start_date);
            PreconditionsService.isNumber(params.start_date);
            PreconditionsService.isNotEmpty(params.end_date);
            PreconditionsService.isNumber(params.end_date);
            PreconditionsService.isNotEmpty(params.aggregate);
            PreconditionsService.isNumber(params.aggregate);
            PreconditionsService.isNotEmpty(params.aggregate_unit);

            return doHttpCall("GET", "rest/retrieveCheckStatistics", params);
        };

        service.getKairosResults = function(options) {
            return doHttpCall("POST", "rest/kairosDBPost", options, null, null);
        };

        service.getAlertDefinitions = function(team) {
            var params = {};
            if (team) {
                params.team = team;
            }
            var postSuccessProcessing = function(data) {
                _.each(data, function(item) {
                    alertNameCache[item.name] = 1;
                    alertIdCache[item.id] = item.name;
                });
            };
            return doHttpCall("GET", "rest/alertDefinitions", params, null, postSuccessProcessing);
        };

        service.getAlertDefinition = function(id) {
            var params = {};
            if (id) {
                PreconditionsService.isNumber(id);
                params.id = id;
            }
            var postSuccessProcessing = function(data) {
                alertNameCache[data.name] = 1;
                alertIdCache[data.id] = data.name;
            };
            return doHttpCall("GET", "rest/alertDefinition", params, null, postSuccessProcessing);
        };

        service.getAlertDefinitionNode = function(id) {
            var params = {};
            if (id) {
                PreconditionsService.isNumber(id);
                params.id = id;
            }
            var postSuccessProcessing = function(data) {
                alertNameCache[data.name] = 1;
                alertIdCache[data.id] = data.name;
            };
            return doHttpCall("GET", "rest/alertDefinitionNode", params, null, postSuccessProcessing);
        };

        service.getAlertDefinitionChildren = function(id) {
            var params = {};
            if (id) {
                PreconditionsService.isNumber(id);
                params.id = id;
            }
            return doHttpCall("GET", "rest/alertDefinitionChildren", params);
        };

        service.forceAlertEvaluation = function(id) {
            var params = {};
            if (id) {
                PreconditionsService.isNumber(id);
                params.alert_definition_id = id;
            }
            return doHttpCall("POST", "rest/forceAlertEvaluation", params);
        };

        service.getAllTeams = function() {
            return doHttpCall("GET", "rest/allTeams");
        };

        service.getAllTags = function() {
            var postSuccessProcessing = function(response) {
                var tags = [];
                _.each(response.sort(), function(t) {
                    tags.push({ 'id': t, 'text': t });
                });
                return tags;
            }
            return doHttpCall("GET", "rest/allTags", null, null, postSuccessProcessing);
        };

        service.getDashboard = function(id) {
            PreconditionsService.isNotEmpty(id);
            PreconditionsService.isNumber(id);
            var params = {
                "id": id
            };
            return doHttpCall("GET", "rest/dashboard", params);
        };

        service.getAllDashboards = function() {
            return doHttpCall("GET", "rest/allDashboards");
        };

        service.getCheckDefinitions = function(team) {
            var params = {};

            if (team) {
                params.team = team;
            }

            return doHttpCall("GET", "rest/checkDefinitions", params);
        };

        service.getCheckDefinition = function(id) {
            PreconditionsService.isNotEmpty(id);
            PreconditionsService.isNumber(id);
            var params = {
                "check_id": id
            };
            return doHttpCall("GET", "rest/checkDefinition", params);
        };

        service.getStatus = function() {
            return doHttpCall("GET", "rest/status");
        };

        service.updateAlertDefinition = function(def) {
            var deferred = $q.defer();
            if (def.id) {
                if (def.name != alertIdCache[def.id]) {
                    alertNameCache[def.name] = 1;
                    delete alertNameCache[alertIdCache[def.id]];
                }
            } else {
                alertNameCache[def.name] = 1;
            }

            $http({
                method: 'POST',
                url: 'rest/updateAlertDefinition',
                headers: {
                    'Content-Type': 'application/json'
                },
                data: def
            }).success(function(data, status, headers, config) {
                alertIdCache[data.id] = data.name;
                deferred.resolve(data);
            }).error(function(data, status, headers, config) {
                alertNameCache[alertIdCache[def.id]] = 1;
                delete alertNameCache[def.name];
                deferred.reject(status);
            });
            return deferred.promise;
        };

        service.deleteAlertDefinition = function(alertId) {
            PreconditionsService.isNotEmpty(alertId);
            PreconditionsService.isNumber(alertId);
            var params = {
                id: alertId
            };
            return doHttpCall('DELETE', 'rest/deleteAlertDefinition', params);
        };

        service.updateDashboard = function(dashboard) {
            PreconditionsService.isNotEmpty(dashboard);
            var headers = {
                'Content-Type': 'application/json'
            };
            return doHttpCall("POST", "rest/updateDashboard", dashboard, headers);
        };

        service.isValidAlertName = function(name) {
            return !(name in alertNameCache);
        };

        /*
         * Fetches downtimes for specific alert; if omitted, fetches all downtimes of all alerts
         */
        service.getDowntimes = function(alertDefId) {
            PreconditionsService.isNotEmpty(alertDefId);
            PreconditionsService.isNumber(alertDefId);
            var params = {
                "alert_definition_id": alertDefId
            };
            return doHttpCall("GET", "rest/downtimes", params);
        };

        /**
         * Generic downtime scheduler. The entitiesPerAlert is an array of objects each of which has format:
         *      {   "alert_definition": 1,
         *          "entity_ids": ["a", "b"]
         *      }
         */
        service.scheduleDowntime = function(comment, startTime, endTime, entitiesPerAlert) {
            PreconditionsService.isNotEmpty(comment);
            PreconditionsService.isNotEmpty(startTime);
            PreconditionsService.isDate(startTime);
            PreconditionsService.isNotEmpty(endTime);
            PreconditionsService.isDate(endTime);
            PreconditionsService.isNotEmpty(entitiesPerAlert);
            var postData = {
                "comment": comment,
                "start_time": parseInt(startTime.getTime() / 1000, 10), // convert to seconds
                "end_time": parseInt(endTime.getTime() / 1000, 10),
                "downtime_entities": entitiesPerAlert
            };
            var headers = {
                'Content-Type': 'application/json;charset=utf-8'
            };
            return doHttpCall("POST", "rest/scheduleDowntime", postData, headers);
        };

        /**
         * NOTE: we cannot use doHttpCall() because we cannot pass params through object
         * as we normally do because in this case all keys are the same ("downtime_id")
         */
        service.deleteDowntime = function(downtimeUUIDs) {
            PreconditionsService.isNotEmpty(downtimeUUIDs);
            var deferred = $q.defer();
            var deleteUrl = 'rest/deleteDowntimes?';
            _.each(downtimeUUIDs, function(nextUUID) {
                deleteUrl += '&downtime_id=' + nextUUID;
            });

            $http({
                method: 'DELETE',
                url: deleteUrl
            }).success(function(data, status, headers, config) {
                deferred.resolve(data);
            }).error(function(data, status, headers, config) {
                deferred.reject(status);
            });
            return deferred.promise;
        };

        /**
         * Reports services
         */

        service.getReports = function(params) {
            return doHttpCall("GET", "rest/historyReport", params);
        };

        service.initTrialRun = function(params) {
            PreconditionsService.isNotEmpty(params.alert_condition);
            PreconditionsService.isNotEmpty(params.check_command);
            PreconditionsService.isNotEmpty(params.name);
            var postData = params;
            var headers = {
                'Content-Type': 'application/json'
            };
            return doHttpCall("POST", "rest/scheduleTrialRun", postData, headers);
        };

        service.getTrialRunResult = function(trialRunId) {
            PreconditionsService.isNotEmpty(trialRunId);
            PreconditionsService.isNumber(trialRunId);
            var params = {
                "id": trialRunId
            };
            return doHttpCall("GET", "rest/trialRunResults", params);
        };

        service.insertAlertComment = function(params) {
            var postData = params;
            var headers = {
                'Content-Type': 'application/json'
            };
            return doHttpCall("POST", "rest/comment", postData, headers);
        };

        service.getAlertComments = function(alertId, limit, offset) {
            PreconditionsService.isNotEmpty(alertId);
            PreconditionsService.isNumber(alertId);
            PreconditionsService.isNotEmpty(limit);
            PreconditionsService.isNumber(limit);
            PreconditionsService.isNotEmpty(offset);
            PreconditionsService.isNumber(offset);
            var params = {
                "alert_definition_id": alertId,
                "limit": limit,
                "offset": offset
            };
            return doHttpCall("GET", "rest/comments", params);
        };

        service.deleteAlertComment = function(commentId) {
            PreconditionsService.isNotEmpty(commentId);
            PreconditionsService.isNumber(commentId);
            var params = {
                "id": commentId
            };
            return doHttpCall("DELETE", "rest/deleteComment", params);
        };

        service.getAlertHistory = function(alertId, fromEpoch, toEpoch, batchSize) {
            PreconditionsService.isNotEmpty(alertId);
            PreconditionsService.isNumber(alertId);
            var params = {
                "alert_definition_id": alertId
            };
            if (batchSize) {
                PreconditionsService.isNumber(batchSize);
                params.limit = batchSize;
            }
            if (fromEpoch) {
                PreconditionsService.isNumber(fromEpoch);
                params.from = fromEpoch;
            }
            if (toEpoch) {
                PreconditionsService.isNumber(toEpoch);
                params.to = toEpoch;
            }
            return doHttpCall("GET", "rest/alertHistory", params);
        };

        /*
         * Fetches check or alert definition history of changes
         */
        service.getHistoryChanges = function(params) {
            PreconditionsService.isNotEmpty(params.alert_definition_id);
            PreconditionsService.isNumber(params.alert_definition_id);
            PreconditionsService.isNotEmpty(params.limit);
            PreconditionsService.isNumber(params.limit);
            PreconditionsService.isNotEmpty(params.from);
            PreconditionsService.isNumber(params.from);
            url = params.check_definition_id ? 'rest/checkDefinitionHistory' : 'rest/alertDefinitionHistory';
            return doHttpCall("GET", url, params);
        };

        service.getEntityProperties = function() {
            return doHttpCall("GET", 'rest/entityProperties');
        };

        /**
         * Covers all http methods; the arg postSuccessProcessing is a function which will receive as single argument
         * the upon success response data in case it needs to go through additional processing before resolving the promise
         */
        function doHttpCall(httpMethod, endpoint, payload, extraHeaders, postSuccessProcessing) {
            PreconditionsService.isNotEmpty(httpMethod);
            PreconditionsService.isHTTPMethod(httpMethod);
            PreconditionsService.isNotEmpty(endpoint);
            /**
             * Converts a simple object (flat key/value pairs; no nested objects|arrays) into a query string
             * Used only for GETs/DELETEs; POST payload is sent as is
             */
            function objectToQueryString(obj) {
                var str = [];
                angular.forEach(obj, function(nextValue, nextKey) {
                    str.push(encodeURIComponent(nextKey) + "=" + encodeURIComponent(nextValue));
                });
                return str.join("&");
            }
            var deferred = $q.defer();

            // console.log(' method: ', httpMethod, ' / endpoint: ', endpoint, ' / payload: ', objectToQueryString(payload));
            var httpConfig = {
                method: httpMethod
            };
            if (httpMethod === "POST") {
                httpConfig.url = endpoint;
                httpConfig.data = payload;
            } else {
                // GETs & DELETEs
                httpConfig.url = endpoint + "?" + objectToQueryString(payload);
            }

            if (extraHeaders) {
                httpConfig.headers = extraHeaders;
            }

            $http(httpConfig).success(function(response, status, headers, config) {
                if (postSuccessProcessing) {
                    var result = postSuccessProcessing(response);
                    response = result ? result : response;
                }
                deferred.resolve(response);
            }).error(function(response, status, headers, config) {
                deferred.reject(status);
            });

            return deferred.promise;
        }

        return service;
    }
]);
