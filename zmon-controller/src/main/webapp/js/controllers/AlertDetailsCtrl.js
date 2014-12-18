angular.module('zmon2App').controller('AlertDetailsCtrl', ['$scope', '$location', 'timespanFilter', '$routeParams', '$modal', 'MainAlertService', 'CommunicationService', 'DowntimesService', 'FeedbackMessageService', 'UserInfoService', 'APP_CONST',
    function($scope, $location, timespanFilter, $routeParams, $modal, MainAlertService, CommunicationService, DowntimesService, FeedbackMessageService, UserInfoService, APP_CONST) {
        $scope.AlertDetailsCtrl = this;

        // Set in parent scope which page is active for the menu styling
        $scope.$parent.activePage = 'alert-details'; // is not a menu option, but still set
        this.entitiesFilter = [];
        this.entitiesExcludeFilter = [];
        this.alertDefinitionId = $routeParams.alertId;
        this.alertDefinition = null;
        this.alertDetails = null; // all alerts (active + currently in downtime)
        this.activeAlerts = null; // 1st tab, 1st button filter content with alerts currently active
        this.alertsInDowntime = null; // 1st tab, 2nd button filter content with alerts currently in downtime
        this.checkResults = null; // 1st tab, 3rd button filter content with OKs [checks results i.e. w/o alert]
        this.allAlertsAndChecks = null; // a concatenation of the (non-null) arrays activeAlerts, alertsInDowntime and checkResults
        this.allDowntimes = null; // 2nd tab content with all downtimes (for alerts + OK's, current and future)
        this.allHistory = null; // 3rd tab content with all history entries

        this.showActiveAlerts = true; // 1st tab, 1st button
        this.showAlertsInDowntime = false; // 1st tab, 2nd button
        this.showCheckResults = false; // 1st tab, 3rd button

        // Total number of alerts/checksResults visible on screen (used by alert-details-infinit-scroll directive)
        this.infScrollNumAlertsVisible = APP_CONST.INFINITE_SCROLL_VISIBLE_ENTITIES_INCREMENT;
        // Total number of downtimes visible on screen
        this.infScrollNumDowntimesVisible = APP_CONST.INFINITE_SCROLL_VISIBLE_ENTITIES_INCREMENT;
        this.checkDefinition = null;
        this.addDowntimeEntities = [];
        this.deleteDowntimeUUIDs = [];
        // History button active
        this.activeHistoryButton = {
            "1": false,
            "7": false,
            "14": false,
            "-1": false
        };
        this.historyFromInEpochSeconds = null;
        this.currentDate = new Date();

        this.alertComments = [];

        this.alertJson = '';

        this.userInfo = UserInfoService.get();

        // Querystring is '?downtimes' when user comes from dashboard clicking on the flag icon of an alert to see its downtimes
        if ($location.search().downtimes) {
            this.showAlertsInDowntime = true;
        }

        $scope.$watch('[AlertDetailsCtrl.activeAlerts, AlertDetailsCtrl.alertsInDowntime, AlertDetailsCtrl.checkResults]', function() {
            $scope.AlertDetailsCtrl.allAlertsAndChecks = _.foldl([$scope.AlertDetailsCtrl.activeAlerts, $scope.AlertDetailsCtrl.alertsInDowntime, $scope.AlertDetailsCtrl.checkResults], function(result, nextDataArray) {
                if (nextDataArray && nextDataArray.length !== 0) {
                    return result.concat(nextDataArray);
                }
                return result;
            }, []);
        }, true);

        this.timeAgo = function(epochPastTs) {
            var timeIntervalSinceLastUpdate = MainAlertService.millisecondsApart(epochPastTs, MainAlertService.getLastUpdate());
            return timespanFilter(timeIntervalSinceLastUpdate);
        };

        this.refreshAlertDetails = function() {
            var now = new Date().getTime() / 1000;
            CommunicationService.getAlertDefinition(this.alertDefinitionId).then(function(response) {
                    $scope.AlertDetailsCtrl.alertDefinition = response;
                    $scope.AlertDetailsCtrl.currentDate = new Date();

                    // Fetch the information needed to fill the "Details" panel for both ACTIVE & INACTIVE alerts
                    CommunicationService.getCheckDefinition($scope.AlertDetailsCtrl.alertDefinition.check_definition_id).then(
                        function(response) {
                            $scope.AlertDetailsCtrl.checkDefinition = response;
                            $scope.AlertDetailsCtrl.entitiesFilter = [];
                            $scope.AlertDetailsCtrl.entitiesExcludeFilter = [];

                            // Multiply and merge check entities filter with alert entities filter.
                            if (_.size($scope.AlertDetailsCtrl.checkDefinition.entities) < 1) {
                                $scope.AlertDetailsCtrl.entitiesFilter = $scope.AlertDetailsCtrl.alertDefinition.entities;
                            } else if (_.size($scope.AlertDetailsCtrl.alertDefinition.entities) < 1) {
                                $scope.AlertDetailsCtrl.entitiesFilter = $scope.AlertDetailsCtrl.checkDefinition.entities;
                            } else {
                                _.each($scope.AlertDetailsCtrl.checkDefinition.entities, function (cEntity) {
                                    _.each($scope.AlertDetailsCtrl.alertDefinition.entities, function (aEntity) {
                                        var mergedEntity = _.extend({}, cEntity, aEntity);
                                        $scope.AlertDetailsCtrl.entitiesFilter.push(mergedEntity);
                                    });
                                });
                            }

                            // Remove entity filter duplicates!
                            $scope.AlertDetailsCtrl.entitiesFilter = _.uniq($scope.AlertDetailsCtrl.entitiesFilter, false, function(eFilter) {
                                return JSON.stringify(eFilter, null, 0);
                            });

                            // Remove entity filters with no "type".
                            $scope.AlertDetailsCtrl.entitiesFilter = _.reject($scope.AlertDetailsCtrl.entitiesFilter, function(eFilter) {
                                return (eFilter.type === undefined || eFilter.type == null || eFilter.type == "");
                            });

                            // Multiply and merge check entities EXCLUDE filter with alert entities EXCLUDE filter.
                            if (_.size($scope.AlertDetailsCtrl.checkDefinition.entities_exclude) < 1) {
                                $scope.AlertDetailsCtrl.entitiesExcludeFilter = $scope.AlertDetailsCtrl.alertDefinition.entities_exclude;
                            } else if (_.size($scope.AlertDetailsCtrl.alertDefinition.entities_exclude) < 1) {
                                $scope.AlertDetailsCtrl.entitiesExcludeFilter = $scope.AlertDetailsCtrl.checkDefinition.entities_exclude;
                            } else {
                                _.each($scope.AlertDetailsCtrl.checkDefinition.entities_exclude, function (cEntity) {
                                    _.each($scope.AlertDetailsCtrl.alertDefinition.entities_exclude, function (aEntity) {
                                        var mergedEntity = _.extend({}, cEntity, aEntity);
                                        $scope.AlertDetailsCtrl.entitiesExcludeFilter.push(mergedEntity);
                                    });
                                });
                            }

                            // Remove entity EXCLUDE filter duplicates!
                            $scope.AlertDetailsCtrl.entitiesExcludeFilter = _.uniq($scope.AlertDetailsCtrl.entitiesExcludeFilter, false, function(eFilter) {
                                return JSON.stringify(eFilter, null, 0);
                            });

                            // Remove entity EXCLUDE filters with no "type".
                            $scope.AlertDetailsCtrl.entitiesExcludeFilter = _.reject($scope.AlertDetailsCtrl.entitiesExcludeFilter, function(eFilter) {
                                return (eFilter.type === undefined || eFilter.type == null || eFilter.type == "");
                            });

                            // Get any children alerts that inherit from this alert
                            CommunicationService.getAlertDefinitionChildren($scope.AlertDetailsCtrl.alertDefinition.id).then(function(response) {
                                $scope.AlertDetailsCtrl.alertDefinitionChildren = response;
                            });

                            // Get Parent Alert Definition if a paret_id is preset
                            if ($scope.AlertDetailsCtrl.alertDefinition.parent_id) {
                                CommunicationService.getAlertDefinition($scope.AlertDetailsCtrl.alertDefinition.parent_id).then(function(response) {
                                    $scope.AlertDetailsCtrl.parentAlertDefinition = response;
                                });
                            }

                            if ($scope.AlertDetailsCtrl.alertDefinition.status === 'ACTIVE') {
                                CommunicationService.getAlertDetails($scope.AlertDetailsCtrl.alertDefinitionId).then(function(response) {
                                    $scope.AlertDetailsCtrl.alertDetails = response;
                                    // TBD: decide whether we want to reset the number of displayed entities on each refresh
                                    // or whether we want to keep the extended # displayed on previous refresh (the only way to reset back is by page refresh)
                                    // $scope.AlertDetailsCtrl.infScrollNumAlertsVisible = APP_CONST.INFINITE_SCROLL_VISIBLE_ENTITIES_INCREMENT;

                                    // Split into 2 sets: active alerts and alerts currently in downtime additionally flagging each item accordingly
                                    // so we can discriminate them in the allAlertAndChecks array
                                    $scope.AlertDetailsCtrl.activeAlerts = [];
                                    $scope.AlertDetailsCtrl.alertsInDowntime = [];

                                    _.each($scope.AlertDetailsCtrl.alertDetails.entities, function(nextAlert) {
                                        if (nextAlert.result.downtimes && nextAlert.result.downtimes.length) {
                                            // Add it to alertsInDowntime if any of its downtimes is active now; otherwise add it to activeAlerts
                                            if (DowntimesService.isAnyDowntimeNow(nextAlert.result.downtimes)) {
                                                nextAlert.isAlertInDowntime = true;
                                                $scope.AlertDetailsCtrl.alertsInDowntime.push(nextAlert);
                                            } else {
                                                nextAlert.isActiveAlert = true;
                                                $scope.AlertDetailsCtrl.activeAlerts.push(nextAlert);
                                            }
                                        } else {
                                            // alert has no downtimes; by definition goes to activeAlerts
                                            nextAlert.isActiveAlert = true;
                                            $scope.AlertDetailsCtrl.activeAlerts.push(nextAlert);
                                        }
                                    });

                                    $scope.namesOfEntitiesWithAlert = _.foldl($scope.AlertDetailsCtrl.alertDetails.entities, function(prev, curr) {
                                        prev[curr.entity] = true;
                                        return prev;
                                    }, {});

                                    CommunicationService.getCheckResultsForAlert($scope.AlertDetailsCtrl.alertDefinitionId, 1).then(
                                        function(response) {
                                            $scope.AlertDetailsCtrl.checkResults = _.map(_.filter(response, function(entityRes) {
                                                return !(entityRes.entity in $scope.namesOfEntitiesWithAlert);
                                            }), function(entityRes) {
                                                return {
                                                    'entity': entityRes.entity,
                                                    'result': entityRes.results[0],
                                                    'isCheckResult': true
                                                };
                                            });
                                        }

                                    );

                                    CommunicationService.getDowntimes($scope.AlertDetailsCtrl.alertDefinitionId).then(
                                        function(response) {
                                            $scope.AlertDetailsCtrl.allDowntimes = response;
                                        }
                                    );
                                });
                            }

                            // AlertDefinition, checkDefinition and entities filters are set. A link to TrialRun can
                            // be now generated and set on $scope.alertJson.
                            setLinkToTrialRun();
                        }
                    );
                }

            );
        };

        var setLinkToTrialRun = function () {
            var params = {
                name: $scope.AlertDetailsCtrl.alertDefinition.name,
                description: $scope.AlertDetailsCtrl.alertDefinition.description,
                check_command: $scope.AlertDetailsCtrl.checkDefinition.command,
                alert_condition: $scope.AlertDetailsCtrl.alertDefinition.condition,
                entities: $scope.AlertDetailsCtrl.entitiesFilter,
                entities_exclude: $scope.AlertDetailsCtrl.entitiesExcludeFilter,
                interval: $scope.AlertDetailsCtrl.checkDefinition.interval,
                period: $scope.AlertDetailsCtrl.alertDefinition.period,
                parameters: $scope.AlertDetailsCtrl.alertDefinition.parameters || []
            }
            $scope.AlertDetailsCtrl.alertJson = window.encodeURIComponent(JSON.stringify(params));
        };

        this.showDeleteAlertDefinitionModal = function() {

            // Delete alert definition modal
            var deleteAlertDefinitionModalInstance = $modal.open({
                templateUrl: '/templates/deleteAlertDefinitionModal.html',
                controller: deleteAlertDefinitionModalCtrl,
                backdrop: false,
                resolve: {
                    alertDefinition: function() {
                        return $scope.AlertDetailsCtrl.alertDefinition;
                    }
                }
            });

            deleteAlertDefinitionModalInstance.result.then(
                function() {
                    CommunicationService.deleteAlertDefinition($scope.AlertDetailsCtrl.alertDefinition.id).then(function() {
                        $location.path('/alert-definitions');
                    });
                });
        };


        var deleteAlertDefinitionModalCtrl = function($scope, $modalInstance, alertDefinition) {

            $scope.alertDefinition = alertDefinition;

            $scope.delete = function() {
                $modalInstance.close();
            };

            $scope.cancel = function() {
                $modalInstance.dismiss();
            };
        };

        // Downtime modal window's controller
        var downtimeModalCtrl = function($scope, $modalInstance, downtimeAlertId, downtimeEntities) {
            $scope.downtimeAlertId = downtimeAlertId;
            $scope.downtimeEntities = downtimeEntities;
            $scope.isDurationTabActive = true;
            $scope.minDate = new Date();
            $scope.maxDate = new Date($scope.minDate.getFullYear() + 1, $scope.minDate.getMonth(), $scope.minDate.getDate() - 1);
            $scope.dateFormat = 'dd-MMMM-yyyy';
            $scope.dateOptions = {
                'year-format': "'yy'",
                'starting-day': 1,
                'show-weeks': true
            };
            $scope.models = {
                // Tab 1: downtime duration starting now
                downtimeDuration: new Date(2013, 0, 0, 0, 0), // using Date object, but will only be using the HH:MM part as duration
                downStartDate: new Date(),
                downStartTime: new Date(),
                downEndDate: new Date(),
                downEndTime: new Date(new Date().getTime() + 30 * 60 * 1000), // 30' in the future from now
                downtimeComment: null,
                startDatepickerOpened: false,
                endDatepickerOpened: false
            };

            $scope.setDurationTabActive = function(isDurationTabActive) {
                $scope.isDurationTabActive = isDurationTabActive;
            };

            $scope.ok = function() {
                // Depending on which tab was active, we return corresponding data
                if ($scope.isDurationTabActive) {

                    $modalInstance.close({
                        "downStartTime": new Date(),
                        "downEndTime": $scope.calcDowntimeEndtime(),
                        "comment": $scope.models.downtimeComment
                    });
                } else {
                    var downStartTime = new Date($scope.models.downStartDate.getFullYear(), $scope.models.downStartDate.getMonth(), $scope.models.downStartDate.getDate(), $scope.models.downStartTime.getHours(), $scope.models.downStartTime.getMinutes());
                    var downEndTime = new Date($scope.models.downEndDate.getFullYear(), $scope.models.downEndDate.getMonth(), $scope.models.downEndDate.getDate(), $scope.models.downEndTime.getHours(), $scope.models.downEndTime.getMinutes());
                    // Check end time is after start time
                    if (downStartTime.getTime() > downEndTime.getTime()) {
                        FeedbackMessageService.showErrorMessage('Start date must precede end date!');
                    } else {
                        $modalInstance.close({
                            "downStartTime": downStartTime,
                            "downEndTime": downEndTime,
                            "comment": $scope.models.downtimeComment
                        });
                    }
                }
            };

            $scope.openDatepicker = function($event, which) {
                $event.preventDefault();
                $event.stopPropagation();
                if (which === 'start') {
                    $scope.models.startDatepickerOpened = !$scope.models.startDatepickerOpened;
                    $scope.models.endDatepickerOpened = false;
                } else if (which === 'end') {
                    $scope.models.endDatepickerOpened = !$scope.models.endDatepickerOpened;
                    $scope.models.startDatepickerOpened = false;
                }
            };

            // Applicable only for "Duration" type downtimes
            $scope.calcDowntimeEndtime = function() {
                var durationInMs = $scope.models.downtimeDuration.getHours() * 3600000 + $scope.models.downtimeDuration.getMinutes() * 60000;
                var nowPlusDuration = new Date(new Date().getTime() + durationInMs);
                return nowPlusDuration;
            };

            $scope.cancel = function() {
                $modalInstance.dismiss();
            };

            /**
             * When user clicks the [x] of an entity in the modal entity list to exclude it from the downtime
             */
            $scope.removeEntity = function(exclEntity) {
                $scope.downtimeEntities.splice($scope.downtimeEntities.indexOf(exclEntity), 1);
                if ($scope.downtimeEntities.length === 0) {
                    $scope.cancel();
                }
            };
        };

        this.showDowntimeModal = function(alertId) {
            var downtimeModalInstance = $modal.open({
                templateUrl: '/templates/downtimeModal.html',
                controller: downtimeModalCtrl,
                backdrop: false,
                resolve: {
                    downtimeAlertId: function() {
                        return alertId;
                    },
                    downtimeEntities: function() {
                        return $scope.AlertDetailsCtrl.addDowntimeEntities;
                    }
                }
            });

            downtimeModalInstance.result.then(
                // Modal's OK pressed; returned downtimeData has format: {"downStartTime": <date Object>, "downEndTime": <date Object>, "comment": <string>}
                // POST a new downtime
                function(downtimeData) {
                    // In this case the entity-alert relationship is N-1
                    var entitiesPerAlert = [{
                        "alert_definition_id": $scope.AlertDetailsCtrl.alertDefinitionId,
                        "entity_ids": $scope.AlertDetailsCtrl.addDowntimeEntities
                    }];
                    CommunicationService.scheduleDowntime(downtimeData.comment, downtimeData.downStartTime, downtimeData.downEndTime, entitiesPerAlert).then(
                        function(downtimeUUIDs) {
                            FeedbackMessageService.showSuccessMessage('Success setting ' + $scope.AlertDetailsCtrl.addDowntimeEntities.length + ($scope.AlertDetailsCtrl.addDowntimeEntities.length > 1 ? ' downtimes' : ' downtime'));
                            $scope.AlertDetailsCtrl.addDowntimeEntities = [];
                        }

                    );
                });
        };

        /**
         * Delete multiple downtimes (Downtimes tab)
         */
        this.deleteMultiDowntimes = function() {
            var that = this;
            CommunicationService.deleteDowntime(this.deleteDowntimeUUIDs).then(
                function(data) {
                    FeedbackMessageService.showSuccessMessage('Downtimes deleted', 3000);
                    that.deleteDowntimeUUIDs = [];
                }, function(httpStatus) {
                    that.deleteDowntimeUUIDs = [];
                }
            );
        };

        /**
         * Returns t/f (Downtimes tab). Again displayed don't mean visible.
         */
        this.areAllDowntimesChecked = function() {
            var totalDisplayedDowntimes = 0;
            if (this.allDowntimes && this.allDowntimes.length) {
                totalDisplayedDowntimes = this.allDowntimes.length;
                if (this.deleteDowntimeUUIDs.length === totalDisplayedDowntimes) {
                    return true;
                }
            }
            return false;
        };

        /**
         * Triggered when individual delete downtime checkbox is checked/unchecked (Downtimes tab)
         */
        this.toggleSingleDeleteDowntime = function(downtimeUUID) {
            var idx = this.deleteDowntimeUUIDs.indexOf(downtimeUUID);
            if (idx > -1) {
                // It's already in deleteDowntimeUUIDs; remove it
                this.deleteDowntimeUUIDs.splice(idx, 1);
            } else {
                // Not in deleteDowntimeUUIDs; add it
                this.deleteDowntimeUUIDs.push(downtimeUUID);
            }
        };

        /**
         * (Downtimes tab) Triggered when overall delete downtime checkbox of header is checked/unchecked to set/unset all delete downtime checkboxes
         */
        this.toggleAllDeleteDowntimes = function() {
            if (!this.areAllDowntimesChecked()) {
                this.deleteDowntimeUUIDs = [];
                // Delete downtimes checkboxes are partially checked; proceed to check all of them
                _.each(_.pluck(this.allDowntimes, 'id'), function(nextUUID) {
                    $scope.AlertDetailsCtrl.deleteDowntimeUUIDs.push(nextUUID);
                });
            } else {
                this.deleteDowntimeUUIDs = [];
            }
        };

        /**
         * (Alerts tab) Triggered when individual entity checkbox for downtime is checked/unchecked
         */
        this.toggleEntityAddDowntime = function(entityId) {
            var idx = this.addDowntimeEntities.indexOf(entityId);
            if (idx > -1) {
                // It's already in addDowntimeEntities; remove it
                this.addDowntimeEntities.splice(idx, 1);
            } else {
                // Not in addDowntimeEntities; add it
                this.addDowntimeEntities.push(entityId);
            }
        };

        /**
         * (Alerts tab) Triggered when overall downtime checkbox of header is checked/unchecked to set/unset all entity checkboxes to add downtime
         * What is included by "all", depends on which groups are selected to be displayed at the moment
         */
        this.toggleAllEntitiesAddDowntime = function() {
            if (!this.areAllDisplayedAlertsChecked()) {
                this.addDowntimeEntities = [];
                // Check all
                if (this.showActiveAlerts) {
                    _.each(_.pluck(this.activeAlerts, 'entity'), function(entity) {
                        $scope.AlertDetailsCtrl.addDowntimeEntities.push(entity);
                    });
                }
                if (this.showAlertsInDowntime) {
                    _.each(_.pluck(this.alertsInDowntime, 'entity'), function(entity) {
                        $scope.AlertDetailsCtrl.addDowntimeEntities.push(entity);
                    });
                }
                if (this.showCheckResults) {
                    _.each(_.pluck(this.checkResults, 'entity'), function(entity) {
                        $scope.AlertDetailsCtrl.addDowntimeEntities.push(entity);
                    });
                }
            } else {
                // Uncheck all
                this.addDowntimeEntities = [];
            }
        };

        /**
         * Trivial function, but necessary because the directive for infinite-scroll requires the attribute "getTotalNumDisplayedItems" to be a function ref
         * Return # of items to be displayed and not necessarilly visible on screen
         */
        this.getTotalNumDowntimes = function() {
            return this.allDowntimes ? this.allDowntimes.length : 0;
        };

        /**
         * (Alerts tab) Returns true if all alerts from groups selected to be displayed are checked
         */
        this.areAllDisplayedAlertsChecked = function() {
            return this.addDowntimeEntities.length === this.getTotalNumDisplayedAlerts();
        };

        /**
         * Returns number of entities from groups (activeAlerts, alertsInDowntime, checkResults) selected to be displayed
         * Displayed doesn't mean immediately visible on screen due to infinite scroll; it means belonging to a group that is selected to be displayed and not hidden
         */
        this.getTotalNumDisplayedAlerts = function() {
            var numDisplayed = 0;
            if (this.showActiveAlerts && this.activeAlerts) {
                numDisplayed += this.activeAlerts.length;
            }
            if (this.showAlertsInDowntime && this.alertsInDowntime) {
                numDisplayed += this.alertsInDowntime.length;
            }
            if (this.showCheckResults && this.checkResults) {
                numDisplayed += this.checkResults.length;
            }
            return numDisplayed;
        };

        /**
         * Toggles the state of showActiveAlerts, showAlertsInDowntime and showCheckResults. Passed param defines which one gets toggled
         * When a group is deselected from being displayed, any references to its entities are remove from addDowntimeEntities
         * Passed param is 'activeAlerts', 'alertsInDowntime' or 'checkResults'
         */
        this.toggleShowEntities = function(entityType) {
            if (entityType === 'activeAlerts') {
                this.showActiveAlerts = !this.showActiveAlerts;
                if (this.showActiveAlerts === false) {
                    // Active alerts no longer displayed; remove from addDowntimeEntities any references to them
                    _.each(_.pluck(this.activeAlerts, 'entity'), function(entity) {
                        var idx = $scope.AlertDetailsCtrl.addDowntimeEntities.indexOf(entity);
                        if (idx > -1) {
                            $scope.AlertDetailsCtrl.addDowntimeEntities.splice(idx, 1);
                        }
                    });
                }
            } else if (entityType === 'alertsInDowntime') {
                this.showAlertsInDowntime = !this.showAlertsInDowntime;
                if (this.showAlertsInDowntime === false) {
                    // Alerts in downtime no longer displayed; remove from addDowntimeEntities any references to them
                    _.each(_.pluck(this.alertsInDowntime, 'entity'), function(entity) {
                        var idx = $scope.AlertDetailsCtrl.addDowntimeEntities.indexOf(entity);
                        if (idx > -1) {
                            $scope.AlertDetailsCtrl.addDowntimeEntities.splice(idx, 1);
                        }
                    });
                }
            } else {
                this.showCheckResults = !this.showCheckResults;
                if (this.showCheckResults === false) {
                    // Check results no longer displayed; remove from addDowntimeEntities any references to them
                    _.each(_.pluck(this.checkResults, 'entity'), function(entity) {
                        var idx = $scope.AlertDetailsCtrl.addDowntimeEntities.indexOf(entity);
                        if (idx > -1) {
                            $scope.AlertDetailsCtrl.addDowntimeEntities.splice(idx, 1);
                        }
                    });
                }
            }
        };

        this.startAlertDetailsRefresh = function() {
            MainAlertService.startDataRefresh('AlertDetailsCtrl', _.bind(this.refreshAlertDetails, this), APP_CONST.ALERT_DETAILS_REFRESH_RATE, true);
        };


        this.getComments = function(alertId, limit, offset, cb) {
            CommunicationService.getAlertComments(alertId, limit, offset).then(function(comments) {
                if (cb) cb(comments);
            });
        };

        this.saveComment = function(data, cb) {
            CommunicationService.insertAlertComment(data).then(function(comment) {
                if (cb) cb(comment);
            });
        };

        this.deleteComment = function(commentId, cb) {
            CommunicationService.deleteAlertComment(commentId).then(function(status) {
                if (cb) cb(commentId);
            });
        };

        this.getComments(this.alertDefinitionId, 6, 0, function(comments) {
            $scope.AlertDetailsCtrl.alertComments = comments;
        });

        /**
         * Refreshes history data with lastNDays worth of events; the range is [now - lastNDays, now]
         * Stores fetched data in allHistory array
         */
        this.fetchHistoryLastNDays = function(lastNDays) {
            // Set corresponding flags for highlighting of history buttons accordingly
            _.each(this.activeHistoryButton, function(nextVal, nextKey) {
                if (lastNDays === parseInt(nextKey, 10)) {
                    $scope.AlertDetailsCtrl.activeHistoryButton[nextKey] = true;
                } else {
                    $scope.AlertDetailsCtrl.activeHistoryButton[nextKey] = false;
                }
            });

            // Note: we maintain the from timestamp in seconds but javascript time calculations are done in milliseconds
            this.historyFromInEpochSeconds = parseInt(((new Date().getTime()) - (lastNDays * 24 * 60 * 60 * 1000)) / 1000, 10);
            CommunicationService.getAlertHistory(this.alertDefinitionId, this.historyFromInEpochSeconds).then(
                function(response) {
                    $scope.AlertDetailsCtrl.allHistory = response;
                }
            );
        };

        /**
         * Fetches 1 week's worth of data; the range is [historyFromInEpochSeconds - 7 days, historyFromInEpochSeconds, ]
         * Concats fetched data to the existing allHistory array
         */
        this.fetchOneMoreWeekOfHistory = function() {
            // Set corresponding flags for highlighting of history buttons accordingly
            _.each(this.activeHistoryButton, function(nextVal, nextKey) {
                $scope.AlertDetailsCtrl.activeHistoryButton[nextKey] = false;
            });
            this.activeHistoryButton['-1'] = true;
            // Decrement current historyFromInEpochSeconds by 1 more week (here all times are in seconds)
            var historyToInEpochSeconds = this.historyFromInEpochSeconds;
            this.historyFromInEpochSeconds = this.historyFromInEpochSeconds - (7 * 24 * 60 * 60);
            CommunicationService.getAlertHistory(this.alertDefinitionId, this.historyFromInEpochSeconds, historyToInEpochSeconds).then(
                function(response) {
                    // Append the additional week's
                    $scope.AlertDetailsCtrl.allHistory = $scope.AlertDetailsCtrl.allHistory.concat(response);
                }
            );
        };

        // Force evaluation of alert definition
        this.forceAlertEvaluation = function() {
            CommunicationService.forceAlertEvaluation($scope.AlertDetailsCtrl.alertDefinitionId)
                .then(function() {;
                    FeedbackMessageService.showSuccessMessage('Evaluation of alert successfully forced...');
                }
            );
        };

        /**
         * Returns the content to be displayed for this type of history entry
         * "historyType" is one of:   ALERT_{STARTED|ENDED}, ALERT_ENTITY_{STARTED|ENDED}, DOWNTIME_{STARTED|ENDED}, DOWNTIME_SCHEDULED, TRIAL_RUN_SCHEDULED,
         *                          NEW_ALERT_COMMENT, CHECK_DEFINITION_{CREATED|UPDATED}, ALERT_DEFINITION_{CREATED|UPDATED}
         * "aattributes" is
         */
        this.getHistoryContent = function(historyType, attributes) {
            switch (historyType) {
                case 'ALERT_STARTED':
                case 'ALERT_ENDED':
                case 'ALERT_ENTITY_STARTED':
                case 'ALERT_ENTITY_ENDED':
                    return "";
                case 'DOWNTIME_STARTED':
                case 'DOWNTIME_ENDED':
                case 'DOWNTIME_SCHEDULED':
                case 'DOWNTIME_REMOVED':
                    return attributes.comment;
                case 'ALERT_COMMENT_CREATED':
                case 'ALERT_COMMENT_REMOVED':
                    return attributes.comment;
                case 'CHECK_DEFINITION_CREATED':
                case 'CHECK_DEFINITION_UPDATED':
                    return JSON.stringify(attributes);
                case 'ALERT_DEFINITION_CREATED':
                case 'ALERT_DEFINITION_UPDATED':
                    return JSON.stringify(attributes);
                default:
                    return "N/A";
            }
        };

        this.HSLaFromHistoryEventTypeId = function(eventTypeId) {
            return ((eventTypeId * 6151 % 1000 / 1000.0) * 360);
        };

        this.startAlertDetailsRefresh();
    }
]);
