angular.module('zmon2App').directive('ngFocus', function($timeout) {
    return {
        link: function ( scope, element, attrs ) {
            scope.$watch( attrs.ngFocus, function ( val ) {
                if ( angular.isDefined( val ) && val && !scope.focusedElement) {
                    scope.focusedElement = element[0];
                    $timeout( function () { element[0].focus(); } );
                }
            }, true);
        }
    };
});
