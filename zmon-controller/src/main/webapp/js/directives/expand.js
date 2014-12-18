/**
 * NOTE: if used to make text inside table cell expandable, it's important for table to have class "zmon-data-table"
 * and for table headers of all columns except the expandable one, to have a class with style that defines a width %
 */
var expand = function($compile, $filter, $timeout) {
    return {
        restrict: 'A',
        scope: {},
        link: function(scope, elem, attrs) {
            var $elem = $(elem[0]);
            scope.expanded = false;
            // Wait till after data has been loaded, otherwise we cannot detect if elem has ellipsis or not
            // If it has an ellipsis, add "clickable" class so it has cursor pointer
            $timeout(function() {
                if (elem[0].offsetWidth < elem[0].scrollWidth && !$elem.hasClass('clickable')) {
                    $elem.addClass('clickable');
                }
            }, 4000);

            $elem.on('click', function(ev) {
                if (scope.expanded) {
                    scope.expanded = false;
                    $(this).addClass('ellipsis');
                } else {
                    scope.expanded = true;
                    $(this).removeClass('ellipsis');
                }
            });
        }
    };
};

angular.module('zmon2App').directive('expand', ['$compile', '$filter', '$timeout', expand]);
