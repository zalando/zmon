angular.module('zmon2App').factory('PreconditionsService', ['FeedbackMessageService',
    function(FeedbackMessageService) {
        var IS_EMPTY_ERR = "isNotEmpty() precondition violated";
        var IS_NOT_BOOLEAN_ERR = "isBoolean() precondition violated";
        var IS_NOT_NUMBER_ERR = "isNumber() precondition violated";
        var IS_NOT_DATE_ERR = "isDate() precondition violated";
        var IS_NOT_HTTP_METHOD_ERR = "isHTTPMethod() precondition violated";

        var service = {};


        service.isNotEmpty = function(expr, msg) {
            if (_.isEmpty(expr + '')) {
                msg !== undefined ? FeedbackMessageService.showErrorMessage(msg) : FeedbackMessageService.showErrorMessage(IS_EMPTY_ERR);
                throw new Error(' PreconditionsService: expr is empty when it should not be');
            }
        };

        service.isBoolean = function(expr, msg) {
            if (expr !== true && expr !== false) {
                msg !== undefined ? FeedbackMessageService.showErrorMessage(msg) : FeedbackMessageService.showErrorMessage(IS_NOT_BOOLEAN_ERR);
                throw new Error(' PreconditionsService: expr is !boolean when it should be');
            }
        };

        /**
         * Recognizes numbers base 2/8/10/16
         */
        service.isNumber = function(expr, msg) {
            if (!_.isNumber(expr) && !_.isNumber(parseInt(expr, 2)) && !_.isNumber(parseInt(expr, 8)) && !_.isNumber(parseInt(expr, 10)) && !_.isNumber(parseInt(expr, 16))) {
                msg !== undefined ? FeedbackMessageService.showErrorMessage(msg) : FeedbackMessageService.showErrorMessage(IS_NOT_NUMBER_ERR);
                throw new Error(' PreconditionsService: expr is !number when it should be');
            }
        };

        service.isDate = function(expr, msg) {
            if (!_.isDate(expr)) {
                msg !== undefined ? FeedbackMessageService.showErrorMessage(msg) : FeedbackMessageService.showErrorMessage(IS_NOT_DATE_ERR);
                throw new Error(' PreconditionsService: expr is !date when it should be');
            }
        };

        service.isHTTPMethod = function(expr, msg) {
            if (!_.isString(expr) || (expr.toLowerCase() !== "get" && expr.toLowerCase() !== "post" && expr.toLowerCase() !== "delete" && expr.toLowerCase() !== "put")) {
                msg !== undefined ? FeedbackMessageService.showErrorMessage(msg) : FeedbackMessageService.showErrorMessage(IS_NOT_HTTP_METHOD_ERR);
                throw new Error(' PreconditionsService: expr is !http_method when it should be');
            }
        };

        return service;
    }
]);