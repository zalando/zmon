angular.module('zmon2App').directive('entityFilterContainer', ['$compile', '$log', 'FeedbackMessageService',
    function ($compile, $log, FeedbackMessageService) {
        return {
            restrict: 'E',
            scope: {
                entityFilterTypes: '=',
                checkEntities: '=',
                formEntityFilters: '=',
                emptyJson: '=?',
                exclude: '=?'
            },
            templateUrl: 'templates/entityFilterContainer.html',
            link: function (scope, element, attrs, controller) {

                scope.inEditMode = false;
                scope.selectedType = 'GLOBAL'
                scope.globalIsUsed = false;
                scope.config = {};
                scope.availableEntityFilterTypes = [ 'GLOBAL' ];
                scope.entityFilter = { type: scope.selectedType };

                scope.addEntityFilter = function () {
                    if (scope.selectedType === 'GLOBAL') {
                        scope.entityFilter = { type: 'GLOBAL' };
                        return scope.formEntityFilters.push(scope.entityFilter);
                    }
                    scope.config = getEntityFilterConfig(scope.selectedType);
                    scope.entityFilter = { type: scope.selectedType };
                    scope.inEditMode = true;
                };

                scope.editEntityFilter = function(i) {
                    scope.definitionInEditModeIndex = i;
                    scope.entityFilter = scope.formEntityFilters[i];

                    if (typeof scope.entityFilter.type === 'undefined') {
                        scope.entityFilter.type = getTypeFromCheck();
                    };

                    scope.config = getEntityFilterConfig(scope.entityFilter.type);
                    scope.selectedType = scope.entityFilter.type;
                    scope.inEditMode = true;
                };

                scope.removeEntityFilter = function (idx) {
                    scope.formEntityFilters.splice(idx, 1);
                };

                var getEntityFilterConfig = function(type) {
                    var entityFilter = { type: type };
                    _.each(scope.entityFilterTypes, function(filter) {
                        if (filter.type === type) {
                            entityFilter = filter;
                        }
                    });
                    return entityFilter;
                };

                // When an entity filter is missing a type, a default type can be taken from the Check
                var getTypeFromCheck = function() {
                    var type = '';
                    _.each(scope.checkEntities, function(checkEntity) {
                        if (checkEntity.type) {
                            type = checkEntity.type;
                        }
                    });
                    return type;
                };

                scope.$watch('entityFilterTypes', function(){
                    scope.availableEntityFilterTypes = _.pluck(scope.entityFilterTypes, 'type');
                }, true);

                scope.$watch('formEntityFilters', function() {
                    // Remove GLOBAL type if used.
                    scope.globalIsUsed = _.pluck(scope.formEntityFilters, 'type').indexOf('GLOBAL') !== -1;
                    if (scope.globalIsUsed && scope.availableEntityFilterTypes[0] === 'GLOBAL') {
                        scope.availableEntityFilterTypes.splice(0, 1);
                        return scope.selectedType = 'appdomain';
                    }
                    if (!scope.globalIsUsed && scope.availableEntityFilterTypes.indexOf('GLOBAL') === -1) {
                        scope.availableEntityFilterTypes = [ 'GLOBAL' ].concat(scope.availableEntityFilterTypes);
                        scope.selectedType = 'GLOBAL';
                    }
                }, true);
            }
        };
    }
]);
