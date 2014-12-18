var HistoryCtrl = function($scope, $location, APP_CONST, CommunicationService, MainAlertService, UserInfoService, FeedbackMessageService) {
    MainAlertService.removeDataRefresh();
    $scope.$parent.activePage = 'history';

    var HC =  $scope.HistoryCtrl = this;

    HC.limit = APP_CONST.INFINITE_SCROLL_VISIBLE_ENTITIES_INCREMENT;
    HC.definition = {};
    HC.history = [];
    HC.activeHistoryButton = 7;

    var q = $location.search();

    if (q.alert_definition_id) {
        $scope.alert_definition_id = q.alert_definition_id;
    }

    // Preventing execution of code if check or alert definition are not defined or values are invalid
    if((!q.check_definition_id || isNaN(q.check_definition_id)) && (!q.alert_definition_id || isNaN(q.alert_definition_id))) {
        var search = Object.keys(q).map(function(key) { return key + '=' + q[key]; }).join('&');
        FeedbackMessageService.showErrorMessage("The requested [GET history?" + search + "] is invalid. You'll be redirected to the previous page.", 3000, function() {
            window.history.back();
        });

        return;
    }

    // Fn. which storing the check definition data into global HC.definition
    var checkHandler = function(def) {
        HC.definition = def;
    };

    // Fn. which appending check definition into alert definition and then storing the alert definition data into global HC.definition
    var alertHandler = function(def) {
        HC.definition = def;

        CommunicationService.getCheckDefinition(def.check_definition_id).then(function(cd) {
            HC.definition.check_definition = cd;
        });
    };

    // Converting original changed_attributes obj into array which is more suitable for searching
    var convertHistory = function(history) {
        history.forEach(function(change) {
            if (change.changed_attributes) {
                change.changed_attributes_list = Object.keys(change.changed_attributes).map(function(key) {
                    return { attribute: key, value: change.changed_attributes[key] };
                });
            }
        });

        return history;
    };

    HC.mode = q.check_definition_id ? 'check' : 'alert';

    // Building default query
    q.limit = q.limit || 20 * HC.limit;
    q.from = q.from || parseInt( (Date.now() / 1000) - (HC.activeHistoryButton * 60 * 60 * 24) , 10);

    // Loading the check/alert definition
    if(HC.mode === 'check') {
        CommunicationService.getCheckDefinition(q.check_definition_id).then(checkHandler);
    } else {
        CommunicationService.getAlertDefinition(q.alert_definition_id).then(alertHandler);
    }

    // Loading the history of changes
    CommunicationService.getHistoryChanges(q).then(function(history) {
        HC.history = convertHistory(history);
    });

    // Updating history data after applying the days filter
    HC.fetchHistory = function(days) {
        HC.activeHistoryButton = days;
        q.from = parseInt( (Date.now() / 1000) - (days * 60 * 60 * 24) , 10);
        CommunicationService.getHistoryChanges(q).then(function(history) {
            HC.history = convertHistory(history);
        });
    };

    /**
     * Used for both INSERTs and UPDATEs attributes (passed param is "record.attributes" and "record.changed_attributes" respectively)
     */
    HC.getChanges = function(attributes) {
        var res = [];
        _.each(attributes, function(val, attr) {
            res.push("- " + attr + ": <span class='codeish'>" + $scope.HistoryCtrl.escapeValue(val) + "</span>");
        });
        return res.join('<br>');
    };

    // Counting the size of history changes
    HC.total = function() {
        return HC.history.length;
    };

    // Escaping value (e.g. empty_str => "", null => 'null')
    HC.escapeValue = function(value) {
        var tagsToReplace = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;'
        };

        function replaceTag(tag) {
            return tagsToReplace[tag] || tag;
        }

        if (typeof value === 'undefined') {
            return value;
        } else if (value === null) {
            return 'null';
        } else {
            return (value.length > 0) ? value.replace(/[&<>]/g, replaceTag) : '""';
        }
    };

    // Calculating the background color of event labels
    HC.hslFromEventType = function(id) {
        return "hsla(" + ((id * 6151 % 1000 / 1000.0) * 360) + ", 50%, 50%, 1);";
    };
};

angular.module('zmon2App').controller('HistoryCtrl', ['$scope', '$location', 'APP_CONST', 'CommunicationService', 'MainAlertService', 'UserInfoService', 'FeedbackMessageService', HistoryCtrl]);
