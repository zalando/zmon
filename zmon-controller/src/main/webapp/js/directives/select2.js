// Directive which represent warper around select2 library
// --------------------------------------------------------------------------
// ->

angular.module('zmon2App').directive('zmonSelect', [ 'CommunicationService', '$timeout', function (CommunicationService, $timeout) {
    return {
        restrict: 'A',

        scope: {
            service: '&?',
            data: '=?',
            tags: '=?',
            multi: '=?',
            width: '@?',
            placeholder: '@?',
            visible: '=?',
            select: '&',
            unselect: '&?',
            close: '&?',
            open: '=?',
            initOnce: '=?',
            default: '=?'
        },

        link: function (scope, element) {

            // Append to the element select2 list element
            // --------------------------------------------------------------------------
            // ->

            scope.isInit = false;

            var initialize = function () {

                // Prevent re-initialization if onlyInit argument is true
                if (scope.initOnce) {
                    scope.isInit = true;
                }

                // format data to select2 objects: { id: 'id', text: 'txt' }.
                var selectData = [];
                _.each(scope.default, function(d) {
                    selectData.push({'id': d, 'text': d });
                });

                var config = {
                    placeholder: scope.placeholder ? scope.placeholder : '',
                    minimumInputLength: scope.data ? 0 : 3,
                    multiple: scope.multi || false,
                    allowClear: true,
                    width: scope.width ? scope.width : 150,
                    tags: [],
                    data: scope.data,
                    query: function (query) {
                        scope.service({
                            query: {
                                selected: query.term
                            }
                        }).then(function (data) {
                            query.callback({
                                results: data
                            });
                        });
                    },
                    initSelection: function (element, callback) {
                        if (typeof scope.
                            default === 'object') {
                            callback(selectData);
                        } else {
                            callback({
                                text: selectData
                            });
                        }
                    },
                    createSearchChoice: function (term, data) {
                        if ($(data).filter(function() {
                            return this.text.localeCompare(term)===0;
                        }).length===0) {
                            return {id:term, text:term}; }
                    }
                };

                delete config[scope.data ? 'query' : 'data'];
                delete config[scope.tags ? 'pseudo_tags' : 'tags'];

                element.select2(config);
                element.val(selectData).trigger('change');
            };

            // Remove select2 list element
            // --------------------------------------------------------------------------
            // ->
            var destroy = function () {
                element.select2('destroy');
            };

            // Observing the external open event which is used to focus the select2 element
            // --------------------------------------------------------------------------
            // ->

            scope.$watch('open', function (open) {
                if (open) {
                    $timeout(function() {  element.select2('open'); });
                }
            });


            // Observing the external trigger which is used to show or hide select2 list
            // --------------------------------------------------------------------------
            // ->

            scope.$watch('visible', function (visible) {
                var fn = (visible) ? initialize : destroy;
                fn();
            });

            // Observing the data change and reinitialize the select2 list
            // --------------------------------------------------------------------------
            // ->

            scope.$watch('data', function () {
                if (scope.visible) {
                    initialize();
                }
            });

            // Observing the default change and reinitialize the select2 list
            // --------------------------------------------------------------------------
            // ->
            scope.$watch('default', function () {
                if (scope.visible && !scope.isInit) {
                    initialize();
                }
            });

            // Pass the selected value via callback to parent directive/controller
            // --------------------------------------------------------------------------
            // ->

            element.on('select2-selecting', function (selected) {
                scope.select({
                    selected: selected.object,
                    action: 'selected'
                });
            });

            // Pass the removed value via callback to parent directive/controller
            // --------------------------------------------------------------------------
            // ->

            element.on('select2-removed', function (selected) {
                scope.unselect({
                    unselected: {
                        id: selected.val
                    },
                    action: 'unselected'
                });
            });

            // Abort the change on close event (mainly fix for ESC btn press)
            // --------------------------------------------------------------------------
            // ->
            element.on('select2-close', function () {
                scope.close({
                    selected: null
                });

            });
        }
    };
}]);
