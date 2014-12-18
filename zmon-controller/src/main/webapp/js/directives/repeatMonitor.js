angular.module('zmon2App').directive('repeatMonitor', [ 'LoadingIndicatorService',
    function(LoadingIndicatorService) {
        return {
            restrict: "A",
            scope: {
                "last": "="
            },
            link: function(scope, elem, attrs) {
                if (scope.last) {
                    LoadingIndicatorService.stop();
                }
            }
        };
    }
]);
