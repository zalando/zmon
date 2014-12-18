angular.module('zmon2App').factory('FeedbackMessageService', ['$q', '$window', '$location', '$timeout', 'APP_CONST',
    function($q, $window, $location, $timeout, APP_CONST) {

        var service = {};
        var $wrapper, $message, callback;
        var lastContactWithServer = null;

        var initDom = function(type) {
            $wrapper = $("#message-manager-wrapper");
            $message = $wrapper.children(".message");
            switch (type) {
                case 'error':
                    $wrapper.removeClass('success warning').addClass('error');
                    break;
                case 'warning':
                    $wrapper.removeClass('success error').addClass('warning');
                    break;
                default: //be default it's normal/success message
                    $wrapper.removeClass('error warning').addClass('success');
                    break;
            }
        };

        service.showSuccessMessage = function(message, delay, callback) {
            if (typeof delay === 'function') {
                callback = delay;
                delay = null;
            }

            showMessage('success', message, delay, callback);
        };

        service.showErrorMessage = function(message, delay, callback) {
            if (typeof delay === 'function') {
                callback = delay;
                delay = null;
            }

            showMessage('error', message, delay, callback);
        };

        function showMessage(type, message, delay, callback) {
            initDom(type);
            $message.html(message);
            $wrapper.fadeIn(200);
            $timeout(function() {
                $wrapper.fadeOut(200, callback || angular.noop);
            }, delay || APP_CONST.FEEBACK_MSG_SHOW_TIME);
        }

        return service;
    }
]);