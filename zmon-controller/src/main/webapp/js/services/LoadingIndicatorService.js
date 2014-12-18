angular.module('zmon2App').factory('LoadingIndicatorService', ['$q', '$log', 'APP_CONST',
    function($q, $log, APP_CONST) {
        var service = {};
        var isLoading = false;

        service.start = function() {
            isLoading = true;
        };

        service.stop = function() {
            isLoading = false;
        };

        service.getState = function() {
            return isLoading;
        }

        return service;
    }
]);
