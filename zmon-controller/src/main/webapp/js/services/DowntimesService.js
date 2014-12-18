/**
 * Util functions for downtimes
 */
angular.module('zmon2App').factory('DowntimesService', [

    function() {
        var service = {};

        /**
         * Given an array of downtimes of a single entity, returns true if any of them is active now
         */
        service.isAnyDowntimeNow = function(downtimes) {
            return _.size(downtimes) > 0;
        };

        service.hasAllEntitiesInDowntime = function(alertInstance) {
            var hasAllEntitiesInDowntime = true;
            // Each entity has an array of downtimes; we an array of arrays of downtimes
            var arrayOfDowntimesArrays = _.pluck(_.pluck(alertInstance.entities, 'result'), 'downtimes');
            alertInstance.numEntitiesNotInDowntimeNow = 0;
            alertInstance.numEntitiesInDowntimeNow = 0;

            _.each(arrayOfDowntimesArrays, function(nextEntityDowntimes) {
                if(!service.isAnyDowntimeNow(nextEntityDowntimes)){
                    // Means we have to show this alertInstance since is has at least one entity now currently in downtime
                    hasAllEntitiesInDowntime = false;
                    alertInstance.numEntitiesNotInDowntimeNow++;
                } else {
                    alertInstance.numEntitiesInDowntimeNow++;
                }
            });
            return hasAllEntitiesInDowntime;
        };

        return service;
    }
]);
