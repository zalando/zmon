/**
 * UserInfo service provide information about current active user.
 * Those information are provided from back-end as attributes of span element with class "auth" in index.jsp
 * Info includes:
 *      data-user="value"
 *      data-teams="value" [string with comma separated values]
 *      data-schedule-downtime="true/false"
 *      data-delete-downtime="true/false"
 *      data-add-alert-def="true/false"
 *      data-add-dashboard="true/false"
 *      data-add-comment="${hasAddCommentPermission}"
 *      data-history-report-access="${hasHistoryReportAccess}"
 *      data-instantaneous-alert-evaluation="${hasInstantaneousAlertEvaluationPermission}">
*/

var UserInfoService = function() {
    return {
        get: function() {
            var attributes = {};
            var el = angular.element('span.auth')[0];

            Object.keys(el.attributes).forEach(function(index) {
                var attr = el.attributes[index];

                if (attr.localName && ~attr.localName.indexOf('data-')) {
                    attributes[attr.localName.replace('data-', '')] = attr.value;
                }

            });
            return attributes;
        }
    };
};

angular.module('zmon2App').factory('UserInfoService', [UserInfoService]);
