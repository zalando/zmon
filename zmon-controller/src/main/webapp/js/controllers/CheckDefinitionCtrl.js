angular.module('zmon2App').controller('CheckDefinitionCtrl', ['$scope', '$routeParams', '$location', 'MainAlertService', 'CommunicationService', 'FeedbackMessageService', 'APP_CONST', 'UserInfoService', 'LoadingIndicatorService', 'localStorageService',
    function($scope, $routeParams, $location, MainAlertService, CommunicationService, FeedbackMessageService, APP_CONST, UserInfoService, LoadingIndicatorService, localStorageService) {
        $scope.DefinitionsCtrl = this;
        $scope.initialLoading = true;

        $scope.$parent.activePage = 'check-definitions';
        $scope.checkDefinitions = [];
        $scope.checkDefinitionId = parseInt($routeParams.checkDefinitionId);
        $scope.teamFilter = null;
        $scope.userInfo = UserInfoService.get();
        $scope.checkJson = '';

        var userInfo = UserInfoService.get();

        this.fetchCheckDefinitions = function() {

            // Start loading animation
            LoadingIndicatorService.start();

            // Get all teams from backend to generate filter by team menu.
            CommunicationService.getAllTeams().then(
                function(data) {
                    $scope.checkTeams = data;
                }
            );

            if ($scope.checkDefinitionId) {
                CommunicationService.getCheckDefinition($scope.checkDefinitionId).then(function(data) {
                    $scope.checkDefinition = data;
                    CommunicationService.getAlertDefinitions().then(function(data) {
                        $scope.alertDefinitions = _.filter(data, function(def) {
                            return def.check_definition_id === $scope.checkDefinitionId;
                        });
                        setLinkToTrialRun();
                    });

                    // Stop loading indicator!
                    LoadingIndicatorService.stop();
                    $scope.initialLoading = false;

                });
            } else {
                CommunicationService.getCheckDefinitions($scope.teamFilter).then(function(data) {
                    $scope.checkDefinitions = data;

                    // Stop loading indicator!
                    LoadingIndicatorService.stop();
                    $scope.initialLoading = false;

                    setLinkToTrialRun();
                });
            }
        };

        // Set team filter and re-fetch check defs.
        $scope.setTeamFilter = function(team) {
            $scope.teamFilter = team ? team.split(',')[0] : null;
            $scope.DefinitionsCtrl.fetchCheckDefinitions();
            $location.search('tf', $scope.teamFilter ? $scope.teamFilter : 'all');
            localStorageService.set('returnTo', '/#' + $location.url());
        };


        var setLinkToTrialRun = function () {
            if (typeof $scope.checkDefinition === 'undefined') return;
            var params = {
                name: $scope.checkDefinition.name,
                check_command: $scope.checkDefinition.command,
                entities: $scope.checkDefinition.entities,
                interval: $scope.checkDefinition.interval,
            }
            $scope.checkJson = window.encodeURIComponent(JSON.stringify(params));
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

        // Non-refreshing; one-time listing
        MainAlertService.removeDataRefresh();
        this.fetchCheckDefinitions();

        // Init page state depending on URL's query string components
        if (!_.isEmpty($location.search().cf)) {
            $scope.checkFilter = $location.search().cf;
        }
        $scope.$watch('checkFilter', function(newVal) {
            $location.search('cf', _.isEmpty(newVal) ? null : newVal);
            localStorageService.set('returnTo', '/#' + $location.url());
        });
    }
]);
