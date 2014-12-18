angular.module('zmon2App').controller('ReportsCtrl', ['$scope', '$routeParams', '$location', '$modal', 'MainAlertService', 'CommunicationService', 'UserInfoService', 'FeedbackMessageService', 'LoadingIndicatorService', 'APP_CONST', 'localStorageService',
    function($scope, $routeParams, $location, $modal, MainAlertService, CommunicationService, UserInfoService, FeedbackMessageService, LoadingIndicatorService, APP_CONST, localStorageService) {

        $scope.$parent.activePage = 'reports';

        // Get report id from url parameters
        $scope.reportId = $routeParams.reportId;

        // Get all teams from backend to generate filter by team menu.
        CommunicationService.getAllTeams().then(
            function(data) {
                $scope.teams = data;
            }
        );

        // Initialize date fields
        var fromDate = new Date();
        var toDate = new Date();

        // Initialize date range as disabled
        $scope.useDateRange = false;

        // Set state from URL
        if (!_.isEmpty($location.search().from) && $location.search().to) {
            $scope.useDateRange = true;
            fromDate = new Date($location.search().from);
            toDate = new Date($location.search().to);
        }
        if ($location.search().team) {
            $scope.teamFilter = $location.search().team;
        }

        //TODO Check if time value is necessary. Prob overrated.
        $scope.dates = {
            fromDate: fromDate,
            toDate: toDate,
            fromTime: new Date(fromDate),
            toTime: new Date(toDate)
        };

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
        };

        $scope.showCalendar = function($event, cal) {
            $event.preventDefault();
            $event.stopPropagation();
            _.each($scope.openedCalendars, function(isOpen, cal) {
                $scope.openedCalendars[cal] = false;
            });
            $scope.openedCalendars[cal] = true;
        };

        $scope.openedCalendars = {
            'from': false,
            'to': false
        };

        $scope.apply = function() {
            setTimes($scope.dates);
            setStateToUrl($scope);
            fetchReports();
        };

        var setStateToUrl = function(scope) {
            $location.url($location.path());
            if (scope.useDateRange) {
                $location.search('from', scope.dates.fromDate);
                $location.search('to', scope.dates.toDate);
                localStorageService.set('returnTo', '/#' + $location.url());
            }
            if (scope.teamFilter !== 'all') {
                $location.search('team', scope.teamFilter);
                localStorageService.set('returnTo', '/#' + $location.url());
            }
        };

        var setTimes = function(d) {
            d.fromDate.setHours(d.fromTime.getHours());
            d.fromDate.setMinutes(d.fromTime.getMinutes());
            d.toDate.setHours(d.toTime.getHours());
            d.toDate.setMinutes(d.toTime.getMinutes());
        };

        var reportsModalCtrl = function($scope, $modalInstance, params) {

            $scope.useDateRange = params.useDateRange;
            $scope.dates = params.dates;
            $scope.dateOptions = params.dateOptions;
            $scope.teamFilter = params.teamFilter;
            $scope.teams = params.teams;
            $scope.showCalendar = params.showCalendar;
            $scope.openedCalendars = params.openedCalendars;

            //TODO Use parent setTeamFilter()
            $scope.setTeamFilter = function(team) {
                $scope.teamFilter = team;
            };

            $scope.ok = function() {
                setTimes($scope.dates);
                var params = {
                    teamFilter: $scope.teamFilter,
                    useDateRange: $scope.useDateRange,
                    dates: $scope.dates,
                };
                $modalInstance.close(params);
            };

            $scope.cancel = function() {
                $modalInstance.dismiss();
            };
        };

        $scope.showReportsModal = function(reportId) {
            var reportsModalInstance = $modal.open({
                templateUrl: '/templates/reportsModal.html',
                controller: reportsModalCtrl,
                backdrop: false,
                resolve: {
                    params: function() {
                        return {
                            useDateRange: $scope.useDateRange,
                            dates: $scope.dates,
                            dateOptions: $scope.dateOptions,
                            teamFilter: $scope.teamFilter,
                            teams: $scope.teams,
                            setTeamFilter: $scope.setTeamFilter,
                            showCalendar: $scope.showCalendar,
                            openedCalendars: $scope.openedCalendars
                        };
                    },
                    reportId: function() {
                        return reportId;
                    }
                }
            });

            reportsModalInstance.result.then(function(params) {
                setStateToUrl(params);
                $location.path('/reports/view/' + reportId);
            });

        };

        // Set team filter and re-fetch alerts
        $scope.setTeamFilter = function(team) {
            $scope.teamFilter = team;
            if ($scope.reportId) {
                setStateToUrl($scope);
                fetchReports();
            }
        };

        $scope.getLink = function(record) {
            if (record.history_type === "ALERT_DEFINITION") {
                return "/#/alert-details/" + record.attributes.adt_id;
            }
            return "/#/check-definitions/view/" + record.attributes.cd_id;
        };

        // Escaping value (e.g. empty_str => "", null => 'null')
        $scope.escapeValue = function(value) {
            var tagsToReplace = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;'
            };

            function replaceTag(tag) {
                return tagsToReplace[tag] || tag;
            }

            if (typeof value === 'undefined') {
                return value;
            } else if (value === null) {
                return 'null';
            } else {
                return (value.length > 0) ? value.replace(/[&<>]/g, replaceTag) : '""';
            }
        };

        $scope.getChanges = function(attributes, inPlainTxt) {
            var res = [];
            _.each(attributes, function(val, attr) {
                var line = "- " + attr + ": ";
                if (inPlainTxt) {
                    line += val;
                } else {
                    line += "<span class='codeish'>";
                    line += $scope.escapeValue(val);
                    line += "</span>";
                }
                res.push(line);
            });
            return inPlainTxt ? '"' + res.join('\r') + '"' : res.join('<br/>');
        };

        $scope.handleDateRangeClick = function() {
            $scope.useDateRange = !$scope.useDateRange;
            if (!$scope.useDateRange) {
                setStateToUrl($scope);
                fetchReports();
            }
        };

        // Calculating the background color of event labels
        $scope.hslFromEventType = function(id) {
            return "hsla(" + ((id * 6151 % 1000 / 1000.0) * 360) + ", 50%, 50%, 1);";
        };

        $scope.export = function() {
            window.URL.revokeObjectURL($scope.blob);
            $scope.blob = new Blob([generateCSV()], {
                type: 'text/plain'
            });
            $scope.csvBlobUrl = window.URL.createObjectURL($scope.blob);
        };

        var generateCSV = function() {
            var csv = [];
            var header = 'LastModified;ModifiedBy;ModifierTeam;Name;ModificationType;OriginalData;NewData';
            csv.push(header);
            _.each($scope.reports, function(report) {
                var line = [];
                var pfix = report.history_type === 'ALERT_DEFINITION' ? 'adt_' : 'cd_';
                line.push(report.attributes[pfix + 'last_modified']);
                line.push(report.attributes[pfix + 'last_modified_by']);
                line.push(report.attributes[pfix + 'team']);
                line.push(report.attributes[pfix + 'name']);
                line.push(report.action);
                line.push($scope.getChanges(report.attributes, true));
                line.push($scope.getChanges(report.changed_attributes, true));
                csv.push(line.join(';'));
            });

            return csv.join('\n');
        };

        var fetchReports = function() {
            var params = {};
            //FIXME Temporarily hardcoding team to incident team, since we only have
            //one report as dummy data. Later this parameter should be provided either
            //from the report object or from a dropdown.
            params.team = "Incident";
            if ($scope.useDateRange) {
                params.from = $scope.dates.fromDate.getTime() / 1000 | 0;
                params.to = $scope.dates.toDate.getTime() / 1000 | 0;
            }
            if ($scope.teamFilter) {
                params.responsible_team = $scope.teamFilter;
            }
            CommunicationService.getReports(params).then(function(data) {
                $scope.reports = data;
                console.log('REPORTS: ', data);
                LoadingIndicatorService.stop();
            });
        };

        // Non-refreshing; one-time listing
        MainAlertService.removeDataRefresh();
        if ($scope.reportId) {
            LoadingIndicatorService.start();
            fetchReports();
        }

        // Init page state depending on URL's query string components
        if (!_.isEmpty($location.search().rf)) {
            $scope.alertFilter = $location.search().rf;
        }
        $scope.$watch('reportsFilter', function(newVal) {
            $location.search('rf', _.isEmpty(newVal) ? null : newVal);
            localStorageService.set('returnTo', '/#' + $location.url());
        });
    }
]);
