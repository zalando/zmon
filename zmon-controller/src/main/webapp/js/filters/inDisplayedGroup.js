/**
 * Used in alert details view to filter out items from all three groups
 * Given an array with entities from all three groups (activeAlerts, alertsInDowntime, checkResults) filter the ones that belong to groups selected to be displayed
 * Passed params are t/f flags denoting if this group is displayed or not
 */
angular.module('zmon2App').filter('inDisplayedGroup', function() {
    return function(allAlertsAndChecks, showActiveAlerts, showAlertsInDowntime, showCheckResults) {
        var onlyDisplayedItems = _.filter(allAlertsAndChecks, function(nextItem) {
            if ((showActiveAlerts && nextItem.isActiveAlert) ||
                (showAlertsInDowntime && nextItem.isAlertInDowntime) ||
                (showCheckResults && nextItem.isCheckResult)) {
                return true;
            }
        });
        return onlyDisplayedItems;
    };
});
