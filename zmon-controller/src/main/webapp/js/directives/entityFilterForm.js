angular.module('zmon2App').directive('entityFilterForm', function () {
    return {
        restrict: 'E',
        scope: {
            entityFilter: '=',
            allEntityFilters: '=',
            definitionIndex: '=',
            inEditMode: '=',
            config: '='
        },
        templateUrl: 'templates/entityFilterForm.html',
        link: function (scope, element, attrs, controller) {

            scope.save = function () {
                scope.entityFilter = _.extend(scope.entityFilter, scope.definition);
                cleanUpFilter(scope.entityFilter);
                if (typeof scope.definitionIndex === 'undefined' || scope.definitionIndex === -1) {
                    scope.allEntityFilters.push(scope.entityFilter);
                }
                scope.definitionIndex = -1;
                scope.inEditMode = false;
            }

            scope.cancel = function () {
                scope.definition = {};
                scope.entityFilter = {};
                scope.definitionIndex = -1;
                scope.inEditMode = false;
            };

            // Template helper to keep autocomplete menu sorted
            scope.sortItems = function(items) {
                return _.sortBy(items);
            };

            // Remove empty properties: null, undefined or empty arrays.
            var cleanUpFilter = function(filter) {
                for (var p in filter) {
                    if (filter.hasOwnProperty(p) && (filter[p] === null
                                || filter[p] === undefined || filter[p].length === 0)) {
                        delete filter[p];
                    } else if (p === 'host_role_id') {
                        filter[p] = filter[p].value;
                    }
                }
            }

            scope.$watch('entityFilter', function() {
                scope.definition = angular.copy(scope.entityFilter);
            });
        }
    };
});
