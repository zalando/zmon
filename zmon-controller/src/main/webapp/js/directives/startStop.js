angular.module('zmon2App').directive('startStop', function() {
    return {
        restrict: 'E',
        templateUrl: 'templates/startStopDirective.html',
        replace: true,
        scope: {
            refreshing: '=',
            startRefreshCallback: '&',
            stopRefreshCallback: '&'
        }
    };
});