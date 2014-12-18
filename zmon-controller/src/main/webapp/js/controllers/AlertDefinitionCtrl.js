angular.module('zmon2App').controller('AlertDefinitionCtrl', ['$scope', '$window', '$routeParams', '$location', 'MainAlertService', 'CommunicationService', 'FeedbackMessageService', 'localStorageService', 'UserInfoService', 'LoadingIndicatorService', 'APP_CONST',
    function($scope, $window, $routeParams, $location, MainAlertService, CommunicationService, FeedbackMessageService, localStorageService, UserInfoService, LoadingIndicatorService, APP_CONST) {
        $scope.DefinitionsCtrl = this;
        $scope.initialLoading = true;

        $scope.$parent.activePage = 'alert-definitions';
        $scope.alertDefinitions = {};
        $scope.templates = {};
        $scope.alertDefinitionsByStatus = [];
        $scope.templatesByStatus = [];
        $scope.statusFilter = null;
        $scope.teamFilter = null;
        $scope.viewedTabs = [];
        $scope.lastReviews = {};
        $scope.isFilteredByTemplate = false;

        var userInfo = UserInfoService.get();

        this.fetchAlertDefinitions = function() {

            // Start loading animation
            LoadingIndicatorService.start();

            // Get all teams from backend to generate filter by team menu.
            CommunicationService.getAllTeams().then(
                function(data) {
                    $scope.alertTeams = data;
                }
            );

            // Get all alert definitions
            CommunicationService.getAlertDefinitions($scope.teamFilter).then(
                function(data) {

                    // Initially point to all alert definitions until filter status is defined
                    $scope.alertDefinitionsByStatus = data;

                    // Generate Tabs
                    $scope.tabs = [];
                    $scope.alertStatuses = ['All'].concat(_.unique(_.pluck(data, 'status')).sort());
                    _.each($scope.alertStatuses, function(status) {
                        $scope.tabs.push({
                            name: status,
                            active: ($location.search().tab && $location.search().tab === status) ? true : false
                        });
                    });

                    // Create alertDefinitions dictionary by status
                    _.each($scope.alertStatuses, function(status) {
                        $scope.alertDefinitions[status] = [];
                        $scope.templates[status] = [];
                        $scope.lastReviews[status] = localStorageService.get('lastReview-' + status);
                    });
                    // Populate alert definition dict and set star to mark as new or old.
                    _.each(data, function(alert) {
                        var arr = alert.template ? $scope.templates : $scope.alertDefinitions;
                        arr['All'].push(alert);
                        arr[alert.status].push(alert);
                        if (alert.last_modified > $scope.lastReviews[alert.status]) {
                            alert.star = true;
                        }
                    });

                    // Stop loading indicator!
                    LoadingIndicatorService.stop();
                    $scope.initialLoading = false;
                }
            );
        };

        // Set team filter and re-fetch alerts
        $scope.setTeamFilter = function(team) {
            $scope.teamFilter = team ? team.split(',')[0] : null;
            $scope.DefinitionsCtrl.fetchAlertDefinitions();
            $location.search('tf', $scope.teamFilter ? $scope.teamFilter : 'all');
            $scope.isFilteredByTemplate = false;
            localStorageService.set('returnTo', '/#' + $location.url());
        };

        // Set status filter and point alertDefinitionsByStatus to dict entry.
        $scope.setAlertsFilter = function(status) {
            status = status ? status : 'All';
            $scope.updateStars();
            $scope.statusFilter = status;
            $scope.alertDefinitionsByStatus = $scope.alertDefinitions[status];
            $scope.templatesByStatus = $scope.templates[status];
            if (typeof $scope.templatesByStatus === 'undefind' ||
                ($scope.templatesByStatus && $scope.templatesByStatus.length === 0)) {
                    $scope.isFilteredByTemplate = false;
            }
            $scope.viewedTabs.push(status);
            $location.search('tab', status);
            localStorageService.set('returnTo', '/#' + $location.url());
        };

        // Set template filter.
        $scope.setTemplateFilter = function(filter) {
            if (filter === 'template') {
                $scope.isFilteredByTemplate = true;
                return $scope.alertDefinitionsByStatus = $scope.templates[$scope.statusFilter];
            }
            $scope.isFilteredByTemplate = false;
            $scope.alertDefinitionsByStatus = $scope.alertDefinitions[$scope.statusFilter];
        }

        // Check if tab contains new alerts
        $scope.tabHasStar = function(status) {
            var hasStar = false;
            _.each($scope.alertDefinitions[status], function(alert) {
                if (alert.star) {
                    hasStar = true;
                }
            });
            return hasStar;
        };

        // Set last review timestamp to current time
        $scope.setReviewTimestamp = function(status) {
            localStorageService.set('lastReview-' + status, new Date());
        };

        $scope.updateStars = function() {
            _.each($scope.viewedTabs, function(status) {
                _.each($scope.alertDefinitions[status], function(alert) {
                    delete alert.star;
                });
                $scope.setReviewTimestamp(status);
            });
        };

        // Mark all alerts as old whenever user leaves page.
        $scope.$on('$locationChangeStart', function(event) {
            $scope.updateStars();
        });

        $window.onbeforeunload = function(event) {
            $scope.updateStars();
        };

        // Set team filter on load from userInfo
        if (!_.isEmpty(userInfo.teams)) {
            $scope.teamFilter = userInfo.teams.split(',')[0];
        }

        // Override teamFilter if specified on queryString
        if ($location.search().tf) {
            var tf = $location.search().tf === 'all' ? null : $location.search().tf;
            $scope.teamFilter = tf;
        }

        // Set active tab from querystring
        if ($location.search().tab) {
            $scope.setAlertsFilter($location.search().tab);
        }

        // Non-refreshing; one-time listing
        MainAlertService.removeDataRefresh();
        this.fetchAlertDefinitions();

        // Init page state depending on URL's query string components
        if (!_.isEmpty($location.search().af)) {
            $scope.alertFilter = $location.search().af;
        }
        $scope.$watch('alertFilter', function(newVal) {
            $location.search('af', _.isEmpty(newVal) ? null : newVal);
            localStorageService.set('returnTo', '/#' + $location.url());
        });
    }
]);
