angular.module('zmon2App').factory('HttpResponseInterceptorService', ['$q', '$location', 'localStorageService', 'APP_CONST', 'FeedbackMessageService',
    function($q, $location, localStorageService, APP_CONST, FeedbackMessageService) {
        var lastContactWithServer = null;
        var lastHistoryBack = 0;
        var showErrorMessageDebounced = _.debounce(FeedbackMessageService.showErrorMessage, 2 * APP_CONST.FEEBACK_MSG_SHOW_TIME, true);

        return {
            response: function(response) {
                lastContactWithServer = new Date().getTime();
                return response;
            },
            responseError: function(rejection) {
                var message, callback = null;

                if (rejection.status === 0) {
                    // Server is not accessible; the only case where for sure there is not server set message
                    message = 'Server connection lost; last contact was ' + parseFloat((new Date().getTime() - lastContactWithServer) / 1000).toFixed(2) + 'secs ago';
                    // Only case where we don't show the message debounced
                    FeedbackMessageService.showErrorMessage(message, callback);
                } else if (rejection.status === 401) {
                    // Just redirect
                    window.location.href = '/login.jsp?next_page=' + encodeURIComponent(localStorageService.get('returnTo'));
                } else {
                    // resolve the message and display
                    if (rejection.status === 403) { // Loged in, but insufficient rights
                        message = 'You\'re not authorized to perform this action.';
                    } else if (rejection.status === 404) {
                        message = 'The requested resource [' + rejection.config.method + ' ' + rejection.config.url + '] could not be found.  You\'ll be redirected to the previous page.';
                        callback = function() {
                            window.history.back();
                        };
                    } else if (rejection.status === 500) {
                        message = 'Something went really bad requesting [' + rejection.config.method + ' ' + rejection.config.url + '] Please contact the platform team.';
                    } else if (rejection.data.message) {
                        message = rejection.data.message;
                    }
                    showErrorMessageDebounced(message, callback);
                }
                return $q.reject(rejection);
            }
        };
    }
]);


/* Configure app to use our HTTP interceptor to handle errors.
 * In case of reponse error, collaborates with FeedbackMessageService
 * to provide relevant info.
 */
angular.module('zmon2App').config(['$httpProvider',
    function($httpProvider) {
        $httpProvider.interceptors.push('HttpResponseInterceptorService');
    }
]);